"""FastAPI single-page UI for the Antique Infernal Engine.

Serves the field-guide page and the pre-computed runs/<case>/ artifacts, AND
lets a visitor UPLOAD a photo to run the live pipeline (Claude + granite) in the
browser — then add/delete their own specimens.

Zero-network for the curated demo: it reads fixtures the pipeline already
produced (article.md, math.json, trace.json). Uploads run the live orchestrator
off the event loop; they degrade to the deterministic path if a model is down,
so the demo never hard-fails.

Run:  uv run python app.py        (or: uv run uvicorn app:app --reload)
Then: http://127.0.0.1:8000
27JUN2026 · Flame.
"""

from __future__ import annotations

import asyncio
import json
import re
import shutil
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

ROOT = Path(__file__).resolve().parent
RUNS = ROOT / "runs"
STATIC = ROOT / "static"
IMAGES = ROOT / "test images"
UPLOADS = ROOT / "uploads"          # visitor uploads — gitignored, never part of the judged deliverable

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
    "rubber_duck": "rubber_duck.jpg",   # edge-case live run (Claude saw a rubber duck)
}
LIVE_DEMO_RUNS = ("IMG_4523", "rubber_duck")  # curated live runs for the demo rail (Claude saw these)
PROTECTED = set(ARC_ORDER) | set(LIVE_DEMO_RUNS)  # the demo itself — never deletable via the UI

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_UPLOAD = 12_000_000  # 12 MB — a phone photo, not a payload

app = FastAPI(title="Antique Infernal Engine")


# ── helpers ────────────────────────────────────────────────────────────────
def _read_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _safe_case(case: str) -> str:
    """No path traversal: a case id is a single flat token. Fail loud on anything else."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", case or ""):
        raise HTTPException(400, "bad case id")
    return case


def _is_upload(case: str) -> bool:
    """A visitor-uploaded specimen — marked, listable, and the only kind we let the UI delete."""
    return (RUNS / case / "source.json").exists()


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


def _image_path(case: str) -> Path | None:
    """Curated fixture image first (test images/), then a visitor upload (uploads/<case>.*)."""
    fn = IMAGE_MAP.get(case)
    if fn and (IMAGES / fn).exists():
        return IMAGES / fn
    if UPLOADS.exists():
        for p in sorted(UPLOADS.glob(f"{case}.*")):
            return p
    return None


def _ordered_cases() -> list[str]:
    """Curated demo arc, then curated LIVE runs, then the visitor's uploads (oldest→newest).
    Excludes eval_*/other agents' QC scratch — only marked uploads join the rail."""
    base = [c for c in ARC_ORDER if (RUNS / c / "math.json").exists()]
    live = [c for c in LIVE_DEMO_RUNS if (RUNS / c / "math.json").exists()]
    uploads: list[str] = []
    if RUNS.exists():
        ups = [d for d in RUNS.iterdir()
               if d.is_dir() and d.name not in base and d.name not in live
               and (d / "source.json").exists() and (d / "math.json").exists()]
        ups.sort(key=lambda d: d.stat().st_mtime)  # newest specimen lands at the end of the rail
        uploads = [d.name for d in ups]
    return base + live + uploads


def _new_case_id(filename: str) -> str:
    """A flat, collision-free id from the filename stem, namespaced so uploads never
    shadow a curated case or eval scratch."""
    stem = re.sub(r"[^a-z0-9_-]+", "-", Path(filename).stem.lower()).strip("-")[:32] or "photo"
    base = f"up_{stem}"
    cand, n = base, 2
    while (RUNS / cand).exists() or list(UPLOADS.glob(f"{cand}.*")):
        cand, n = f"{base}-{n}", n + 1
    return cand


# ISO-BMFF 'ftyp' brands that mean HEIC/HEIF. The iPhone default. Claude vision
# can't read it and most desktop browsers won't render it — and we have no
# transcoder on this laptop — so we sniff + reject with an actionable message
# (by magic bytes too, since iPhones sometimes hand us a .jpg name on HEIC data).
_HEIC_BRANDS = {b"heic", b"heix", b"hevc", b"hevx", b"heim", b"heis",
                b"hevm", b"hevs", b"mif1", b"msf1", b"heif"}


def _is_heic(raw: bytes) -> bool:
    return len(raw) >= 12 and raw[4:8] == b"ftyp" and raw[8:12] in _HEIC_BRANDS


# ── routes ─────────────────────────────────────────────────────────────────
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
            "deletable": _is_upload(c),
            "mode": m.get("mode", ""),
            "time_seconds": m.get("time_seconds", 0.0),
            "input_value": m.get("input_value", 0.0),
            "units_for_ai_hello": m.get("units_for_ai_hello", 0.0),
            "can_evaluate": m.get("can_evaluate", True),
            "has_image": _image_path(c) is not None,
        })
    return {"cases": out}


@app.get("/run/{case}")
def run(case: str) -> JSONResponse:
    _safe_case(case)
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
        "has_image": _image_path(case) is not None,
    })


@app.get("/image/{case}")
def image(case: str) -> FileResponse:
    _safe_case(case)
    p = _image_path(case)
    if not p or not p.exists():
        raise HTTPException(404, f"no image for '{case}'")
    ext = p.suffix.lower()
    media = {".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}.get(ext, "image/jpeg")
    return FileResponse(p, media_type=media)


@app.post("/upload")
async def upload(request: Request, filename: str = "photo.jpg") -> JSONResponse:
    """Accept a raw image body (no python-multipart needed), save it, and run the
    LIVE pipeline off the event loop. Returns the new case id for the UI to open."""
    raw = await request.body()
    if not raw:
        raise HTTPException(400, "empty upload")
    if len(raw) > MAX_UPLOAD:
        raise HTTPException(413, "image too large (max 12 MB)")
    ext = Path(filename).suffix.lower()
    if ext in {".heic", ".heif"} or _is_heic(raw):
        raise HTTPException(415,
            "HEIC/HEIF photos can't run live vision. On iPhone: Settings -> Camera -> "
            "Formats -> Most Compatible, or share/export the photo as JPEG, then re-upload.")
    if ext not in ALLOWED_EXT:
        ext = ".jpg"
    case = _new_case_id(filename)
    UPLOADS.mkdir(exist_ok=True)
    img_path = UPLOADS / f"{case}{ext}"
    await asyncio.to_thread(img_path.write_bytes, raw)

    # Mark it an uploaded specimen UP FRONT: the run becomes discoverable the instant
    # math.json lands (both markers gate listing), and the cleanup path below now
    # sweeps source.json too — no orphan "invisible" dir if the pipeline throws.
    run_dir = RUNS / case
    run_dir.mkdir(parents=True, exist_ok=True)
    await asyncio.to_thread(
        (run_dir / "source.json").write_text,
        json.dumps({"source": "upload", "filename": filename, "image": img_path.name}, ensure_ascii=False),
        encoding="utf-8")

    # The live pipeline is blocking (~60–90s) — run it in a worker thread so the
    # server stays responsive. It degrades to deterministic agents on any model
    # failure, so this raises only on a genuine bug, not on a dead key / offline.
    import orchestrator
    try:
        await run_in_threadpool(orchestrator.run_infernal_engine, "", case, True, str(img_path))
    except Exception as e:  # fail loud + clean up the half-made artifacts (incl. source.json)
        shutil.rmtree(run_dir, ignore_errors=True)
        img_path.unlink(missing_ok=True)
        raise HTTPException(500, f"live pipeline failed: {type(e).__name__}: {e}") from e

    return JSONResponse({"case": case, "display": _display(case)})


@app.delete("/case/{case}")
def delete_case(case: str) -> JSONResponse:
    """Remove a visitor-uploaded specimen (run dir + image). The curated demo is protected."""
    _safe_case(case)
    if case in PROTECTED or not _is_upload(case):
        raise HTTPException(403, "only uploaded specimens can be removed")
    d = RUNS / case
    shutil.rmtree(d, ignore_errors=True)
    # OneDrive/file-watcher can briefly hold the now-empty dir handle so the final
    # rmdir fails (contents are already gone). Sweep the husk if it lingers.
    if d.exists():
        try:
            d.rmdir()
        except OSError:
            pass  # empty + invisible to the app (no math.json) — harmless if it lingers a beat
    if UPLOADS.exists():
        for p in UPLOADS.glob(f"{case}.*"):
            p.unlink(missing_ok=True)
    return JSONResponse({"ok": True, "deleted": case})


# Mounted last so it never shadows the routes above.
if STATIC.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
