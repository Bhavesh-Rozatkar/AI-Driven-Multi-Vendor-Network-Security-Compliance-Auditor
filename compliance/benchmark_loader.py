"""Load and validate the supplied CIS benchmark JSON."""

import json
from pathlib import Path

REQUIRED = ("rule_id", "title", "type", "audit_command", "expected_configuration")


class BenchmarkError(RuntimeError):
    pass


def load_benchmark(path=None):
    path = Path(path or Path(__file__).resolve().parents[1] / "data" / "cis_benchmark.json")
    if not path.exists():
        raise BenchmarkError(
            f"CIS benchmark file not found: {path}. "
            "Place the supplied benchmark in data/cis_benchmark.json."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BenchmarkError(f"Invalid CIS benchmark JSON: {exc}") from exc

    controls = data.get("controls") if isinstance(data, dict) else data
    if not isinstance(controls, list):
        raise BenchmarkError("Benchmark must contain a 'controls' array.")

    if not controls:
        raise BenchmarkError(
            "CIS benchmark contains no controls. The supplied benchmark must be loaded "
            "before a compliance audit can run."
        )

    seen = set()
    for i, control in enumerate(controls):
        missing = [k for k in REQUIRED if k not in control]
        if missing:
            raise BenchmarkError(f"Control {i} is missing fields: {', '.join(missing)}")
        rule_id = str(control.get("rule_id", "")).strip()
        if not rule_id:
            raise BenchmarkError(f"Control {i} has an empty rule_id.")
        if rule_id in seen:
            raise BenchmarkError(f"Duplicate CIS rule_id: {rule_id}")
        seen.add(rule_id)
    return data if isinstance(data, dict) else {"controls": controls}
