"""orchestrator.py — the Lane 3 planner + bounded ADJUDICATION LOOP.

Not a linear chain: the Reality Badger can kick work back, and this orchestrator
re-dispatches to an earlier agent (re-look / re-research), capped at MAX_LOOPS.
Writes file-backed JSON to runs/<id>/ and a visible trace.json (demo + Lane 3 evidence).

Usage:  uv run python orchestrator.py [case]      # case = a folder under fixtures/
27JUN2026 · Flame.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import agents

ROOT = Path(__file__).parent
RUNS = ROOT / "runs"
MAX_LOOPS = 2  # bounded — the Badger can kick back; the orchestrator never loops forever


def _dump(obj):
    if hasattr(obj, "model_dump"):
        return obj.model_dump(by_alias=True)
    return obj


def _write(run_dir: Path, name: str, obj) -> None:
    (run_dir / f"{name}.json").write_text(
        json.dumps(_dump(obj), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _rec(r: dict) -> dict:
    """Pull the honest trace receipt fields from an agents_live model call."""
    return {"model": r.get("model"), "provider": r.get("provider"),
            "latency_ms": r.get("latency_ms"), "tokens": r.get("tokens")}


def _run_live(case: str | None, image_path: str | None = None, run_id: str | None = None) -> str:
    """ENHANCE profile: Claude sees, granite researches + QCs, Python computes, Claude writes.
    Every step logs a REAL receipt; falls back to deterministic on any model failure."""
    import agents_live

    run_id = run_id or case or (Path(image_path).stem if image_path else "live")
    run_dir = RUNS / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    trace: list[dict] = []

    obs, rv = agents_live.artifact_goblin(image_path=image_path, case=case)
    _write(run_dir, "observation", obs)
    trace.append({"agent": "artifact_goblin (vision)", **_rec(rv), "guess": obs.artifact_guess})

    research, rr = agents_live.sherlock_ohms(obs, case=case)
    _write(run_dir, "research", research)
    trace.append({"agent": "sherlock_ohms (research)", **_rec(rr), "family": research.artifact_family})

    math, qc, attempt = None, None, 0
    for attempt in range(MAX_LOOPS):
        math = agents_live.potato_accountant(obs, research)  # deterministic — never a model
        _write(run_dir, "math", math)
        trace.append({"agent": f"potato_accountant (loop {attempt + 1})",
                      "model": "deterministic (python)", "skills": ["antique-power-math"]})
        qc, rq = agents_live.reality_badger(math, research, obs)
        _write(run_dir, "qc", qc)
        trace.append({"agent": f"reality_badger (loop {attempt + 1})", **_rec(rq),
                      "skills": ["antique-power-math"], "pass": qc.passed,
                      "route_to": qc.route_to, "reason": qc.reason})
        if qc.passed:
            break
        if qc.route_to == "artifact_goblin":
            obs, rv = agents_live.artifact_goblin(image_path=image_path, case=case, hint=qc.reason)
            _write(run_dir, "observation", obs)
        elif qc.route_to == "sherlock_ohms":
            research, rr = agents_live.sherlock_ohms(obs, case=case, hint=qc.reason)
            _write(run_dir, "research", research)

    article, rp = agents_live.page_goblin(math, qc, obs, research)
    (run_dir / "article.md").write_text(article, encoding="utf-8")
    trace.append({"agent": "page_goblin (prose)", **_rec(rp),
                  "skills": ["trcl-field-guide-writer"], "output": "article.md"})

    _write(run_dir, "trace", {"case": run_id, "profile": "live", "loops": attempt + 1,
                              "passed": qc.passed, "steps": trace})
    return article


def run_infernal_engine(case: str, run_id: str | None = None, live: bool = False,
                        image_path: str | None = None) -> str:
    if live or image_path:
        return _run_live(case, image_path, run_id)
    run_id = run_id or case
    run_dir = RUNS / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    trace: list[dict] = []

    obs = agents.artifact_goblin(case)
    _write(run_dir, "observation", obs)
    trace.append({"agent": "artifact_goblin", "model": "fixture", "guess": obs.artifact_guess})

    research = agents.sherlock_ohms(obs, case)
    _write(run_dir, "research", research)
    trace.append({"agent": "sherlock_ohms", "model": "fixture", "family": research.artifact_family})

    math, qc, attempt = None, None, 0
    for attempt in range(MAX_LOOPS):
        math = agents.potato_accountant(obs, research)
        _write(run_dir, "math", math)
        qc = agents.reality_badger(math, research, obs)
        _write(run_dir, "qc", qc)
        trace.append({
            "agent": f"accountant+badger (loop {attempt + 1})", "model": "deterministic",
            "skills": ["antique-power-math"],
            "pass": qc.passed, "route_to": qc.route_to, "reason": qc.reason,
        })
        if qc.passed:
            break
        # ⟲ ADJUDICATION: orchestrator re-dispatches to the agent the Badger blames.
        if qc.route_to == "artifact_goblin":
            obs = agents.artifact_goblin(case, hint=qc.reason)
            _write(run_dir, "observation", obs)
        elif qc.route_to == "sherlock_ohms":
            research = agents.sherlock_ohms(obs, case, hint=qc.reason)
            _write(run_dir, "research", research)
        # else: loop simply re-runs the accountant

    article = agents.page_goblin(math, qc, obs, research)
    (run_dir / "article.md").write_text(article, encoding="utf-8")
    trace.append({
        "agent": "page_goblin",
        "model": "deterministic",
        "skills": ["trcl-field-guide-writer"],
        "output": "article.md",
    })

    _write(run_dir, "trace", {"case": case, "loops": attempt + 1, "passed": qc.passed, "steps": trace})
    return article


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows console: print 🥔 safely
    except Exception:
        pass
    raw = sys.argv[1:]
    forced_live = "--live" in raw
    rest = [a for a in raw if a != "--live"]
    target = rest[0] if rest else "pinwheel"
    is_image = target.lower().endswith((".jpg", ".jpeg", ".png"))
    if forced_live or is_image:
        print(run_infernal_engine("" if is_image else target, live=True,
                                  image_path=target if is_image else None))
        print("\n[LIVE run — real model receipts in trace.json]")
    else:
        print(run_infernal_engine(target))
        print(f"\n[run written to runs/{target}/ — observation, research, math, qc, article.md, trace.json]")
