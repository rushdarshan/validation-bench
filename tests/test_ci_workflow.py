"""Hosted CI contract tests (TDD RED -> GREEN for the validation phase).

Locks what `.github/workflows/python-checks.yml` must do:
- run the full local suite (unittest discover)
- run the comparator/parity regression explicitly against the pinned
  MATLAB fixture (MATLAB itself never runs in CI)
- exercise the deliberate bias regression (must exit 1: FAIL, not ERROR)
- upload evidence artifacts even on failure
- use no secrets and no MATLAB-executing actions

Fixture provenance (csv + provenance + tolerances checked in) is
asserted here too, so CI can never silently swap in an evidenced claim.
"""

import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "python-checks.yml"
FIXTURES = REPO_ROOT / "tests" / "fixtures"
README = REPO_ROOT / "README.md"


def workflow_text():
    return WORKFLOW.read_text(encoding="utf-8")


class CiWorkflowTests(unittest.TestCase):
    def test_workflow_file_exists(self):
        self.assertTrue(WORKFLOW.is_file())

    def test_full_suite_runs(self):
        self.assertIn("unittest discover -s tests", workflow_text())

    def test_parity_regression_uses_pinned_fixture_explicitly(self):
        text = workflow_text()
        self.assertIn("compare_step_response", text)
        self.assertIn("matlab_nominal", text)

    def test_workflow_tolerances_match_pinned_fixture(self):
        text = workflow_text()
        pinned = json.loads((FIXTURES / "parity_tolerances.json").read_text(encoding="utf-8"))
        for flag, key in (("--abs-tol", "abs_tol"), ("--rel-tol", "rel_tol")):
            match = re.search(rf"{re.escape(flag)}\s+([0-9eE.+\-]+)", text)
            self.assertIsNotNone(match, f"{flag} not pinned in workflow")
            assert match is not None
            self.assertEqual(float(match.group(1)), float(pinned[key]))

    def test_no_matlab_execution_in_ci(self):
        text = workflow_text().lower()
        for marker in ("matlab-actions", "setup-matlab", "matlab -batch", "run-matlab-tests"):
            self.assertNotIn(marker, text)

    def test_no_secrets_in_ci(self):
        self.assertNotIn("secrets.", workflow_text())

    def test_artifacts_uploaded_even_on_failure(self):
        text = workflow_text()
        self.assertIn("upload-artifact", text)
        self.assertIn("if: always()", text)

    def test_deliberate_bias_regression_in_ci(self):
        text = workflow_text()
        self.assertIn("bias", text)
        self.assertTrue("-eq 1" in text or "exit 1" in text)

    def test_provenance_fixture_checked_in(self):
        for name in ("matlab_nominal.csv", "matlab_provenance.json", "parity_tolerances.json"):
            self.assertTrue((FIXTURES / name).is_file(), f"missing {name}")

    def test_readme_documents_fixture_based_ci(self):
        self.assertIn("MATLAB itself never runs in CI", README.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
