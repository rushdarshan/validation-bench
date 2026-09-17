# ValidationBench — Evidence-First Step-Response Validation

Validate a recorded step response, produce an auditable report, and detect
any later change to the resulting evidence bundle. MATLAB-checked, CI-gated.

[![CI](https://github.com/rushdarshan/validation-bench/actions/workflows/python-checks.yml/badge.svg)](https://github.com/rushdarshan/validation-bench/actions/workflows/python-checks.yml)
![Python 3.12 · 3.13](https://img.shields.io/badge/python-3.12%20%C2%B7%203.13-blue)
![stdlib only](https://img.shields.io/badge/deps-stdlib%20only-green)
![MIT license](https://img.shields.io/badge/license-MIT-lightgrey)

## Status

| Component | State | Evidence |
|---|---|---|
| Python CLI (`validationbench/`) | Working | 54 tests OK; nominal→PASS, bias→FAIL, tampered→exit 4 |
| Offline CSV comparator (`scripts/`) | Working | 8 dedicated tests; PARITY_PASS at pinned tolerances |
| MATLAB export + unit tests (`matlab/`) | Executed once, checked in | R2026a Update 5; `runtests` 3 passed / 0 failed |
| Python↔MATLAB parity gate | Passing | response max abs gap 4.996e-16 vs 1e-12 tolerance (~2000× margin) |
| GitHub Actions (`python-checks.yml`) | Configured, hosted run pending | Contract-pinned by 10 tests; MATLAB itself never runs in CI |
| JFrog/Artifactory adapter | Deferred | Later milestone, not claimed |
| MATLAB in CI | Deferred | Fixture-based parity instead; MATLAB itself never runs in CI |

This is an **educational, synthetic-data prototype**. It is not a wind-turbine
controller, a certification system, a safety assessment, or Siemens software.
No customer data, company source code, or company branding is used.

## Why ValidationBench

**Problem:** validation results for engineering models are usually a plot and
a claim. Rerun it, tweak a number, regenerate the figure — nobody can tell
what changed, what the thresholds were, or whether the "PASS" survived intact.

**Solution:** a stdlib-only tool that validates a step-response CSV against
explicit numeric requirements, seals input + rules + result + report + logs
into a SHA-256-manifested bundle, and verifies that bundle later. A MATLAB
run of the same model is checked in as a fixture, so Python↔MATLAB agreement
is a measured gate, not an assertion.

## Try it in 30 seconds

Requires Python 3.11+. No dependencies, no virtual environment.

```bash
git clone https://github.com/rushdarshan/validation-bench.git
cd validation-bench
python -m unittest discover -s tests            # 54 tests, all green

python -m validationbench demo --scenario nominal --output /tmp/nominal.csv
python -m validationbench validate /tmp/nominal.csv --output /tmp/good
python -m validationbench verify /tmp/good      # INTEGRITY_VERIFIED
```

The failing path is a first-class citizen:

```bash
python -m validationbench demo --scenario bias --output /tmp/bias.csv
python -m validationbench validate /tmp/bias.csv --output /tmp/bad   # exit 1: FAIL, not ERROR
python -m validationbench verify /tmp/bad                            # integrity still verifies
```

Tamper with any sealed file and verification fails with exit 4
(`INTEGRITY_ERROR: Evidence checksum mismatch`).

## Commands

| Command | Purpose |
|---|---|
| `demo --scenario nominal\|bias\|missing --output FILE` | Write a deterministic demo CSV (refuses to overwrite) |
| `validate INPUT --output DIR [--rules R.json] [--pdf]` | Check requirements, seal the evidence bundle (fresh dir only) |
| `verify BUNDLE` | Check manifest integrity; distinct from validation PASS/FAIL |
| `scripts/compare_step_response.py A.csv B.csv --abs-tol X --rel-tol Y` | Offline CSV-vs-CSV parity check; exits 0 pass / 1 mismatch / 2 error |

Exit codes: `0` validation PASS / integrity OK · `1` requirement FAIL ·
`2` invalid data or configuration · `3` local tool/I-O failure ·
`4` integrity failure.

## How it works

```
demo CSV ──▶ validate ──▶ input.csv + rules + result.json + report.tex
  (+ --pdf)                  (+ events.jsonl + provenance.json)
                                       │ seal (SHA-256 manifest)
                                       ▼
                              verify ──▶ INTEGRITY_VERIFIED / exit 4
```

Every run gets a UUID run ID shared across `events.jsonl` entries, so logs
correlate without a central service. `verify` checks integrity only — a
correctly preserved FAIL bundle passes verification. The manifest is a
tamper record, not a signature against an attacker who can rewrite it.

## Contract and numerical definitions

CSV header: `time_s,reference,response`. All values finite. Time starts at
zero, increases strictly, uniformly sampled. The reference is a constant
positive step applied at time zero. This version deliberately rejects
general time-varying references instead of assigning misleading step metrics.

The demo is the analytic response `1 - exp(-time_s)` of an idealized
unit-gain first-order system with a one-second time constant — not a tuned
PID, wind model, or calibrated plant. The bias case adds a constant 0.2 and
must fail the configured requirements.

- **Overshoot fraction:** `max(0, max(response) - reference) / reference`.
- **Tail error fraction:** max absolute error / reference over the final
  tail window, inclusive of its start sample.
- **Observed settling time:** first sample after the last sample outside the
  band, provided at least one full tail-window duration remains afterward —
  evidence of staying in-band over the recorded horizon only, not forever.
- No observed settling time is JSON `null`, never zero.
- Thresholds are illustrative requirements, not turbine certification limits.

Defaults: ≤10% overshoot, ≤2% tail error, settling within 5 s in a 2% band,
≥8 s of data, 1 s tail window. Override with `--rules rules.json`; unknown
keys and non-finite/non-positive values are errors. Inputs over 5 MB are
rejected. `input_provenance` is recorded as "not independently verified".
A run that fails before validation leaves no output directory behind.

## Requirements traceability

| Requirement | Metric | Regression test |
|---|---|---|
| REQ-001 overshoot ≤ 10% | overshoot fraction | `test_overshoot_*`, bias FAIL path |
| REQ-002 tail error ≤ 2% | tail error fraction | `test_tail_*`, bias FAIL path |
| REQ-003 settling ≤ 5 s | observed settling time | `test_settling_*` incl. boundary |
| REQ-004 PASS/FAIL/ERROR distinct | exit codes 0/1/2 | nominal / bias / missing scenarios |
| REQ-005 evidence integrity | SHA-256 manifest | tamper, missing, unlisted, traversal tests |
| REQ-006 MATLAB parity | comparator at pinned tols | `test_matlab_parity.py` (4 tests) |

## MATLAB handoff

`matlab/export_step_response.m` implements the same nominal model in MATLAB
(basic arithmetic + CSV output — no Simulink, no Engine API), with
`matlab/test_export_step_response.m` covering row count, header, time grid,
model match, and no-overwrite behavior.

Executed 2026-09-17 on MATLAB 26.1.0.3346908 (R2026a) Update 5 (PCWIN64),
trial install: `runtests` 3 passed / 0 failed; 101-row CSV checked in at
`tests/fixtures/matlab_nominal.csv` with provenance
(`tests/fixtures/matlab_provenance.json`, SHA-256 hash of the exact bytes)
and measured tolerances (`tests/fixtures/parity_tolerances.json`:
response max abs gap 4.996e-16, pinned at 1e-12). To reproduce:

```matlab
addpath('matlab');
export_step_response('matlab_nominal.csv');
```

then compare with the Python nominal dataset at the pinned tolerances before
claiming parity. `tests/test_matlab_parity.py` verifies the fixture parses
under the strict contract, passes nominal requirements, matches its
provenance hash, and stays within tolerance.

## Continuous integration

`.github/workflows/python-checks.yml` runs on push/PR (Python 3.12, 3.13):

1. Full suite (`unittest discover -s tests`).
2. Parity regression: comparator at the pinned 1e-12 tolerances against the
   checked-in MATLAB fixture — MATLAB itself never runs in CI.
3. Nominal demo → validate → verify chain.
4. Deliberate red: bias data **must** exit 1; a 0 fails the run.
5. Evidence artifacts (`runs/ci-nominal/`, `runs/ci-bias/`, parity report)
   uploaded with `if: always()`.

Ten contract tests (`tests/test_ci_workflow.py`) pin this behavior locally,
including that workflow tolerances match `parity_tolerances.json` exactly.

## Evidence

Each bundle holds the exact input snapshot, effective rules, result, report
source, events, and provenance. Source hashes identify the Python
implementation; the runtime version is recorded. A PDF failure yields ERROR,
never a masquerading PASS. The demo and metrics are deterministic for fixed
inputs; run IDs, timestamps, and PDF bytes are not promised byte-identical.

## Comparison

| | Ad-hoc scripts + plots | Simulink Test | ValidationBench |
|---|---|---|---|
| License / cost | free, but throwaway | commercial, needs MATLAB license | MIT, stdlib-only |
| Requirement checks | implicit in code | formal test cases | explicit numeric contract |
| Evidence sealing | none | project/test artifacts | SHA-256 manifest + verify |
| MATLAB agreement | eyeballed | native | measured fixture gate (4.996e-16) |
| CI without MATLAB | n/a | needs license/server | fixture-based parity, keyless |
| Scope | anything | full dynamic-system testing | 1-D step responses only |

ValidationBench wins on zero-dependency reproducibility and sealed evidence;
it is not a substitute for Simulink Test on real dynamic systems. That
boundary is the point.

## Limitations (read before citing this)

- MATLAB ran once, on a trial install — the fixture is real but single-source.
- Coverage is executable-line via stdlib `trace` (100%, 353/353), not branch coverage.
- No performance benchmarks, no real plant data, no production deployment.
- The hosted Actions run is unverified until pushed and inspected.
- PDFs need local `pdflatex`; CI does not build PDFs.

## Project structure

```
.github/workflows/python-checks.yml  # suite + parity + bias-fail + artifacts
matlab/                               # export_step_response.m + functiontests
scripts/compare_step_response.py      # offline CSV-vs-CSV comparator
tests/fixtures/                       # MATLAB CSV + provenance + tolerances
tests/test_validation.py              # contract, bundle, report tests
tests/test_compare_step_response.py   # comparator tests
tests/test_matlab_parity.py           # fixture + parity tests
tests/test_ci_workflow.py             # CI contract tests
validationbench/                      # core.py, __main__.py, artifacts.py, report.py
```

## Development

```bash
python -m unittest discover -s tests -v     # full suite
python -m unittest discover -s tests -p "test_validation.py"   # one file
```

Conventions: stdlib only, no new dependencies; TDD (RED→GREEN→REFACTOR);
every behavior change ships with a regression test; docs claim only what
`VALIDATION.md` records as executed.

## Resume / interview note

Review and understand the AI-assisted implementation before representing it
as your work. The MATLAB execution above is evidenced in-repo and
explainable; do not put Artifactory, production usage, coverage percentages,
or hiring outcomes on your resume without corresponding evidence.
One-liner: "Built a stdlib-only validation CLI that seals evidence bundles
with SHA-256 manifests, verified against a real MATLAB R2026a baseline at
5e-16 agreement, gated by keyless CI."

## License

MIT — see [LICENSE](LICENSE).
