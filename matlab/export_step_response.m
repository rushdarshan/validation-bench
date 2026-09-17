function export_step_response(output_path)
arguments
    output_path (1,1) string = "matlab_nominal.csv"
end
if isfile(output_path)
    error('ValidationBench:Exists', 'Choose a new output path.');
end
time_s = (0:100)' / 10;
reference = ones(size(time_s));
response = 1 - exp(-time_s);
assert(all(isfinite(response)), 'Non-finite response');
output = table(time_s, reference, response);
writetable(output, output_path);
end
