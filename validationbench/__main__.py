import argparse
import json
import sys
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .artifacts import IntegrityError, digest, seal_bundle, verify_bundle, write_json
from .core import DataError, Rules, demo_csv, evaluate, parse_samples
from .report import ReportError, compile_pdf, make_report


def event(directory, run_id, name, **fields):
    record = dict(timestamp=datetime.now(timezone.utc).isoformat(), run_id=run_id, event=name, **fields)
    with (directory / "events.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")


def validate(args):
    args.output.mkdir(parents=True, exist_ok=False)
    run_id = str(uuid.uuid4())
    event(args.output, run_id, "validation_started")
    input_bytes = args.input.read_bytes()
    input_bytes = args.input.read_bytes()
    (args.output / "input.csv").write_bytes(input_bytes)
    source_directory = Path(__file__).parent
    provenance = dict(schema_version=1, run_id=run_id, python=sys.version, tool_version=__version__,
                      input_sha256=digest(input_bytes), input_producer="not independently verified",
                      source_sha256={path.name: digest(path.read_bytes()) for path in sorted(source_directory.glob("*.py"))})
    effective_rules = {}
    try:
        if len(input_bytes) > 5_000_000:
            raise DataError("CSV exceeds the five-megabyte prototype limit")
        rule_values = {}
        if args.rules:
            rule_bytes = args.rules.read_bytes()
            (args.output / "rules-input.json").write_bytes(rule_bytes)
            rule_values = json.loads(rule_bytes)
        rules = Rules.from_mapping(rule_values)
        effective_rules = asdict(rules)
        samples = parse_samples(input_bytes.decode("utf-8-sig"))
        result = evaluate(samples, rules)
        exit_code = 0 if result["status"] == "PASS" else 1
    except ValueError as error:
        result = dict(status="ERROR", error=str(error), checks=[])
        exit_code = 2
    result.update(schema_version=1, run_id=run_id, pdf_requested=args.pdf, pdf_generated=False)
    write_json(args.output / "rules.json", effective_rules)
    provenance["rules_sha256"] = digest((args.output / "rules.json").read_bytes())
    write_json(args.output / "provenance.json", provenance)
    (args.output / "report.tex").write_text(make_report(result, effective_rules), encoding="utf-8")
    if args.pdf:
        try:
            compile_pdf(args.output)
            result["pdf_generated"] = True
            event(args.output, run_id, "pdf_generated")
        except ReportError as error:
            result["validation_status_before_report_error"] = result["status"]
            result.update(status="ERROR", error=str(error))
            (args.output / "report.pdf").unlink(missing_ok=True)
            (args.output / "report.tex").write_text(make_report(result, effective_rules), encoding="utf-8")
            event(args.output, run_id, "pdf_error", category="REPORT_TOOL_FAILURE")
            exit_code = 3
    write_json(args.output / "result.json", result)
    event(args.output, run_id, "validation_finished", status=result["status"], exit_code=exit_code)
    seal_bundle(args.output)
    print(json.dumps(dict(status=result["status"], run_id=run_id, bundle=str(args.output))))
    return exit_code


def main(argv=None):
    parser = argparse.ArgumentParser(prog="validationbench")
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo")
    demo.add_argument("--scenario", choices=["nominal", "bias", "missing"], default="nominal")
    demo.add_argument("--output", type=Path, required=True)
    validation = commands.add_parser("validate")
    validation.add_argument("input", type=Path)
    validation.add_argument("--output", type=Path, required=True)
    validation.add_argument("--rules", type=Path)
    validation.add_argument("--pdf", action="store_true")
    verification = commands.add_parser("verify")
    verification.add_argument("bundle", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8", newline="") as stream:
                stream.write(demo_csv(args.scenario))
            print(json.dumps(dict(status="DEMO_WRITTEN", scenario=args.scenario)))
            return 0
        if args.command == "verify":
            count = verify_bundle(args.bundle)
            print(json.dumps(dict(status="INTEGRITY_VERIFIED", file_count=count,
                                  note="This is not a validation PASS or a signature")))
            return 0
        return validate(args)
    except IntegrityError as error:
        print(json.dumps(dict(status="INTEGRITY_ERROR", error=str(error))), file=sys.stderr)
        return 4
    except OSError as error:
        print(json.dumps(dict(status="TOOL_ERROR", category=type(error).__name__)), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())