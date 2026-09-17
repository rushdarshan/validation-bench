import hashlib
import json
import re
from pathlib import Path


class IntegrityError(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def seal_bundle(directory):
    files = {}
    for path in sorted(directory.iterdir()):
        if path.name == "manifest.json":
            continue
        if path.is_symlink() or not path.is_file():
            raise IntegrityError("Unexpected non-regular bundle member")
        files[path.name] = digest(path.read_bytes())
    write_json(directory / "manifest.json", dict(schema_version=1, files=files))


def verify_bundle(directory):
    manifest_path = directory / "manifest.json"
    if manifest_path.is_symlink():
        raise IntegrityError("Manifest cannot be a symlink")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise IntegrityError("Manifest is missing or unreadable") from error
    if not isinstance(manifest, dict) or set(manifest) != {"schema_version", "files"}:
        raise IntegrityError("Invalid manifest structure")
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise IntegrityError("Unsupported manifest version")
    files = manifest["files"]
    required = {"input.csv", "rules.json", "result.json", "report.tex", "events.jsonl", "provenance.json"}
    if not isinstance(files, dict) or not required <= set(files):
        raise IntegrityError("Required evidence is absent from manifest")
    for name, expected in files.items():
        if not isinstance(name, str) or name in {".", "..", "manifest.json"}:
            raise IntegrityError("Invalid bundle member name")
        if "/" in name or "\\" in name or Path(name).name != name:
            raise IntegrityError("Bundle members must be simple filenames")
        if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
            raise IntegrityError("Invalid SHA-256 value")
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise IntegrityError("Missing or non-regular evidence file")
        if digest(path.read_bytes()) != expected:
            raise IntegrityError("Evidence checksum mismatch")
    actual = {path.name for path in directory.iterdir() if path.name != "manifest.json"}
    if actual != set(files):
        raise IntegrityError("Unlisted evidence files detected")
    return len(files)