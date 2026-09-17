"""Offline CSV-vs-CSV step-response comparator (stdlib only).

Compares two step-response CSVs with the same strictness as
validationbench.core.parse_samples, reports per-column max abs/rel
diffs, and exits 0 iff every sample is within tolerance.

This is an offline comparator: it never executes MATLAB and never
claims MATLAB/Python parity on its own. Tolerances must be pinned
from measured MATLAB output, not assumed.
"""

import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validationbench.core import parse_samples

COLUMNS = ("time_s", "reference", "response")


def _check_tol(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return float(value)


def compare_texts(python_text, matlab_text, abs_tol, rel_tol):
    """Compare two CSV documents. Returns a per-column diff report."""
    abs_tol = _check_tol(abs_tol, "abs_tol")
    rel_tol = _check_tol(rel_tol, "rel_tol")
    first = parse_samples(python_text)
    second = parse_samples(matlab_text)
    report = {"passed": False, "sample_counts": (len(first), len(second)), "columns": {}}
    if len(first) != len(second):
        report["reason"] = "sample count mismatch"
        return report
    passed = True
    for index, name in enumerate(COLUMNS):
        max_abs, max_rel, within = 0.0, 0.0, True
        for left, right in zip(first, second):
            gap = abs(left[index] - right[index])
            scale = max(abs(left[index]), abs(right[index]))
            rel = gap / scale if scale else 0.0
            max_abs, max_rel = max(max_abs, gap), max(max_rel, rel)
            within = within and gap <= max(abs_tol, rel_tol * scale)
        report["columns"][name] = {"max_abs_diff": max_abs, "max_rel_diff": max_rel,
                                   "within_tolerance": within}
        passed = passed and within
    report["passed"] = passed
    return report


def main(argv=None):
    """CLI entry point. Returns a process exit code."""
    parser = argparse.ArgumentParser(description="Compare two step-response CSVs offline.")
    parser.add_argument("python_csv", type=Path)
    parser.add_argument("matlab_csv", type=Path)
    parser.add_argument("--abs-tol", type=float, default=1e-9)
    parser.add_argument("--rel-tol", type=float, default=1e-9)
    args = parser.parse_args(argv)
    try:
        report = compare_texts(args.python_csv.read_text(encoding="utf-8-sig"),
                               args.matlab_csv.read_text(encoding="utf-8-sig"),
                               args.abs_tol, args.rel_tol)
    except (ValueError, OSError) as error:
        print(f"COMPARISON_ERROR: {error}", file=sys.stderr)
        return 2
    for name in COLUMNS:
        column = report["columns"].get(name)
        if column is None:
            print(f"{name}: not comparable ({report.get('reason')})")
        else:
            print(f"{name}: max_abs={column['max_abs_diff']:.6g} "
                  f"max_rel={column['max_rel_diff']:.6g} "
                  f"within_tolerance={column['within_tolerance']}")
    print("PARITY_PASS" if report["passed"] else "PARITY_FAIL")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
