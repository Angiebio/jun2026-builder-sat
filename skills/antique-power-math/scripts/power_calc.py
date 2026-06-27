"""Deterministic AI-equivalence calculator for Antique Infernal Engine.

The model may choose assumptions. This script owns the arithmetic.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from typing import Literal


AI_HELLO_WATTS = 30.0
POTATO_WATTS = 0.0001
CYCLIST_WATTS = 100.0
AI_HELLO_OPS = 14_000_000_000.0
SECONDS_PER_YEAR = 31_557_600.0

POWER_PATHS = {
    "galvanic_dc",
    "rotational_mechanical_power",
    "steam_rotational_power",
    "human_mechanical_power",
}

COMPUTE_PATHS = {
    "punched_card_parallel_binary",
    "mechanical_decimal_compute",
    "electromagnetic_switching",
    "silicon_microprocessor_compute",
}

UNSUPPORTED_PATHS = {
    "optical_or_measurement_only",
    "decorative_or_unknown",
}

VALID_PATHS = POWER_PATHS | COMPUTE_PATHS | UNSUPPORTED_PATHS
Mode = Literal["power", "compute", "unsupported"]


@dataclass(frozen=True)
class MathResult:
    path: str
    mode: Mode
    input_value: float
    input_unit: str
    units_for_ai_hello: float
    potatoes_equivalent: float
    cyclists_equivalent: float
    time_seconds: float
    time_years: float
    can_evaluate: bool
    calculation_log: list[str]


def _round(value: float) -> float:
    """Round for stable JSON while preserving large/small values."""
    if value == 0:
        return 0.0
    if math.isinf(value):
        return value
    if abs(value) >= 1000:
        return round(value, 4)
    return round(value, 8)


def _mode_for_path(path: str) -> Mode:
    if path in POWER_PATHS:
        return "power"
    if path in COMPUTE_PATHS:
        return "compute"
    if path in UNSUPPORTED_PATHS:
        return "unsupported"
    raise ValueError(
        f"Unknown artifact path '{path}'. Expected one of: {', '.join(sorted(VALID_PATHS))}"
    )


def run_calculation(path: str, value: float | int | str | None = None) -> dict:
    """Calculate power or compute equivalence for a taxonomy path.

    Power paths interpret ``value`` as watts per artifact.
    Compute paths interpret ``value`` as operations per second.
    Unsupported paths return a non-evaluable result without performing division.
    """

    mode = _mode_for_path(path)
    numeric_value = 0.0 if value is None else float(value)

    if mode != "unsupported" and numeric_value < 0:
        raise ValueError(
            f"WIRING FAILURE: input value {numeric_value} must be strictly positive for {path}."
        )

    result = MathResult(
        path=path,
        mode=mode,
        input_value=numeric_value,
        input_unit="watts" if mode == "power" else "ops_per_second" if mode == "compute" else "none",
        units_for_ai_hello=0.0,
        potatoes_equivalent=0.0,
        cyclists_equivalent=0.0,
        time_seconds=0.0,
        time_years=0.0,
        can_evaluate=mode != "unsupported",
        calculation_log=[],
    )
    data = asdict(result)

    if mode == "power":
        watts_per_unit = numeric_value
        if watts_per_unit == 0:
            data["units_for_ai_hello"] = -1.0
            data["can_evaluate"] = False
            data["calculation_log"].extend(
                [
                    "Power path has 0 W available.",
                    "Sentinel -1.0 means this artifact can never satisfy the AI Hello power target without an external source.",
                ]
            )
            return data
        data["units_for_ai_hello"] = _round(AI_HELLO_WATTS / watts_per_unit)
        data["potatoes_equivalent"] = _round(watts_per_unit / POTATO_WATTS)
        data["cyclists_equivalent"] = _round(watts_per_unit / CYCLIST_WATTS)
        data["calculation_log"].extend(
            [
                f"Power path: {watts_per_unit} W per artifact.",
                f"AI Hello target: {AI_HELLO_WATTS} W.",
                f"Units required: {AI_HELLO_WATTS} / {watts_per_unit}.",
            ]
        )
        return data

    if mode == "compute":
        ops_per_second = numeric_value
        if ops_per_second == 0:
            data["time_seconds"] = -1.0
            data["time_years"] = -1.0
            data["can_evaluate"] = False
            data["calculation_log"].extend(
                [
                    "Compute path has 0 ops/sec.",
                    "Sentinel -1.0 means this artifact never completes the AI Hello operation target by itself.",
                ]
            )
            return data
        time_seconds = AI_HELLO_OPS / ops_per_second
        data["time_seconds"] = _round(time_seconds)
        data["time_years"] = _round(time_seconds / SECONDS_PER_YEAR)
        data["calculation_log"].extend(
            [
                f"Compute path: {ops_per_second} ops/sec.",
                f"AI Hello target: {AI_HELLO_OPS} operations.",
                f"Time required: {AI_HELLO_OPS} / {ops_per_second} seconds.",
            ]
        )
        return data

    data["calculation_log"].append(
        f"Path '{path}' is unsupported for direct power/compute calculation."
    )
    return data


def _load_request(path: str) -> tuple[str, float | None]:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    try:
        artifact_path = payload["path"]
    except KeyError as exc:
        raise ValueError("JSON request must include 'path'.") from exc
    value = payload.get("value", payload.get("watts_per_unit", payload.get("ops_per_second")))
    return artifact_path, value


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute deterministic AI-equivalence math for an artifact taxonomy path."
    )
    parser.add_argument("path", nargs="?", help="Artifact taxonomy path, or use --input-json.")
    parser.add_argument("value", nargs="?", help="Watts per unit for power paths; ops/sec for compute paths.")
    parser.add_argument("--input-json", help="JSON file containing path and value fields.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.input_json:
            path, value = _load_request(args.input_json)
        else:
            if not args.path:
                raise ValueError("Provide a taxonomy path or --input-json.")
            path, value = args.path, args.value
        result = run_calculation(path, value)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
