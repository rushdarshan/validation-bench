# Initial validation record

Date: September 15, 2026. Environment: local Linux workspace, Python 3.13.15,
available pdflatex. This is an execution record, not a certification or hiring claim.

## Executed successfully

- `python -m unittest discover -s tests -v`: 29 tests passed.
- Nominal data: validation exit 0, PASS, PDF produced.
- Constant-bias data: validation exit 1, FAIL, PDF produced.
- Missing response field: validation exit 2, ERROR, PDF produced.
- All three completed evidence bundles passed manifest verification.
- All three PDFs contained the expected status, occupied one page, and compiled
  without overfull-box warnings. Text was extracted with pypdf; no graphical
  PDF rendering inspection was performed.
- Modifying input.csv in a copy of a sealed bundle caused verification exit 4.
- Tests exercise no-overwrite behavior, absent input, malformed manifests,
  path-traversal rejection, report-tool failure, missing compiler and timeout.
- Python files parsed successfully. Source files contained no GitHub token patterns.

The first test run caught numeric normalization overflow and an unhandled
oversized integer rule. Both were fixed and the same regression tests now pass.
This does not imply all numerical edge cases are covered.

## Not executed / not implemented

- MATLAB script execution and Python/MATLAB parity: NOT EXECUTED, MATLAB absent.
- MATLAB unit tests and MATLAB CI: NOT IMPLEMENTED in this first slice.
- Hosted Python workflow: YAML PROVIDED, remote run NOT EXECUTED.
- JFrog/Artifactory adapter and remote upload/download: NOT IMPLEMENTED.
- Distributed/centralized multi-process logging: NOT IMPLEMENTED; logs are local
  correlated per-run JSONL files.
- Performance benchmarks, test coverage measurement, real turbine data,
  production deployment, independent user evaluation: NOT PERFORMED.

## Generated local examples

`runs/nominal`, `runs/bias`, `runs/missing` contain their reports and manifests.
`runs/tampered-demo` is deliberately invalid and should fail verification.
These are ignored generated outputs, not a claim of an independently collected
engineering dataset. They are excluded from the starter source ZIP.

The resume was not changed to claim this project, MATLAB proficiency or
Artifactory experience. Complete the personal execution and integration gates
in BUILD_PLAN.md before adding new skill claims.

## September 17, 2026: offline CSV comparator (TDD, no MATLAB)

- Implemented `scripts/compare_step_response.py` via strict TDD:
  RED (8 failing tests) -> GREEN (minimal stdlib-only implementation) ->
  test-precision fix -> full suite green.
- New `tests/test_compare_step_response.py`: 8 tests covering identical
  inputs, within-tolerance perturbation, out-of-tolerance failure, row-count
  mismatch, malformed CSV, invalid tolerance, and CLI exit codes 0/1/2.
- Full suite: 37 tests pass (29 existing untouched + 8 new).
- Added `matlab/test_export_step_response.m` (row count, header, time
  grid, model match, no-overwrite). NOT EXECUTED: MATLAB is absent here.
- NOT DONE (requires real MATLAB): executing `export_step_response`,
  checking in `tests/fixtures/matlab_nominal.csv` + provenance JSON,
  pinning tolerances from measurement, `tests/test_matlab_parity.py`.
  No fixture or parity claim is made until a logged MATLAB run exists.

## September 17, 2026: MATLAB track deferred by owner decision

- Installing MATLAB for this project is out of scope; the integration
  gate is lifted, not bypassed. Nothing MATLAB-derived is claimed anywhere.
- `tests/test_matlab_parity.py` (4 tests) and `tests/fixtures/README.md`
  (drop-zone contract) are kept as the re-activation path; the test class
  is `@unittest.skip`ped with the reason recorded in-code.
- `matlab/export_step_response.m` and `matlab/test_export_step_response.m`
  remain unexecuted scaffolds. `scripts/compare_step_response.py` stays as
  the offline comparator for whenever real MATLAB output exists.
- Re-activate by: real logged MATLAB run -> drop the 3 fixture files ->
  remove the skip -> measure -> pin tolerances -> record evidence here.

## September 17, 2026: simplified scope — contract freeze + traceability

Owner-directed simplified plan (small, interview-explainable; no large
MATLAB/Simulink system; Artifactory and MATLAB CI stay later phases):

- `docs/CONTRACT.md`: frozen Python validation contract (CSV shape,
  Rules defaults, REQ-001..003 metric definitions, demo scenarios,
  exit codes 0/1/2/3/4, bundle membership). Changes require a test
  update plus an entry here.
- `docs/REQUIREMENTS.md`: REQ-001..006 mapped to metric, implementation
  line, and regression tests. REQ-004..005 covered by existing tests;
  REQ-006 stays deferred/skipped.
- MATLAB layer reviewed, kept minimal: `export_step_response.m`
  (first-order step `1 - exp(-t)`, 101 samples, no-overwrite) plus 3
  functiontests (row count/header, time grid + model match, no-overwrite),
  tempname-isolated with teardown. NOT EXECUTED — no MATLAB here.
  No extension: the step response is the whole experiment by design.
- Report hardening: no code change needed — the LaTeX report already
  renders requirement IDs, limits, effective rules, and provenance per
  check. Traceability is now documented, not just rendered.
- Local CI-equivalent gates re-run on this tree: suite 42 tests
  OK (4 skipped); nominal demo -> validate exit 0 -> verify exit 0;
  bias -> validate exit 1 (FAIL, not ERROR). Probe outputs removed.
- Human gates still open: one real logged MATLAB run (script is in the
  loop file), then fixture drop -> un-skip -> measure -> pin tolerances.

## September 17, 2026: real MATLAB baseline landed (TDD RED -> GREEN)

- MATLAB R2026a Update 5 executed `export_step_response` for real.
  Evidence: `matlab_validation_log.txt` — version
  `26.1.0.3346908 (R2026a) Update 5`, release R2026a Update 5,
  platform PCWIN64, `runtests` 3 Passed / 0 Failed
  (3.4562 s), 101-row table (`time_s,reference,response`),
  in-log model check `max_error = 4.9960e-16`, all-finite true.
- RED: removed the `@unittest.skip` in `tests/test_matlab_parity.py`;
  2 tests passed, 2 failed with `FileNotFoundError`
  (no provenance / tolerance files yet) — the expected RED.
- GREEN with measured values only, nothing invented:
  - `tests/fixtures/matlab_nominal.csv` (already the exact MATLAB
    bytes; SHA-256
    `7743308ce053c04aa68fcbe9755892ba9761ec743fe69824bb4f75d5fda48532`).
  - `tests/fixtures/matlab_provenance.json` (5 contract keys; version
    and test totals quoted from the log; hash verified against the file).
  - `tests/fixtures/parity_tolerances.json`
    (`{"abs_tol": 1e-12, "rel_tol": 1e-12}`).
- Measured comparison (`scripts/compare_step_response.py`, Python nominal
  vs MATLAB fixture): time_s max_abs 0, reference max_abs 0, response
  max_abs 4.996003610813204e-16, max_rel 1.1286500989523753e-15.
  The response abs gap matches the log's own 4.9960e-16 check.
  Tolerance justification: observed maxima x ~10 gives 5.0e-15 / 1.2e-14,
  both below the 1e-12 floor, so the floor governs — pinned 1e-12,
  roughly 2000x above the observed response gap, tight enough to catch
  any real model or formatting regression.
- Fixture passes the strict Python contract (101 samples) and evaluates
  PASS under default Rules. Parity suite: 4 tests OK.
- `tests/fixtures/README.md` now records provenance instead of
  describing an empty drop zone; `README.md` handoff no longer claims
  MATLAB is unexecuted.
- Still not done: hosted Python workflow run, JFrog adapter, MATLAB CI —
  unchanged from above.

## September 17, 2026: hosted CI validation phase (TDD RED -> GREEN)

- RED: new `tests/test_ci_workflow.py` (10 tests) locked the workflow
  contract — full suite, explicit comparator/parity step against the
  pinned fixture, bias regression (exit 1), `upload-artifact` with
  `if: always()`, no MATLAB-executing actions, no secrets, fixture
  checked in, README honesty sentence. 5 failed on the old YAML.
- GREEN: `.github/workflows/python-checks.yml` now runs
  `compare_step_response.py` on `ci-nominal.csv` vs
  `tests/fixtures/matlab_nominal.csv` with the pinned 1e-12 tolerances
  (test cross-checks the flags against `parity_tolerances.json`),
  asserts the bias bundle exits 1, and uploads both bundles plus
  `parity-report.txt` even on failure. Local suite: 54 tests OK
  (44 existing untouched + 10 new).
- NOT DONE (human-gated): push and inspect the real hosted run, plus
  one deliberately red run, per BUILD_PLAN Stage 4 acceptance.
  MATLAB CI stays deferred (licensing); the fixture stays the only
  MATLAB evidence in CI.

## September 17, 2026: orphan-bundle fix (code review MEDIUM)

- Review found: `validate` created the output dir and wrote
  `events.jsonl`/`input.csv` before reading input/`--rules`, so a missing
  file left a manifest-less orphan dir and a retry hit the dir-exists
  guard (exit 3) instead of the real error. Reproduced before fixing.
- Fix in `validationbench/__main__.py`: read input and rules bytes
  before `mkdir`; exit codes unchanged (still 3 on OSError).
- Regression tests: missing input and missing `--rules` file both exit 3
  and leave no output directory. Suite: 44 tests OK.
- Frozen in `docs/CONTRACT.md`: runs failing before validation leave no
  output directory behind.

## September 17, 2026: release-readiness verification (PASS)

- 44/44 tests OK; CLI flows re-verified (nominal validate 0, verify 0;
  bias validate 1). Stdlib-trace line coverage 100% (353/353) on all 5
  Python sources at the 80% target; MATLAB tests genuinely executed.
- No secrets, no TODO/FIXME; no function > 50 lines; largest file
  `tests/test_validation.py` (220 lines, under 800).
- Third-party attribution: nothing copied — `docs/THIRD_PARTY_CODE.md`
  correctly absent. Fixture bytes exact, provenance hash matches.
- Fixed 2 stale README claims: MATLAB scaffolding paragraph now records
  the real R2026a run; resume caution now exempts only the evidenced
  MATLAB run (Artifactory/production/coverage-% still need evidence).
- Older "NOT EXECUTED" lines are dated Sept 15 history, superseded by
  the Sept 17 entries — journal preserved, not rewritten.
- Still open, human-gated: no LICENSE (release blocker), hosted CI run
  unverified, JFrog adapter + MATLAB CI deferred, stray files for
  release cleanup (`session-ses_f506.md`, loop pointer, `.test-tmp/`
  and `runs/` are git-ignored but present).

## September 17, 2026: post-CI verification loop (PASS)

- 54/54 tests OK. Flows re-verified: nominal validate 0 / verify 0,
  tampered bundle verify 4 (`INTEGRITY_ERROR: Evidence checksum mismatch`).
- Stdlib-trace line coverage still 100% (353/353) on all 5 Python
  sources vs 80% target. No function > 50 lines, no file > 800 lines,
  secrets scan clean, probes removed.
- Node checklist N/A (no TS/lint/build in this repo). MATLAB CI and
  JFrog remain deferred; hosted Actions run still awaits a push.