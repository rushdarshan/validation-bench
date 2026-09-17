# tests/fixtures — MATLAB evidence (real R2026a run, 2026-09-17)

Landed from the logged MATLAB session in `matlab_validation_log.txt`.
The parity tests in `tests/test_matlab_parity.py` are GREEN on these
files. Do not invent or estimate replacements — re-run in MATLAB instead.

## Provenance of the landed files

- `matlab_nominal.csv` (101 data rows, SHA-256
  `bd07e3dae31e4b91545f591b4d824bcb1729dc4d3a3860efc57fcea596554854`):
  numeric content exactly as MATLAB `export_step_response` wrote it on
  26.1.0.3346908 (R2026a) Update 5 / PCWIN64, with line endings
  normalized CRLF -> LF on check-in. Reason: Git converts line endings
  on some checkouts, which changes the byte hash and breaks the
  provenance gate on Linux CI while local Windows stays green. No
  numeric reformatting, no re-saving through another tool; the original
  session log is retained in `matlab_validation_log.txt`.
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
