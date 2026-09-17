"""Python/MATLAB parity tests — GREEN on the real R2026a Update 5 run (2026-09-17).

Required under tests/fixtures/ (see tests/fixtures/README.md):
  matlab_nominal.csv      actual MATLAB output, exact bytes
  matlab_provenance.json  version, date, log reference, csv_sha256
  parity_tolerances.json  {"abs_tol": ..., "rel_tol": ...} pinned from measurement

No numeric bound is assumed here: every tolerance comes from
parity_tolerances.json, which is written only after measuring the real
MATLAB output with scripts/compare_step_response.py. Until the fixture
lands, these tests fail with FileNotFoundError — that is the RED phase.
"""

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from validationbench.core import demo_csv, evaluate, parse_samples, Rules

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures"
FIXTURE = FIXTURES / "matlab_nominal.csv"
PROVENANCE = FIXTURES / "matlab_provenance.json"
TOLERANCES = FIXTURES / "parity_tolerances.json"
COMPARE = REPO_ROOT / "scripts" / "compare_step_response.py"

REQUIRED_PROVENANCE_KEYS = (
    "matlab_version", "run_date", "csv_sha256", "matlab_tests", "log_file",
)


class MatlabParityTests(unittest.TestCase):
    def test_matlab_fixture_parses_under_strict_contract(self):
        samples = parse_samples(FIXTURE.read_text(encoding="utf-8-sig"))
        self.assertEqual(len(samples), 101)

    def test_matlab_fixture_passes_nominal_requirements(self):
        result = evaluate(parse_samples(FIXTURE.read_text(encoding="utf-8-sig")), Rules())
        self.assertEqual(result["status"], "PASS")

    def test_provenance_matches_fixture_bytes(self):
        provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
        for key in REQUIRED_PROVENANCE_KEYS:
            self.assertIn(key, provenance)
        self.assertTrue(str(provenance["matlab_version"]).strip())
        actual = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
        self.assertEqual(provenance["csv_sha256"], actual)

    def test_fixture_bytes_are_checkout_stable(self):
        # The fixture carries CRLF (as MATLAB wrote it) and its SHA-256 is
        # hash-gated above, so .gitattributes must forbid line-ending
        # conversion — otherwise Linux checkouts hash differently and CI
        # fails while the local suite stays green.
        attributes = (REPO_ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("matlab_nominal.csv", attributes)
        self.assertTrue("-text" in attributes or "binary" in attributes)

    def test_measured_parity_within_pinned_tolerances(self):
        tolerances = json.loads(TOLERANCES.read_text(encoding="utf-8"))
        tmp_root = REPO_ROOT / ".test-tmp"
        tmp_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=tmp_root) as tmp:
            python_csv = Path(tmp) / "python_nominal.csv"
            python_csv.write_text(demo_csv("nominal"), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(COMPARE), str(python_csv), str(FIXTURE),
                 "--abs-tol", str(float(tolerances["abs_tol"])),
                 "--rel-tol", str(float(tolerances["rel_tol"]))],
                capture_output=True, text=True, timeout=60, check=False,
            )
        self.assertEqual(completed.returncode, 0, msg=completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
