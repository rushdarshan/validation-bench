# ValidationBench

A portfolio engineering-tool project: validate a recorded step response, produce
an auditable report, and detect changes to the resulting evidence bundle.

This is an **educational, synthetic-data prototype**. It is not a wind-turbine
controller, a certification system, a safety assessment, or Siemens software.
No customer data, company source code, or company branding is used.

## First runnable slice

- Python standard-library CLI; no dependency installation or virtual environment.
- Explicit CSV contract, configuration checks and invalid-input rejection.
- Three independently reported requirements: overshoot, settling and tail error.
- PASS, FAIL and ERROR remain distinct; exit codes support automation.
- Structured per-run JSONL logs with a shared run ID; not a distributed logging service.
- JSON results, a LaTeX report, optional PDF compilation and a SHA-256 manifest.
- Fresh output directory per run; existing results are never silently overwritten.
- Manifest verification detects missing, extra or modified files. It is not a
  signature or proof against an attacker who can rewrite the manifest itself.

The MATLAB export path is verified by a real run: MATLAB 26.1.0.3346908
(R2026a) Update 5 executed `export_step_response`, and the resulting
101-row CSV is checked in with provenance and measured tolerances (see
"MATLAB handoff" below). The GitHub Actions workflow and any JFrog CLI
usage remain unverified integration scaffolding: neither was available
in the build environment. An Artifactory adapter is a later milestone,
not a completed feature. See `BUILD_PLAN.md` for what must be
demonstrated next.

## Run from this directory

Requires Python 3.11 or newer. The initial local checks use Python 3.13.
PDF generation additionally requires `pdflatex` on PATH.

```bash
python -m validationbench demo --scenario nominal --output examples/nominal.csv
python -m validationbench validate examples/nominal.csv --output runs/nominal --pdf
python -m validationbench verify runs/nominal
python -m unittest discover -s tests -v
```

Run names must be new. Reusing `runs/nominal` intentionally fails rather than
mixing new evidence with old results. Choose a new name to repeat an experiment.
This workspace already contains the initial demo inputs and runs. Inspect those
outputs or choose new input/output names; the commands above assume a fresh copy.

The failing demonstration is supposed to return exit code 1:

```bash
python -m validationbench demo --scenario bias --output examples/bias.csv
python -m validationbench validate examples/bias.csv --output runs/bias --pdf
python -m validationbench verify runs/bias
```

`verify` checks integrity, not whether the modeled response passes requirements.
A correctly preserved FAIL bundle can pass integrity verification.

## Contract and numerical definitions

CSV header: `time_s,reference,response`. All values must be finite. Time starts
at zero, increases strictly, and is uniformly sampled. The reference is a
constant positive step applied at time zero. This version deliberately rejects
general time-varying references instead of assigning misleading step metrics.

The demonstration is the analytic response `1 - exp(-time_s)` of an idealized
unit-gain first-order system with a one-second time constant. It is not a tuned
PID, wind model or physically calibrated plant. The bias case adds a constant
0.2 to the nominal response and should fail the configured requirements.

- Overshoot fraction: `max(0, max(response) - reference) / reference`.
- Tail error fraction: maximum absolute error divided by reference over the
  final configured tail window, inclusive of its start sample.
- Observed settling time: first sample after the last sample outside the band,
  provided at least one full tail-window duration remains afterward. This is
  evidence of remaining in-band over the recorded horizon only, not forever.
- No observed settling time is represented as JSON `null`, never as zero.
- Thresholds are illustrative requirements, not turbine certification limits.

Defaults: at most 10% overshoot, 2% tail error, settling within 5 seconds using a
2% band, at least 8 seconds of data and a 1-second tail window. Override with
`--rules rules.json`; unknown keys and non-finite/non-positive values are errors.

## Evidence

Each completed validation bundle contains the exact input snapshot, effective
rules, result, report source, events and provenance. Source hashes identify the
Python implementation and the exact runtime version is recorded. A PDF build
failure produces ERROR and does not masquerade as a complete passing report.

The numerical demo and metrics are deterministic for fixed inputs and rules.
Run IDs, timestamps, logs and PDF bytes are not promised to be byte-identical.
The manifest records actual bytes; it does not claim deterministic packaging.

Exit codes: `0` validation PASS / successful integrity check; `1` requirement
FAIL; `2` invalid data or configuration; `3` local tool/I/O failure; `4` integrity
failure. A failed operation may leave diagnostic files without a manifest.
Such a directory is not a verified complete bundle.

## MATLAB handoff

Upload `matlab/export_step_response.m` to MATLAB, or run it locally:

```matlab
addpath('matlab');
export_step_response('matlab_nominal.csv');
```

Then validate the exported CSV with this Python tool. Compare it with the Python
nominal dataset using explicit tolerances before claiming MATLAB/Python parity.
The script uses basic MATLAB arithmetic and CSV output, not Simulink or the
MATLAB Engine API.

Executed 2026-09-17 on MATLAB 26.1.0.3346908 (R2026a) Update 5 (PCWIN64):
`runtests` 3 passed / 0 failed, 101-row CSV checked in at
`tests/fixtures/matlab_nominal.csv` with provenance and measured tolerances
(`tests/fixtures/matlab_provenance.json`,
`tests/fixtures/parity_tolerances.json`; response max abs gap 5.0e-16,
tolerances pinned at 1e-12). `tests/test_matlab_parity.py` verifies the
fixture parses under the strict contract, passes nominal requirements,
matches its provenance hash, and stays within the pinned tolerances.
See `VALIDATION.md` for the full evidence record.

## Publishing

Publish this directory as its own repository if desired; no repository, branch,
commit, remote, deployment, account or referral was created by this build.
The included `.github/workflows/python-checks.yml` activates only when this
directory is a repository root. It runs the full Python suite, replays the
comparator/parity regression against the checked-in MATLAB fixture, and
exercises the bias case as a deliberate regression (must exit 1, FAIL not
ERROR). MATLAB itself never runs in CI. Evidence bundles and the parity
report upload as artifacts even on failure. It uses no secrets. Remote
execution still needs a push: inspect the actual hosted run before claiming
CI experience, and flip the run red on purpose (e.g. tighten a tolerance)
to show the regression blocks checks.

Review and understand the AI-assisted implementation before representing it as
your work. The MATLAB execution above is evidenced in-repo and explainable;
do not put Artifactory, production usage, coverage percentages, or hiring
outcomes on your resume without corresponding evidence.