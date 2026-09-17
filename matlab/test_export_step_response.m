function tests = test_export_step_response
% Unit tests for export_step_response. Run in MATLAB only:
%   runtests('matlab')
% Never runs in the Python CI job (no MATLAB license there).
% Execution status: NOT EXECUTED locally; record results in VALIDATION.md.
tests = functiontests(localfunctions);
end

function test_row_count_and_header(testCase)
output = [tempname, '.csv'];
export_step_response(output);
testCase.addTeardown(@() delete(output));
result = readtable(output);
testCase.verifySize(result, [101, 3]);
testCase.verifyEqual(result.Properties.VariableNames, {'time_s', 'reference', 'response'});
end

function test_time_grid_and_model(testCase)
output = [tempname, '.csv'];
export_step_response(output);
testCase.addTeardown(@() delete(output));
result = readtable(output);
testCase.verifyEqual(result.time_s, (0:100)' / 10, 'AbsTol', 1e-12);
testCase.verifyTrue(all(isfinite(result.response)));
testCase.verifyEqual(result.response, 1 - exp(-result.time_s), 'AbsTol', 1e-9);
end

function test_existing_output_is_not_overwritten(testCase)
output = [tempname, '.csv'];
export_step_response(output);
testCase.addTeardown(@() delete(output));
testCase.verifyError(@() export_step_response(output), 'ValidationBench:Exists');
end
