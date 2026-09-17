# tests/fixtures — MATLAB evidence (real R2026a run, 2026-09-17)

Landed from the logged MATLAB session in `matlab_validation_log.txt`.
The parity tests in `tests/test_matlab_parity.py` are GREEN on these
files. Do not invent or estimate replacements — re-run in MATLAB instead.

## Provenance of the landed files

- `matlab_nominal.csv` (101 data rows, SHA-256
  `7743308ce053c04aa68fcbe9755892ba9761ec743fe69824bb4f75d5fda48532`):
  exact bytes of MATLAB `export_step_response("matlab_nominal.csv")`
  on 26.1.0.3346908 (R2026a) Update 5 / PCWIN64. No reformatting,
  no re-saving through another tool.
- `matlab_provenance.json`: `matlab_version` is the `version` text from
  the log; `run_date` is the session date; `csv_sha256` matches the file
  above; `matlab_tests` is the `runtests` total from the log
  (3 Passed, 0 Failed); `log_file` is the saved diary.
- `parity_tolerances.json`: `{"abs_tol": 1e-12, "rel_tol": 1e-12}`,
  pinned from measurement (response max_abs 4.996003610813204e-16,
  max_rel 1.1286500989523753e-15; time_s/reference exact) via the
  ~10x-then-1e-12-floor rule, justified in `VALIDATION.md`.

## Ordering rule

Tolerances are chosen from measured differences, never upfront.
`VALIDATION.md` and `README.md` may only claim what the measured
comparison supports.
