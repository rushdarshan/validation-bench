# Build plan: relevant evidence, not maximum complexity

Prepared September 15, 2026. Planning estimates below are effort budgets, not
promised completion dates or selection guarantees.

Akshata's supplied post describes work performed during two internships. It is
not her pre-selection resume and does not establish which projects earned her
first shortlist. Use the technical themes, not a claim that copying them wins.

## Product question

Can an engineer run a repeatable validation, distinguish bad data from a failed
requirement, understand failures, regenerate a report and verify its artifacts?

The resume story should eventually be: Python engineering tools + MATLAB data
generation + test automation + report reproducibility + CI + artifact handling.
Do not build a chatbot, Kubernetes cluster or microservice fleet to inflate it.

## Stage 1: understand and demonstrate the local slice

Budget: two focused sessions, followed by explanations written without an LLM.

1. Run the nominal, biased and malformed-data paths.
2. Explain every metric and why a missing settling time is not zero.
3. Read each test, change one implementation line deliberately, and establish
   whether a relevant test detects the regression; revert the deliberate defect.
4. Inspect result JSON, the PDF and JSONL logs side by side.
5. Tamper with a copy of an artifact and show integrity verification failing.

Acceptance: commands and outcomes recorded, no fake benchmark or coverage claim,
and you can explain the distinction between FAIL, ERROR and integrity failure.

## Stage 2: genuine MATLAB experience

Budget: approximately 3-5 focused days if MATLAB is new to you; adjust for study.

1. Check your college's MATLAB access using your college email. If unavailable,
   MathWorks documents MATLAB Online basic with 20 free hours per calendar month.
   Browser access is not the same as a local unattended MATLAB installation.
2. Learn arrays, functions, tables, file I/O, assertions and plotting. Run the
   provided script yourself and explain its analytic model and limitations.
3. Add MATLAB unit tests, then a Python/MATLAB CSV comparison with explicit
   absolute/relative tolerances and a justified discrepancy report.
4. Extend the simple model to an agreed educational controller experiment only
   after the baseline is correct; document sample time and numerical method.

Acceptance: real MATLAB execution log and version, unit-test results and a parity
comparison. Merely having an `.m` file is not this milestone.

## Stage 3: engineering report quality

Budget: 2-3 focused days.

Add a response plot, requirement IDs mapped to checks/tests, a requirements
change history, input units, explicit missing-data handling, and a human-readable
comparison against a pinned baseline. Avoid exposing raw local paths or secrets.

Acceptance: someone else can interpret the report without reading the code;
changing a requirement changes the recorded rules hash and the report.

## Stage 4: CI that actually ran

Budget: 1-2 focused days plus debugging.

Publish only after reviewing the files, choosing a license and checking for
secrets. Run the supplied Python workflow on the hosted service. Add a separate
PDF-build job and upload diagnostic artifacts even on failure. Pin third-party
actions to reviewed commit SHAs before using sensitive credentials.

Add MATLAB CI only after checking licensing and cost. MathWorks documents public
project licensing for supported actions, with limitations; private projects
require appropriate licensing. Batch licensing does not support MATLAB Engine
APIs, so this design exchanges CSV rather than requiring an Engine bridge.

Acceptance: a linked successful CI run plus a deliberately failing PR/run that
shows a regression blocks the checks. A YAML file alone is not CI experience.

## Stage 5: Artifactory/JFrog integration, not a mock-only badge

Budget: 3-5 focused days; requires access to a permitted test instance.

Build an adapter around an installed, configured JFrog CLI. Use its configured
server identity; never put tokens in code, command arguments, logs or this chat.
Do not make paid subscriptions or deploy infrastructure without checking costs.

Required behaviors:

- Verify the local manifest before upload; refuse unknown/modified files.
- Use an exact run-specific artifact path and immutable naming policy.
- Treat exit status and parsed command outcome explicitly; `--fail-no-op` must
  not turn zero uploaded files into success. Missing source files and no matches
  can be different failures: test real behavior for the pinned CLI version.
- Bound timeout/retries. Retry only transient cases when the operation is safe
  to repeat; do not blindly retry authentication or authorization failures.
- Never use destructive synchronization/delete flags in the initial adapter.
- After upload, download to a clean directory and verify checksums again.
- Log event type, run ID, attempt and a safe error category; redact credentials
  and avoid dumping raw CLI output into a purported safe centralized log.

Test success, no files, absent CLI, invalid credentials, forbidden repository,
timeout, interrupted upload and checksum mismatch. Unit-test mocks are valuable
but must be distinguished from actual integration checks. No JFrog adapter or
remote upload was implemented in the first slice.

## Stage 6: packaging and interview evidence

Budget: 2-3 focused days.

Produce a 2-minute demo, one architecture diagram, an example report, test and
CI links, two documented defects you reproduced/fixed, and a limitations page.
Explain why you used CSV, why thresholds are configurable, how errors propagate,
what a checksum cannot prove, and what you would change for multiple concurrent
users. One bounded tool should precede any centralized multi-process log service.

Only then write a resume bullet from measured facts. Do not claim production
deployment, certification, a job offer, time savings or test coverage not measured.
Keep the internship application moving in parallel; do not wait for every stage
or represent unfinished milestones as complete.

## First three actions for Darshan

1. Run and explain the local nominal and failing examples in README.
2. Open MATLAB through legitimate college/basic access and execute the `.m`
   script, saving the actual output and MATLAB version for the next integration.
3. Personally reproduce one failure, add or improve its regression test, and
   write a short explanation of the engineering tradeoff in your own words.

## Official references checked September 15, 2026

- MATLAB Online access: `https://www.mathworks.com/products/matlab-online/matlab-online-versions.html`
- MATLAB unit testing: `https://www.mathworks.com/help/matlab/run-unit-tests.html`
- MATLAB Actions/licensing: `https://github.com/matlab-actions/setup-matlab`
- MATLAB command action: `https://github.com/matlab-actions/run-command`
- JFrog upload/failure options: `https://docs.jfrog.com/artifactory/docs/generic-files`
- Python Actions examples: `https://github.com/actions/setup-python/blob/main/README.md`

Scope and acceptance criteria are project design decisions, not recruiter claims.