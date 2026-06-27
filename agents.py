"""agents.py — the five goblins of the Antiques Inference Engine.

FLOOR (this version): fixture-backed + deterministic — ZERO LLM calls, so the
core demo can never die on venue Wi-Fi or a dead key.
ENHANCE (later): swap artifact_goblin → Claude vision, reality_badger → granite
judge, page_goblin → granite/Claude prose using the trcl-field-guide-writer voice.

Technical: each agent reads typed contracts (models.py) and emits typed/JSON output.
Philosophical: five small hands, one frozen truth passed between them. 27JUN2026 · Flame.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from models import ArtifactObservation, QCResult, ResearchNotes

ROOT = Path(__file__).parent
FIXTURES = ROOT / "fixtures"

# Load TV's deterministic calculator as a module (no subprocess — fast + testable).
_pc_path = ROOT / "skills" / "antique-power-math" / "scripts" / "power_calc.py"
_spec = importlib.util.spec_from_file_location("power_calc", _pc_path)
power_calc = importlib.util.module_from_spec(_spec)
sys.modules["power_calc"] = power_calc  # register BEFORE exec so @dataclass introspection works (Py3.14)
_spec.loader.exec_module(power_calc)  # type: ignore


def _read_fixture(case: str, name: str) -> dict:
    return json.loads((FIXTURES / case / f"{name}.json").read_text(encoding="utf-8"))


# 1. ARTIFACT GOBLIN — sees, guesses the path.  FLOOR: fixture. ENHANCE: Claude vision.
def artifact_goblin(case: str, hint: str | None = None) -> ArtifactObservation:
    # hint (from the Badger via the orchestrator) would steer a real vision re-look.
    return ArtifactObservation(**_read_fixture(case, "observation"))


# 2. SHERLOCK OHMS — mechanism facts.  FLOOR: fixture. ENHANCE: research/Tavily.
def sherlock_ohms(obs: ArtifactObservation, case: str, hint: str | None = None) -> ResearchNotes:
    return ResearchNotes(**_read_fixture(case, "research"))


# 3. POTATO ACCOUNTANT — picks the variable, calls the deterministic calculator. FROZEN output.
def potato_accountant(obs: ArtifactObservation, research: ResearchNotes) -> dict:
    path = obs.power_or_compute_path
    value = _extract_value(research)
    return power_calc.run_calculation(path, value)  # raw dict: superset of MathResult


def _extract_value(research: ResearchNotes) -> float:
    """Pull watts (power paths) or ops/sec (compute paths) from research assumptions."""
    for a in research.usable_assumptions:
        param = str(a.get("parameter", "")).lower()
        if any(k in param for k in ("ops", "watt", "power")):
            try:
                return float(a.get("value", 0))
            except (TypeError, ValueError):
                return 0.0
    return 0.0


# 4. REALITY BADGER — verifies units, adjudicates the loop.  FLOOR: rule-based. ENHANCE: granite judge.
def reality_badger(math: dict, research: ResearchNotes, obs: ArtifactObservation) -> QCResult:
    reason, route = "ok", None
    if obs.confidence < 0.40:
        reason, route = "artifact confidence too low to assess", "artifact_goblin"
    elif math.get("mode") not in ("power", "compute", "unsupported", "absurd_power"):
        reason, route = f"bad math mode: {math.get('mode')}", "potato_accountant"
    elif math.get("can_evaluate") is False and math.get("mode") != "unsupported" \
            and not research.usable_assumptions:
        reason, route = "no usable assumption to compute from", "sherlock_ohms"
    passed = route is None
    return QCResult(**{"pass": passed, "reason": reason, "route_to": route})


# 5. PAGE GOBLIN — fills the field-guide page from FROZEN math.  FLOOR: deterministic render.
#    ENHANCE: granite/Claude prose via trcl-field-guide-writer voice_guide.
def page_goblin(math: dict, qc: QCResult, obs: ArtifactObservation, research: ResearchNotes) -> str:
    mode = math.get("mode")
    can = math.get("can_evaluate", True)

    # The verdict + the headline number, sentinel-aware (-1.0 => "Never (∞)").
    if mode == "compute":
        if not can or math.get("time_seconds", 0) < 0:
            verdict, headline = "❌ No — never, by itself.", "Time to one AI token: **Never (∞)** — it stores/much-too-slowly computes."
        else:
            yrs = math.get("time_years", 0)
            human = f"{yrs:,.2f} years" if yrs >= 1 else f"{math.get('time_seconds', 0):,.0f} seconds"
            verdict = "🐌 Technically… given geological patience."
            headline = f"Time for ONE AI token: **{human}**"
    elif mode == "power":
        if not can or math.get("units_for_ai_hello", 0) < 0:
            verdict, headline = "❌ No — it makes no usable power.", "Units for a 30W AI hello: **Never (∞)**"
        else:
            n = math.get("units_for_ai_hello", 0)
            verdict = "⚡ With enough of them, yes."
            headline = f"Units to reach a 30W AI hello: **{n:,.2f}**"
    else:
        verdict, headline = "❌ Decorative. Beautiful. Inert.", "It neither powers nor computes."

    potato = _fmt_equiv(math.get("potatoes_equivalent", 0), "potato battery", "potato batteries")
    cyclist = _fmt_equiv(math.get("cyclists_equivalent", 0), "cyclist", "cyclists")

    notes = "; ".join(n.get("claim", "") for n in research.historical_notes[:2]) or research.mechanism

    return f"""# 🥔 Antiques Inference Engine — Field Guide

## {obs.artifact_guess}
*{research.era} · path: `{obs.power_or_compute_path}` · confidence {obs.confidence:.0%}*

### Can it Run AI?
{verdict}

> {headline}

**What it actually did:** {research.mechanism}

**How we bully it into powering AI:** we treat its {('output watts' if mode=='power' else 'operations per second')} as the only resource it has, and ask the absurd question rigorously.

| Equivalent | |
|---|---|
| 🥔 Potatoes | {potato} |
| 🚴 Cyclists | {cyclist} |

**The math (frozen — the writer never edits it):**
```
{chr(10).join(math.get("calculation_log", []) or ["(see math.json)"])}
```

**Historical note:** {notes}

**Gotcha:** {_gotcha(mode, can)}

*The humor is decorative. The math is structural.*
"""


def _fmt_equiv(v, single, plural) -> str:
    if v is None or v < 0:
        return "— (n/a)"
    if v == 0:
        return "0"
    label = single if abs(v - 1) < 1e-9 else plural
    return f"≈ {v:,.0f} {label}" if v >= 1 else f"≈ {v:.4g} {label}"


def _gotcha(mode, can) -> str:
    if not can:
        return "It stores or symbolizes computation; it does not perform general AI inference. The first data-center job in history was a no-show."
    if mode == "power":
        return "Watts are power, not energy — and 'powers AI' is not 'runs AI.'"
    return "Cranks provide input power; gears perform the computation. Don't confuse the two."
