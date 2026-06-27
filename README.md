# 🥔🔥 Antique Infernal Engine

> Upload a photo of an antique → receive a field-guide page that computes, with **real physics**, whether it could power or run AI inference. **The humor is decorative. The math is structural.**
>
> The Real Cat AI Labs · Agent Build Day (Lane 3) · 27JUN2026 · tied to the book *100 Ways to Power Artificial Intelligence*

## What it is
A small multi-agent system + two custom [Agent Skills](https://agentskills.io). Give it an antique; a vision agent identifies it, a researcher gathers the mechanism, a **local IBM Granite** model classifies its power/compute path and calls a **deterministic calculator**, a QC agent checks the units, and a writer emits a TRCL "Can It Run AI?" field-guide page (potato + cyclist equivalents included).

**The thesis:** a small local model (`granite4:micro`) is the *discipline-and-verification membrane*; frontier models *see and write*; **Python does the arithmetic**.

## Pipeline
`photo → observation → research → math (deterministic) → QC → article`

## Quickstart
```bash
uv sync
# fully local, zero keys:
uv run python orchestrator.py "test images/IMG_4523.JPG"
# validate the skills:
uv run skills-ref validate ./skills/antique-power-math
uv run skills-ref validate ./skills/trcl-field-guide-writer
# evals (with/without skill):
uv run python -m evals
```
*(Run-from-README finalized during the build window — see `docs/`.)*

## Model selection (the gate)
Runs **fully local with zero keys** (`granite4:micro` via Ollama). Frontier features (vision, prose) use `ANTHROPIC_API_KEY` — copy `.env.example` → `.env` and add keys. Full rationale + measured numbers in [`docs/MODEL_SELECTION.md`](docs/MODEL_SELECTION.md).

## Docs
- [`docs/ADLC.md`](docs/ADLC.md) — Agent Development Life Cycle worksheet
- [`docs/MODEL_SELECTION.md`](docs/MODEL_SELECTION.md) — local vs frontier rationale + receipts
- [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) — the 2–3 min demo

## License
MIT (see `LICENSE`).
