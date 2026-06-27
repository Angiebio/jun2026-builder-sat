"""agents_live.py — the ENHANCE (`--live`) agents: real granite + Claude, real receipts.

Mirrors agents.py but routes the two genuinely-fuzzy jobs to models, keeping the
math deterministic (the thesis holds in BOTH profiles):

  artifact_goblin   -> Claude vision   (sees the photo, proposes the path)
  sherlock_ohms     -> granite4:micro  (proposes mechanism + the ops/sec or watts assumption)
  potato_accountant -> Python power_calc (UNCHANGED — never a model's job)
  reality_badger    -> granite4:micro  (a LOCAL model as verifier — the strong claim)
  page_goblin       -> Claude          (voice + comedic precision)

Each returns (result, receipt) where receipt = {model, provider, latency_ms, tokens}.
On any model failure it falls back to the deterministic FLOOR agent and reports an
HONEST receipt (model='deterministic-fallback') — so `--live` degrades safely and the
trace never names a model that didn't run. 27JUN2026 · Flame.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import get_args

import agents  # FLOOR agents + power_calc + fixtures (the safe fallbacks)
import llm
from models import ArtifactObservation, PowerOrComputePath, QCResult, ResearchNotes

ROOT = Path(__file__).parent
# Authoritative valid paths come from the Pydantic Literal itself — never from
# taxonomy.json keys (those are groupings and drift from the validator).
PATHS = list(get_args(PowerOrComputePath))
_VOICE_F = ROOT / "skills" / "trcl-field-guide-writer" / "references" / "voice_guide.md"
VOICE = _VOICE_F.read_text(encoding="utf-8")[:2200] if _VOICE_F.exists() else ""


def _json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError(f"no JSON object in model output: {text[:160]}")
    return json.loads(m.group(0))


def _only(data: dict, model_cls) -> dict:
    """Keep only fields the Pydantic model declares (avoids extra-field rejects)."""
    return {k: v for k, v in data.items() if k in model_cls.model_fields}


def _fallback_receipt(tried_model: bool) -> dict:
    return {"model": "deterministic-fallback" if tried_model else "fixture",
            "provider": "local", "latency_ms": 0, "tokens": 0}


# 1. ARTIFACT GOBLIN — Claude vision.
def artifact_goblin(image_path: str | None = None, case: str | None = None, hint: str | None = None):
    if image_path:
        try:
            system = "You are an antique appraiser's trained eye. Return ONLY a JSON object, no prose."
            prompt = (
                "Identify this antique and the single power/compute path that best fits it.\n"
                f"`power_or_compute_path` MUST be exactly one of: {PATHS}.\n"
                "JSON keys: artifact_guess (str), confidence (0..1 float), visible_features (list[str]), "
                "alternate_guesses (list[str]), power_or_compute_path (str), questions_for_research (list[str])."
                + (f"\nThe QC step bounced this back — reconsider given: {hint}" if hint else "")
            )
            rec = llm.claude(prompt, system=system, image_path=image_path, max_tokens=700)
            data = _json(rec["text"])
            data.setdefault("confidence", 0.75)
            if data.get("power_or_compute_path") not in PATHS:
                data["power_or_compute_path"] = "decorative_or_unknown"
            return ArtifactObservation(**_only(data, ArtifactObservation)), rec
        except Exception as e:  # noqa: BLE001 — any failure degrades to a safe path
            print(f"[live artifact_goblin -> fallback] {type(e).__name__}: {e}", file=sys.stderr)
            if not case:  # fresh photo, no fixture to fall back to — minimal honest obs
                return ArtifactObservation(artifact_guess="unidentified antique", confidence=0.3,
                                           power_or_compute_path="decorative_or_unknown"), _fallback_receipt(True)
            return agents.artifact_goblin(case, hint=hint), _fallback_receipt(True)
    return agents.artifact_goblin(case, hint=hint), _fallback_receipt(False)


# 2. SHERLOCK OHMS — granite proposes mechanism + the one numeric assumption.
def sherlock_ohms(obs: ArtifactObservation, case: str | None = None, hint: str | None = None):
    try:
        is_power = obs.power_or_compute_path in {
            "galvanic_dc", "rotational_mechanical_power", "steam_rotational_power", "human_mechanical_power",
        }
        param = "watts" if is_power else "ops_per_second"
        prompt = (
            f"Antique: {obs.artifact_guess} (path: {obs.power_or_compute_path}). "
            f"Give compact research as JSON ONLY. Keys: artifact_family (str), era (str), mechanism (str), "
            f"historical_notes (list of {{claim, source}}), usable_assumptions (list of one "
            f"{{parameter: \"{param}\", value: <number>, confidence: \"low|medium|high\"}}). "
            f"Estimate a defensible {param} for one unit; be honest about uncertainty."
        )
        rec = llm.granite(prompt, system="Return only valid JSON.", fmt="json", timeout=45)
        data = _json(rec["text"])
        return ResearchNotes(**_only(data, ResearchNotes)), rec
    except Exception:  # noqa: BLE001
        return agents.sherlock_ohms(obs, case, hint=hint), _fallback_receipt(True)


# 3. POTATO ACCOUNTANT — deterministic Python. Imported unchanged; the math is never a model.
potato_accountant = agents.potato_accountant


# 4. REALITY BADGER — granite as verifier (with the deterministic checks as a floor).
def reality_badger(math: dict, research: ResearchNotes, obs: ArtifactObservation):
    det = agents.reality_badger(math, research, obs)  # deterministic guardrail always runs
    try:
        prompt = (
            "You are a skeptical units-and-claims auditor. Given an artifact, its research, and FROZEN math, "
            "decide if the assessment is sound. Watch for: watts vs joules confusion, 'powers AI' vs 'runs AI', "
            "a path that doesn't match the object, or an unsupported assumption. Return JSON ONLY: "
            "{pass: bool, reason: str, route_to: one of [null, \"artifact_goblin\", \"sherlock_ohms\", \"potato_accountant\"]}.\n"
            f"artifact={obs.artifact_guess} path={obs.power_or_compute_path} confidence={obs.confidence}\n"
            f"math={json.dumps({k: math.get(k) for k in ('mode','input_value','input_unit','can_evaluate','time_years','units_for_ai_hello')})}\n"
            f"assumptions={json.dumps(research.usable_assumptions)}"
        )
        rec = llm.granite(prompt, system="Return only valid JSON.", fmt="json", timeout=45)
        data = _json(rec["text"])
        gpass = bool(data.get("pass", True))
        greason = str(data.get("reason", "")).strip()[:200]
        # Deterministic guardrail is AUTHORITATIVE (the thesis: correctness is deterministic).
        # Granite is the verifier *voice* — a real local-model receipt + a reasoned note, not a veto
        # (a 3B judge is too unreliable to override exact math).
        note = f"granite[{'ok' if gpass else 'flag'}]: {greason or 'no issues found'}"
        reason = note if det.passed else f"{det.reason} | {note}"
        return QCResult(**{"pass": det.passed, "reason": reason, "route_to": det.route_to}), rec
    except Exception as e:  # noqa: BLE001
        print(f"[live reality_badger -> deterministic] {type(e).__name__}: {e}", file=sys.stderr)
        return det, _fallback_receipt(True)


# 5. PAGE GOBLIN — Claude writes the voice over the FROZEN math (never recomputes).
def page_goblin(math: dict, qc: QCResult, obs: ArtifactObservation, research: ResearchNotes):
    try:
        frozen = {k: math.get(k) for k in (
            "mode", "input_value", "input_unit", "units_for_ai_hello", "potatoes_equivalent",
            "cyclists_equivalent", "time_seconds", "time_years", "can_evaluate", "calculation_log")}
        system = (
            "You write TRCL 'Antique Infernal Engine' field-guide pages. Absurd but numerate; every joke sits on a "
            "real mechanism; never hide uncertainty; one memorable line. You NEVER change the math — it is frozen. "
            "If can_evaluate is false or a time is -1.0, the verdict is 'Never (∞)'. Output Markdown only.\n\n"
            f"VOICE GUIDE (excerpt):\n{VOICE}"
        )
        prompt = (
            f"Write the field-guide page. Use a heading '### Can it Run AI?' with the verdict, then sections: "
            f"what it actually did, how we bully it into powering AI, the frozen numbers (potatoes + cyclists + "
            f"time/units), a historical note, and a one-line gotcha. End with '*The humor is decorative. The math "
            f"is structural.*'\n\nartifact={obs.artifact_guess}\nresearch={research.model_dump()}\n"
            f"FROZEN_MATH={json.dumps(frozen)}"
        )
        rec = llm.claude(prompt, system=system, max_tokens=900)
        text = rec["text"]
        if "Can it Run AI" not in text:  # guarantee the brand phrase for the eval/screenshot
            text = f"### Can it Run AI?\n\n{text}"
        return text, rec
    except Exception:  # noqa: BLE001
        return agents.page_goblin(math, qc, obs, research), _fallback_receipt(True)
