import csv
import io
import math
from dataclasses import asdict, dataclass


class DataError(ValueError):
    pass


@dataclass(frozen=True)
class Rules:
    max_overshoot_fraction: float = 0.10
    max_tail_error_fraction: float = 0.02
    max_settling_time_s: float = 5.0
    settling_band_fraction: float = 0.02
    minimum_duration_s: float = 8.0
    tail_window_s: float = 1.0

    @classmethod
    def from_mapping(cls, values):
        if not isinstance(values, dict):
            raise DataError("Rules must be a JSON object")
        unknown = set(values) - set(asdict(cls()))
        if unknown:
            raise DataError("Unknown rule keys")
        for value in values.values():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise DataError("Rule values must be numbers")
            try:
                finite = math.isfinite(value)
            except OverflowError as error:
                raise DataError("Rule value is outside the supported numeric range") from error
            if not finite or value <= 0:
                raise DataError("Rule values must be finite and positive")
        rules = cls(**values)
        if rules.tail_window_s >= rules.minimum_duration_s:
            raise DataError("Tail window must be shorter than minimum duration")
        if rules.max_settling_time_s + rules.tail_window_s > rules.minimum_duration_s:
            raise DataError("Minimum duration must include the settling deadline and tail window")
        return rules


def parse_samples(text):
    try:
        reader = csv.DictReader(io.StringIO(text), strict=True)
        if reader.fieldnames != ["time_s", "reference", "response"]:
            raise DataError("Expected CSV header: time_s,reference,response")
        samples = []
        for row_number, row in enumerate(reader, start=2):
            if None in row or any(value is None or not value.strip() for value in row.values()):
                raise DataError(f"Missing or extra CSV fields at row {row_number}")
            try:
                sample = tuple(float(row[name]) for name in reader.fieldnames)
            except ValueError as error:
                raise DataError(f"Non-numeric CSV field at row {row_number}") from error
            if not all(math.isfinite(value) for value in sample):
                raise DataError(f"Non-finite sample at row {row_number}")
            samples.append(sample)
    except csv.Error as error:
        raise DataError("Malformed CSV") from error
    if len(samples) < 3:
        raise DataError("At least three samples are required")
    if samples[0][0] != 0:
        raise DataError("Time must start at zero")
    reference = samples[0][1]
    if reference <= 0:
        raise DataError("Reference must be positive")
    if any(sample[1] != reference for sample in samples):
        raise DataError("Only a constant step reference is supported")
    step = samples[1][0] - samples[0][0]
    if step <= 0:
        raise DataError("Time must increase strictly")
    for previous, current in zip(samples, samples[1:]):
        difference = current[0] - previous[0]
        if difference <= 0 or not math.isclose(difference, step, rel_tol=1e-6, abs_tol=1e-12):
            raise DataError("Time must increase uniformly")
    return samples


def evaluate(samples, rules):
    if len(samples) < 3:
        raise DataError("At least three samples are required")
    rules = Rules.from_mapping(asdict(rules))
    if samples[-1][0] < rules.minimum_duration_s:
        raise DataError("Recording is shorter than the minimum duration")
    reference = samples[0][1]
    errors = [abs(sample[2] - reference) / reference for sample in samples]
    overshoot = max(0.0, max(sample[2] for sample in samples) - reference) / reference
    if not all(math.isfinite(value) for value in [overshoot, *errors]):
        raise DataError("Normalized metrics exceed the supported numeric range")
    tail_start = samples[-1][0] - rules.tail_window_s
    tail_error = max(error for sample, error in zip(samples, errors) if sample[0] >= tail_start)
    outside = [index for index, error in enumerate(errors) if error > rules.settling_band_fraction]
    settled_index = outside[-1] + 1 if outside else 0
    settling_time = None
    if settled_index < len(samples):
        candidate = samples[settled_index][0]
        if samples[-1][0] - candidate >= rules.tail_window_s:
            settling_time = candidate
    checks = [
        dict(requirement="REQ-001", metric="overshoot_fraction", value=overshoot,
             limit=rules.max_overshoot_fraction, passed=overshoot <= rules.max_overshoot_fraction),
        dict(requirement="REQ-002", metric="tail_error_fraction", value=tail_error,
             limit=rules.max_tail_error_fraction, passed=tail_error <= rules.max_tail_error_fraction),
        dict(requirement="REQ-003", metric="settling_time_s", value=settling_time,
             limit=rules.max_settling_time_s,
             passed=settling_time is not None and settling_time <= rules.max_settling_time_s),
    ]
    return dict(status="PASS" if all(check["passed"] for check in checks) else "FAIL",
                sample_count=len(samples), duration_s=samples[-1][0], checks=checks)


def demo_csv(scenario):
    if scenario not in {"nominal", "bias", "missing"}:
        raise DataError("Unknown demo scenario")
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["time_s", "reference", "response"])
    for index in range(101):
        time_s = index / 10
        response = 1 - math.exp(-time_s) + (0.2 if scenario == "bias" else 0)
        writer.writerow([format(time_s, ".17g"), "1", "" if scenario == "missing" and index == 10 else format(response, ".17g")])
    return stream.getvalue()