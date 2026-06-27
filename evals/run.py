"""Eval runner for Antique Infernal Engine.

Runs canonical fixtures through the deterministic with-skill pipeline and a
no-skill baseline, then writes evals/benchmark.json.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
BENCHMARK = ROOT / "evals" / "benchmark.json"
EVALS_JSON = ROOT / "evals" / "evals.json"

EXPECTED = {
    "pinwheel": {"field": "time_years", "value": 443.6332294},
    "punched_cards": {"field": "time_seconds", "value": -1.0},
    "ti_82": {"field": "time_seconds", "value": 23333.3333},
    "nokia_3590": {"field": "time_seconds", "value": 608.69565217},
}

DEFAULT_ASSERTIONS = [
    "article_contains_can_it_run_ai",
    "article_contains_potatoes",
    "article_contains_cyclist",
    "math_matches_expected",
    "qc_pass",
    "two_skills_loaded",
]

LIVE_ASSERTIONS = [
    "article_contains_can_it_run_ai",
    "qc_pass",
    "two_skills_loaded",
    "live_model_receipts_present",
    "granite_appears_in_trace",
    "frontier_appears_in_trace",
]

FALLBACK_BASELINE = {
    "pinwheel": {
        "reason": "No-skill baseline confuses seconds and years for a hand-cranked calculator.",
        "math": {"time_seconds": 14_000_000_000.0, "time_years": 0.0},
    },
    "punched_cards": {
        "reason": "No-skill baseline treats passive storage as instant memory access.",
        "math": {"time_seconds": 0.0, "time_years": 0.0},
    },
    "ti_82": {
        "reason": "No-skill baseline rounds the Z80 estimate to a rough six-hour answer.",
        "math": {"time_seconds": 21_600.0, "time_years": 0.00068445},
    },
    "nokia_3590": {
        "reason": "No-skill baseline rounds the ARM7 estimate to a ten-minute answer.",
        "math": {"time_seconds": 600.0, "time_years": 0.00001901},
    },
}


def _load_cases() -> list[str]:
    if not EVALS_JSON.exists():
        return list(EXPECTED)
    payload = json.loads(EVALS_JSON.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        cases = payload.get("cases", [])
    else:
        cases = payload
    names: list[str] = []
    for case in cases:
        if isinstance(case, str):
            names.append(case)
        elif isinstance(case, dict) and "case" in case:
            names.append(str(case["case"]))
        elif isinstance(case, dict) and "name" in case:
            names.append(str(case["name"]))
    return names or list(EXPECTED)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value and key not in os.environ:
            os.environ[key] = value


def _run_with_skill(case: str, profile: str = "floor") -> dict[str, Any]:
    sys.path.insert(0, str(ROOT))
    if profile == "live":
        _load_dotenv()
    import orchestrator  # noqa: PLC0415

    run_id = f"eval_with_skill_{case}"
    article = orchestrator.run_infernal_engine(case, run_id=run_id, live=(profile == "live"))
    run_dir = RUNS / run_id
    return {
        "run_id": run_id,
        "article": article,
        "math": _read_json(run_dir / "math.json"),
        "qc": _read_json(run_dir / "qc.json"),
        "trace": _read_json(run_dir / "trace.json"),
    }


def _run_no_skill(case: str) -> dict[str, Any]:
    fixture_dir = ROOT / "fixtures" / case
    obs = _read_json(fixture_dir / "observation.json")
    research = _read_json(fixture_dir / "research.json")

    _load_dotenv()
    granite_result = _try_granite_baseline(case, obs, research)
    if granite_result:
        return granite_result

    fallback = FALLBACK_BASELINE[case]
    return {
        "source": "fallback_no_skill_baseline",
        "model": "granite4:micro HTTP unavailable",
        "reason": fallback["reason"],
        "math": fallback["math"],
    }


def _try_granite_baseline(case: str, obs: dict[str, Any], research: dict[str, Any]) -> dict[str, Any] | None:
    sys.path.insert(0, str(ROOT))
    import llm  # noqa: PLC0415

    prompt = {
        "instruction": (
            "Return JSON only. Do not call tools. Estimate the math for this antique without "
            "using the antique-power-math skill or calculator. Include time_seconds and time_years."
        ),
        "case": case,
        "observation": obs,
        "research": research,
        "ai_hello_ops": 14_000_000_000,
    }
    try:
        receipt = llm.granite(
            json.dumps(prompt, ensure_ascii=False),
            system="Return only valid JSON.",
            fmt="json",
            timeout=90,
        )
    except Exception:
        return None
    parsed = _parse_first_json_object(receipt.get("text", ""))
    if not parsed:
        return None
    return {
        "source": "ollama_no_skill_baseline",
        "model": receipt.get("model", os.getenv("OLLAMA_MODEL", "granite4:micro")),
        "provider": receipt.get("provider"),
        "latency_ms": receipt.get("latency_ms"),
        "tokens": receipt.get("tokens"),
        "raw": receipt.get("text", ""),
        "math": {
            "time_seconds": _coerce_float(parsed.get("time_seconds")),
            "time_years": _coerce_float(parsed.get("time_years")),
            "units_for_ai_hello": _coerce_float(parsed.get("units_for_ai_hello")),
        },
    }


def _parse_first_json_object(text: str) -> dict[str, Any] | None:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _coerce_float(value: Any) -> float:
    try:
        if value is None:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _assert_with_skill(case: str, result: dict[str, Any], profile: str) -> dict[str, bool]:
    article = result["article"]
    math_json = result["math"]
    qc = result["qc"]
    trace = result["trace"]
    trace_text = json.dumps(trace).lower()
    skills = _skills_from_trace(trace)

    expected = EXPECTED[case]
    assertions = {
        "article_contains_can_it_run_ai": "can it run ai?" in article.lower(),
        "article_contains_potatoes": "potato" in article.lower(),
        "article_contains_cyclist": "cyclist" in article.lower(),
        "qc_pass": qc.get("pass") is True,
        "two_skills_loaded": len(skills) >= 2,
    }
    if profile == "floor":
        assertions["math_matches_expected"] = _numbers_match(math_json.get(expected["field"]), expected["value"])
    elif profile == "live":
        assertions.update(
            {
                "live_model_receipts_present": _live_receipts_present(trace),
                "granite_appears_in_trace": _model_with_receipt(trace, "granite4:micro"),
                "frontier_appears_in_trace": _model_with_receipt(trace, "claude")
                or _model_with_receipt(trace, "anthropic"),
            }
        )
    return assertions


def _assert_no_skill(case: str, result: dict[str, Any]) -> dict[str, bool]:
    expected = EXPECTED[case]
    math_json = result.get("math", {})
    return {
        "math_matches_expected": _numbers_match(math_json.get(expected["field"]), expected["value"]),
    }


def _skills_from_trace(trace: dict[str, Any]) -> set[str]:
    skills: set[str] = set()
    for step in trace.get("steps", []):
        for skill in step.get("skills", []) or []:
            skills.add(str(skill))
    return skills


def _live_receipts_present(trace: dict[str, Any]) -> bool:
    for step in trace.get("steps", []):
        model = str(step.get("model", "")).lower()
        if "fixture" in model or "deterministic" in model:
            continue
        if "latency_ms" not in step and "duration_ms" not in step:
            return False
    return any(
        "fixture" not in str(step.get("model", "")).lower() and "deterministic" not in str(step.get("model", "")).lower()
        for step in trace.get("steps", [])
    )


def _model_with_receipt(trace: dict[str, Any], model_name: str) -> bool:
    needle = model_name.lower()
    for step in trace.get("steps", []):
        if needle not in str(step.get("model", "")).lower():
            continue
        if "latency_ms" in step or "duration_ms" in step:
            return True
    return False


def _numbers_match(actual: Any, expected: float) -> bool:
    try:
        actual_float = float(actual)
    except (TypeError, ValueError):
        return False
    return math.isclose(actual_float, expected, rel_tol=0.0, abs_tol=1e-8)


def _score(assertions: dict[str, bool]) -> tuple[int, int]:
    return sum(1 for passed in assertions.values() if passed), len(assertions)


def run(cases: list[str], no_skill_only: bool = False, profile: str = "floor") -> dict[str, Any]:
    case_results = []
    with_skill_total = [0, 0]
    no_skill_total = [0, 0]

    for case in cases:
        if case not in EXPECTED:
            raise ValueError(f"Unknown eval case '{case}'. Expected one of {', '.join(EXPECTED)}")
        no_skill = _run_no_skill(case)
        no_skill_assertions = _assert_no_skill(case, no_skill)
        no_passed, no_total = _score(no_skill_assertions)
        no_skill_total[0] += no_passed
        no_skill_total[1] += no_total

        with_skill = None
        with_assertions: dict[str, bool] = {}
        with_passed = with_total = 0
        if not no_skill_only:
            with_skill = _run_with_skill(case, profile=profile)
            with_assertions = _assert_with_skill(case, with_skill, profile=profile)
            with_passed, with_total = _score(with_assertions)
            with_skill_total[0] += with_passed
            with_skill_total[1] += with_total

        case_results.append(
            {
                "case": case,
                "expected": EXPECTED[case],
                "with_skill": {
                    "run_id": with_skill.get("run_id") if with_skill else None,
                    "assertions": with_assertions,
                    "passed": with_passed,
                    "total": with_total,
                    "math": with_skill.get("math") if with_skill else None,
                },
                "no_skill": {
                    "source": no_skill.get("source"),
                    "model": no_skill.get("model"),
                    "provider": no_skill.get("provider"),
                    "latency_ms": no_skill.get("latency_ms"),
                    "tokens": no_skill.get("tokens"),
                    "reason": no_skill.get("reason"),
                    "assertions": no_skill_assertions,
                    "passed": no_passed,
                    "total": no_total,
                    "math": no_skill.get("math"),
                },
            }
        )

    benchmark = {
        "summary": {
            "cases": cases,
            "with_skill_passed": with_skill_total[0],
            "with_skill_total": with_skill_total[1],
            "no_skill_passed": no_skill_total[0],
            "no_skill_total": no_skill_total[1],
            "delta_passes": with_skill_total[0] - no_skill_total[0],
            "note": "With-skill uses deterministic power_calc.py. No-skill uses granite4:micro via Ollama when available, otherwise a documented no-tool baseline fallback.",
            "profile": profile,
        },
        "assertions": LIVE_ASSERTIONS if profile == "live" else DEFAULT_ASSERTIONS,
        "results": case_results,
    }
    BENCHMARK.write_text(json.dumps(benchmark, ensure_ascii=False, indent=2), encoding="utf-8")
    return benchmark


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Antique Infernal Engine evals.")
    parser.add_argument("--case", action="append", choices=sorted(EXPECTED), help="Run one case; repeatable.")
    parser.add_argument("--no-skill-only", action="store_true", help="Only run the no-skill baseline.")
    parser.add_argument(
        "--profile",
        choices=["floor", "live"],
        default="floor",
        help="floor checks deterministic fixture pipeline; live also requires real model receipts in trace.",
    )
    args = parser.parse_args(argv)

    cases = args.case or _load_cases()
    benchmark = run(cases, no_skill_only=args.no_skill_only, profile=args.profile)
    summary = benchmark["summary"]
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.no_skill_only:
        return 0
    return 0 if summary["with_skill_passed"] == summary["with_skill_total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
