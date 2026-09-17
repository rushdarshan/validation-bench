import importlib.util
import unittest
from pathlib import Path

from validationbench.core import DataError, demo_csv

MODULE_PATH = Path(__file__).parent.parent / "scripts" / "compare_step_response.py"


def test_tmp():
    path = Path(__file__).resolve().parent.parent / ".test-tmp"
    path.mkdir(exist_ok=True)
    return path


def load_module():
    spec = importlib.util.spec_from_file_location("compare_step_response", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def offset_response(text, row_index, delta):
    lines = text.splitlines(keepends=True)
    header, rows = lines[0], lines[1:]
    time_s, reference, response = rows[row_index].rstrip("\n").split(",")
    rows[row_index] = f"{time_s},{reference},{float(response) + delta:.17g}\n"
    return header + "".join(rows)


class CompareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compare = load_module()

    def test_identical_inputs_pass_with_zero_diff(self):
        report = self.compare.compare_texts(demo_csv("nominal"), demo_csv("nominal"), 1e-9, 1e-9)
        self.assertTrue(report["passed"])
        for column in ("time_s", "reference", "response"):
            self.assertEqual(report["columns"][column]["max_abs_diff"], 0.0)

    def test_small_perturbation_within_tolerance_passes(self):
        other = offset_response(demo_csv("nominal"), 50, 1e-10)
        report = self.compare.compare_texts(demo_csv("nominal"), other, 1e-9, 1e-9)
        self.assertTrue(report["passed"])

    def test_large_perturbation_fails(self):
        other = offset_response(demo_csv("nominal"), 50, 0.01)
        report = self.compare.compare_texts(demo_csv("nominal"), other, 1e-9, 1e-9)
        self.assertFalse(report["passed"])
        self.assertAlmostEqual(report["columns"]["response"]["max_abs_diff"], 0.01)

    def test_row_count_mismatch_fails(self):
        short = "".join(demo_csv("nominal").splitlines(keepends=True)[:-1])
        report = self.compare.compare_texts(demo_csv("nominal"), short, 1e-9, 1e-9)
        self.assertFalse(report["passed"])

    def test_malformed_csv_raises(self):
        with self.assertRaises(DataError):
            self.compare.compare_texts(demo_csv("nominal"), demo_csv("missing"), 1e-9, 1e-9)

    def test_negative_tolerance_rejected(self):
        with self.assertRaises(ValueError):
            self.compare.compare_texts(demo_csv("nominal"), demo_csv("nominal"), -1e-9, 1e-9)

    def test_cli_identical_files_exit_zero(self):
        import contextlib
        import io
        import tempfile

        with tempfile.TemporaryDirectory(dir=test_tmp()) as tmp:
            first = Path(tmp) / "python.csv"
            second = Path(tmp) / "matlab.csv"
            first.write_text(demo_csv("nominal"), encoding="utf-8")
            second.write_text(demo_csv("nominal"), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(self.compare.main([str(first), str(second)]), 0)

    def test_cli_mismatch_exits_one_and_missing_exits_two(self):
        import contextlib
        import io
        import tempfile

        with tempfile.TemporaryDirectory(dir=test_tmp()) as tmp:
            first = Path(tmp) / "python.csv"
            second = Path(tmp) / "matlab.csv"
            first.write_text(demo_csv("nominal"), encoding="utf-8")
            second.write_text(offset_response(demo_csv("nominal"), 50, 0.01), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(self.compare.main([str(first), str(second)]), 1)
                short = Path(tmp) / "short.csv"
                short.write_text("".join(demo_csv("nominal").splitlines(keepends=True)[:-1]),
                                 encoding="utf-8")
                self.assertEqual(self.compare.main([str(first), str(short)]), 1)
                self.assertEqual(self.compare.main([str(first), str(Path(tmp) / "absent.csv")]), 2)


if __name__ == "__main__":
    unittest.main()
