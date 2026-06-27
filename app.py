"""FastAPI single-page UI for the Antique Infernal Engine.

Serves the field-guide page and the pre-computed runs/<case>/ artifacts.
Zero-network by design: the primary demo reads fixtures the pipeline already
produced (article.md, math.json, trace.json). No external calls, no CDNs.

Run:  uv run python app.py        (or: uv run uvicorn app:app --reload)
Then: http://127.0.0.1:8000
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent
RUNS = ROOT / "runs"
STATIC = ROOT / "static"
IMAGES = ROOT / "test images"

# The demo arc order: cardboard (never) -> brass (centuries) -> calc (hours) -> phone (minutes).
ARC_ORDER = ["punched_cards", "pinwheel", "ti_82", "nokia_3590"]
DISPLAY = {
    "punched_cards": "Punched Cards (FORTRAN deck)",
    "pinwheel": "Rapid Calculator (pinwheel)",
    "ti_82": "Texas Instruments TI-82",
    "nokia_3590": "Nokia 3590 (AT&T)",
}
IMAGE_MAP = {
    "pinwheel": "IMG_4523.JPG",
    "punched_cards": "IMG_4526.JPG",
    "ti_82": "IMG_4527.JPG",
    "nokia_3590": "IMG_4524.JPG",
    "IMG_4523": "IMG_4523.JPG",   # live run (Claude saw the pinwheel photo)
}

app = FastAPI(title="Antique Infernal Engine")


def _read_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _is_live_extra(name: str) -> bool:
    """A live/ad-hoc run (Claude saw a fresh photo) — not a curated fixture, not eval scratch."""
    return name not in ARC_ORDER and not name.startswith("eval_")


def _display(case: str) -> str:
    if case in DISPLAY:
        return DISPLAY[case]
    obs = RUNS / case / "observation.json"
    if obs.exists():
        g = _read_json(obs).get("artifact_guess", "").split(" - ")[0].split(",")[0].strip()
        return f"🔴 LIVE: {g[:30]}" if g else f"🔴 LIVE: {case}"
    return case


LIVE_DEMO_RUNS = ("IMG_4523",)  # curated live run(s) for the demo rail (Claude saw this photo)


def _ordered_cases() -> list[str]:
    """Curated demo arc, then the curated LIVE run — excludes eval_*/other agents' QC scratch."""
    base = [c for c in ARC_ORDER if (RUNS / c / "math.json").exists()]
    live = [c for c in LIVE_DEMO_RUNS if (RUNS / c / "math.json").exists()]
    return base + live


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    page = STATIC / "index.html"
    if not page.exists():
        raise HTTPException(500, "static/index.html missing")
    return page.read_text(encoding="utf-8")


@app.get("/cases")
def cases() -> dict:
    out = []
    for c in _ordered_cases():
        m = _read_json(RUNS / c / "math.json")
        out.append({
            "case": c,
            "display": _display(c),
            "live": _is_live_extra(c),
            "time_seconds": m.get("time_seconds", 0.0),
            "can_evaluate": m.get("can_evaluate", True),
            "has_image": (IMAGES / IMAGE_MAP.get(c, "")).exists(),
        })
    return {"cases": out}


@app.get("/run/{case}")
def run(case: str) -> JSONResponse:
    d = RUNS / case
    if not (d / "math.json").exists():
        raise HTTPException(404, f"no run found for '{case}'")

    def maybe(name: str, default):
        p = d / name
        if not p.exists():
            return default
        return p.read_text(encoding="utf-8") if name.endswith(".md") else _read_json(p)

    return JSONResponse({
        "case": case,
        "display": _display(case),
        "article_md": maybe("article.md", ""),
        "math": maybe("math.json", {}),
        "trace": maybe("trace.json", {}),
        "qc": maybe("qc.json", {}),
        "observation": maybe("observation.json", {}),
        "research": maybe("research.json", {}),
        "has_image": (IMAGES / IMAGE_MAP.get(case, "")).exists(),
    })


@app.get("/image/{case}")
def image(case: str) -> FileResponse:
    fn = IMAGE_MAP.get(case)
    p = IMAGES / fn if fn else None
    if not p or not p.exists():
        raise HTTPException(404, f"no image for '{case}'")
    return FileResponse(p, media_type="image/jpeg")


# Mounted last so it never shadows the routes above.
if STATIC.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
