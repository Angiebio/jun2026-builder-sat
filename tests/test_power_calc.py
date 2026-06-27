from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "antique-power-math" / "scripts" / "power_calc.py"


def load_power_calc():
    spec = importlib.util.spec_from_file_location("power_calc", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_power_path_calculates_units_potatoes_and_cyclists():
    power_calc = load_power_calc()

    result = power_calc.run_calculation("galvanic_dc", 0.5)

    assert result["mode"] == "power"
    assert result["input_unit"] == "watts"
    assert result["units_for_ai_hello"] == 60.0
    assert result["potatoes_equivalent"] == 5000.0
    assert result["cyclists_equivalent"] == 0.005
    assert result["time_seconds"] == 0.0


def test_compute_path_calculates_time_for_ai_hello():
    power_calc = load_power_calc()

    result = power_calc.run_calculation("mechanical_decimal_compute", 1)

    assert result["mode"] == "compute"
    assert result["input_unit"] == "ops_per_second"
    assert result["time_seconds"] == 14_000_000_000.0
    assert result["time_years"] == pytest.approx(443.6332294)
    assert result["units_for_ai_hello"] == 0.0


def test_silicon_microprocessor_compute_path_supports_real_fixtures():
    power_calc = load_power_calc()

    result = power_calc.run_calculation("silicon_microprocessor_compute", 600_000)

    assert result["mode"] == "compute"
    assert result["time_seconds"] == pytest.approx(23333.33333333)
    assert result["time_years"] == pytest.approx(0.00073939)


def test_unsupported_path_returns_non_evaluable_result_without_division():
    power_calc = load_power_calc()

    result = power_calc.run_calculation("decorative_or_unknown")

    assert result["mode"] == "unsupported"
    assert result["can_evaluate"] is False
    assert result["units_for_ai_hello"] == 0.0
    assert result["time_seconds"] == 0.0


@pytest.mark.parametrize(
    ("path", "value"),
    [
        ("galvanic_dc", -1),
        ("silicon_microprocessor_compute", -2),
    ],
)
def test_calculable_paths_fail_loud_on_negative_values(path, value):
    power_calc = load_power_calc()

    with pytest.raises(ValueError, match="WIRING FAILURE"):
        power_calc.run_calculation(path, value)


def test_zero_compute_value_returns_standard_json_sentinel():
    power_calc = load_power_calc()

    result = power_calc.run_calculation("punched_card_parallel_binary", 0)

    assert result["mode"] == "compute"
    assert result["can_evaluate"] is False
    assert result["time_seconds"] == -1.0
    assert result["time_years"] == -1.0


def test_zero_power_value_returns_standard_json_sentinel():
    power_calc = load_power_calc()

    result = power_calc.run_calculation("galvanic_dc", 0)

    assert result["mode"] == "power"
    assert result["can_evaluate"] is False
    assert result["units_for_ai_hello"] == -1.0


def test_unknown_taxonomy_fails_loud():
    power_calc = load_power_calc()

    with pytest.raises(ValueError, match="Unknown artifact path"):
        power_calc.run_calculation("haunted_teapot", 1)


def test_cli_outputs_json():
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "human_mechanical_power", "7"],
        check=True,
        capture_output=True,
        text=True,
    )

    result = json.loads(completed.stdout)
    assert result["path"] == "human_mechanical_power"
    assert result["units_for_ai_hello"] == pytest.approx(4.28571429)
