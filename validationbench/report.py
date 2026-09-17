import subprocess


class ReportError(RuntimeError):
    pass


def tex_escape(value):
    replacements = {
        "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
        "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
        "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(character, character) for character in str(value))


def make_report(result, rules):
    rows = []
    for check in result.get("checks", []):
        value = "not observed" if check["value"] is None else f'{check["value"]:.6g}'
        rows.append(" & ".join(tex_escape(value) for value in [
            check["requirement"], check["metric"], value, f'{check["limit"]:.6g}',
            "PASS" if check["passed"] else "FAIL",
        ]) + r" \\")
    rule_rows = [tex_escape(key) + " = " + tex_escape(value) + r"\\" for key, value in sorted(rules.items())]
    return "\n".join([
        r"\documentclass[10pt]{article}", r"\usepackage[margin=1in]{geometry}",
        r"\usepackage[T1]{fontenc}", r"\usepackage[utf8]{inputenc}",
        r"\setlength{\parindent}{0pt}", r"\begin{document}",
        r"\section*{ValidationBench: educational validation report}",
        r"Synthetic demonstration / recorded step response. Not turbine certification or production qualification.\par",
        r"\medskip", "Run: " + tex_escape(result["run_id"]) + r"\\",
        "Status: " + tex_escape(result["status"]) + r"\\",
        "PDF generation requested: " + tex_escape(result["pdf_requested"]) + r"\\",
        "Error: " + tex_escape(result.get("error", "none")) + r"\\",
        r"\section*{Requirement checks}",
        r"\begin{tabular}{lllll}", r"ID & Metric & Observed & Maximum & Result \\",
        r"\hline", *rows, r"\end{tabular}",
        r"\section*{Effective rules}", *rule_rows,
        r"\section*{Interpretation and provenance}",
        r"Fractions are normalized to the constant positive reference. Settling is observed only over the recorded horizon. No observed settling time is not zero.\par",
        r"The JSON result retains numeric precision. Input, rules, logs, report and implementation provenance are recorded in this bundle. Check manifest.json before using it.\par",
        r"An intact manifest is not a digital signature, a guarantee of model validity or a passing requirement result.",
        r"\end{document}", "",
    ])


def compile_pdf(directory):
    try:
        completed = subprocess.run(
            ["pdflatex", "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error", "report.tex"],
            cwd=directory, capture_output=True, text=True, timeout=30, check=False,
        )
    except FileNotFoundError as error:
        raise ReportError("pdflatex is not installed") from error
    except subprocess.TimeoutExpired as error:
        raise ReportError("PDF compilation timed out") from error
    (directory / "pdf-build.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    if completed.returncode != 0 or not (directory / "report.pdf").is_file():
        raise ReportError("PDF compilation failed; inspect pdf-build.log")