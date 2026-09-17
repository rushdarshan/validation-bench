import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from validationbench.__main__ import main
from validationbench.artifacts import IntegrityError, verify_bundle
from validationbench.core import DataError, Rules, demo_csv, evaluate, parse_samples
from validationbench.report import ReportError, compile_pdf, tex_escape


class CoreTests(unittest.TestCase):
    def test_nominal_matches_expected_sampled_settling(self):
        result = evaluate(parse_samples(demo_csv("nominal")), Rules())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["sample_count"], 101)
        self.assertEqual(result["checks"][0]["value"], 0.0)
        self.assertEqual(result["checks"][2]["value"], 4.0)

    def test_bias_is_failure_not_input_error(self):
        result = evaluate(parse_samples(demo_csv("bias")), Rules())
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(all(not check["passed"] for check in result["checks"]))
        self.assertIsNone(result["checks"][2]["value"])

    def test_last_sample_alone_does_not_prove_settling(self):
        samples = [(index / 10, 1.0, 0.5 if index < 100 else 1.0) for index in range(101)]
        result = evaluate(samples, Rules())
        self.assertIsNone(result["checks"][2]["value"])

    def test_constant_in_band_can_settle_at_zero(self):
        result = evaluate([(index / 10, 1.0, 1.0) for index in range(101)], Rules())
        self.assertEqual(result["checks"][2]["value"], 0.0)
        self.assertEqual(result["status"], "PASS")

    def test_tail_window_detects_error_before_last_sample(self):
        samples = [(index / 10, 1.0, 0.8 if index == 95 else 1.0) for index in range(101)]
        result = evaluate(samples, Rules())
        self.assertAlmostEqual(result["checks"][1]["value"], 0.2)
        self.assertFalse(result["checks"][1]["passed"])

    def test_missing_data_rejected(self):
        with self.assertRaises(DataError):
            parse_samples(demo_csv("missing"))

    def test_nonfinite_data_rejected(self):
        for invalid in ["nan", "inf", "-inf"]:
            with self.subTest(invalid=invalid), self.assertRaises(DataError):
                parse_samples(f"time_s,reference,response\n0,1,0\n1,1,{invalid}\n2,1,1\n")

    def test_bad_headers_and_extra_fields_rejected(self):
        for text in ["time,reference,response\n0,1,0", "time_s,reference,response\n0,1,0,4"]:
            with self.subTest(text=text), self.assertRaises(DataError):
                parse_samples(text)

    def test_nonnumeric_and_short_data_rejected(self):
        for text in ["time_s,reference,response\n0,1,text", "time_s,reference,response\n0,1,0\n1,1,1"]:
            with self.subTest(text=text), self.assertRaises(DataError):
                parse_samples(text)

    def test_time_and_reference_contract(self):
        cases = [
            "0,1,0\n0,1,1\n1,1,1",
            "0,1,0\n2,1,1\n1,1,1",
            "0,1,0\n1,1,1\n3,1,1",
            "1,1,0\n2,1,1\n3,1,1",
            "0,1,0\n1,2,1\n2,2,1",
            "0,0,0\n1,0,1\n2,0,1",
        ]
        for body in cases:
            with self.subTest(body=body), self.assertRaises(DataError):
                parse_samples("time_s,reference,response\n" + body)

    def test_rules_reject_invalid_values(self):
        cases = [{"unknown": 1}, [], {"tail_window_s": 10}, {"minimum_duration_s": 2}]
        cases += [{"max_settling_time_s": value} for value in [0, -1, True, "5", float("nan"), float("inf"), 10 ** 400]]
        for values in cases:
            with self.subTest(values=values), self.assertRaises(DataError):
                Rules.from_mapping(values)

    def test_short_recording_rejected(self):
        with self.assertRaises(DataError):
            evaluate(parse_samples(demo_csv("nominal"))[:21], Rules())

    def test_evaluate_rejects_too_few_samples(self):
        with self.assertRaises(DataError):
            evaluate([], Rules())

    def test_threshold_change_is_observable(self):
        samples = parse_samples(demo_csv("nominal"))
        self.assertEqual(evaluate(samples, replace(Rules(), max_settling_time_s=3))["status"], "FAIL")

    def test_normalization_overflow_rejected(self):
        samples = [(index / 10, 1e-320, 1.0) for index in range(101)]
        with self.assertRaises(DataError):
            evaluate(samples, Rules())


class BundleTests(unittest.TestCase):
    def setUp(self):
        tmp_root = Path(__file__).resolve().parent.parent / ".test-tmp"
        tmp_root.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=tmp_root)
        self.root = Path(self.temporary.name)
        self.source = self.root / "input.csv"
        self.source.write_text(demo_csv("nominal"), encoding="utf-8")
        self.output = self.root / "result"

    def tearDown(self):
        self.temporary.cleanup()

    def invoke(self, arguments):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return main(arguments)

    def validate(self, extra=None):
        return self.invoke(["validate", str(self.source), "--output", str(self.output), *(extra or [])])

    def test_complete_passing_bundle_and_correlated_logs(self):
        self.assertEqual(self.validate(), 0)
        self.assertEqual(self.invoke(["verify", str(self.output)]), 0)
        result = json.loads((self.output / "result.json").read_text())
        events = [json.loads(line) for line in (self.output / "events.jsonl").read_text().splitlines()]
        self.assertTrue(all(event["run_id"] == result["run_id"] for event in events))
        self.assertFalse(result["pdf_generated"])

    def test_failed_requirements_still_have_valid_integrity(self):
        self.source.write_text(demo_csv("bias"), encoding="utf-8")
        self.assertEqual(self.validate(), 1)
        self.assertEqual(self.invoke(["verify", str(self.output)]), 0)

    def test_invalid_input_is_error_not_fail(self):
        self.source.write_text(demo_csv("missing"), encoding="utf-8")
        self.assertEqual(self.validate(), 2)
        self.assertEqual(json.loads((self.output / "result.json").read_text())["status"], "ERROR")
        self.assertEqual(self.invoke(["verify", str(self.output)]), 0)

    def test_existing_output_is_not_overwritten(self):
        self.assertEqual(self.validate(), 0)
        original = (self.output / "result.json").read_bytes()
        self.assertEqual(self.validate(), 3)
        self.assertEqual(original, (self.output / "result.json").read_bytes())

    def test_tampering_and_missing_files_fail(self):
        self.assertEqual(self.validate(), 0)
        (self.output / "input.csv").write_text("tampered", encoding="utf-8")
        self.assertEqual(self.invoke(["verify", str(self.output)]), 4)
        (self.output / "input.csv").unlink()
        self.assertEqual(self.invoke(["verify", str(self.output)]), 4)

    def test_unlisted_file_fails(self):
        self.assertEqual(self.validate(), 0)
        (self.output / "unlisted.txt").write_text("extra", encoding="utf-8")
        self.assertEqual(self.invoke(["verify", str(self.output)]), 4)

    def test_manifest_path_traversal_rejected(self):
        self.assertEqual(self.validate(), 0)
        path = self.output / "manifest.json"
        manifest = json.loads(path.read_text())
        manifest["files"]["../outside"] = "0" * 64
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(IntegrityError):
            verify_bundle(self.output)

    def test_empty_and_malformed_manifest_rejected(self):
        self.output.mkdir()
        for data in ["{}", "not JSON", '{"schema_version": 1, "files": {}}']:
            (self.output / "manifest.json").write_text(data, encoding="utf-8")
            self.assertEqual(self.invoke(["verify", str(self.output)]), 4)

    def test_invalid_rule_document_is_error(self):
        rules = self.root / "rules.json"
        rules.write_text('{"tail_window_s": "large"}', encoding="utf-8")
        self.assertEqual(self.validate(["--rules", str(rules)]), 2)
        self.assertTrue((self.output / "rules-input.json").is_file())

    def test_pdf_failure_does_not_leave_passing_result(self):
        with patch("validationbench.__main__.compile_pdf", side_effect=ReportError("missing compiler")):
            self.assertEqual(self.validate(["--pdf"]), 3)
        result = json.loads((self.output / "result.json").read_text())
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["validation_status_before_report_error"], "PASS")
        self.assertFalse(result["pdf_generated"])
        self.assertIn("Status: ERROR", (self.output / "report.tex").read_text())
        self.assertEqual(self.invoke(["verify", str(self.output)]), 0)

    def test_missing_input_is_tool_error(self):
        self.source.unlink()
        self.assertEqual(self.validate(), 3)
        self.assertFalse((self.output / "manifest.json").exists())

    def test_demo_does_not_overwrite(self):
        self.assertEqual(self.invoke(["demo", "--output", str(self.source)]), 3)


class ReportTests(unittest.TestCase):
    def test_tex_special_characters_escaped(self):
        self.assertEqual(tex_escape("a_b&c%"), r"a\_b\&c\%")
        self.assertNotIn(r"\input{", tex_escape(r"\input{secret}"))

    def test_missing_pdf_binary_is_explicit_error(self):
        with patch("validationbench.report.subprocess.run", side_effect=FileNotFoundError()):
            with self.assertRaises(ReportError):
                compile_pdf(Path("unused"))

    def test_pdf_timeout_is_explicit_error(self):
        with patch("validationbench.report.subprocess.run", side_effect=subprocess.TimeoutExpired("pdflatex", 30)):
            with self.assertRaises(ReportError):
                compile_pdf(Path("unused"))


if __name__ == "__main__":
    unittest.main()