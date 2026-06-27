# 🥔🔥 Antique Infernal Engine

> Give it an antique → get a field-guide page that computes, with **real physics**, whether it could power or run AI inference. **The humor is decorative. The math is structural.**
>
> The Real Cat AI Labs · Agent Build Day, Lane 3 · 27JUN2026 · tied to the book *100 Ways to Power Artificial Intelligence*

## What it is
A multi-agent system + two custom [Agent Skills](https://agentskills.io). Five agents cooperate through a **bounded adjudication loop** (the Lane-3 delegation mechanism): an artifact analyst sees the object and proposes its power/compute path, a researcher gathers the mechanism, the **`antique-power-math` skill** runs a **deterministic** `power_calc.py` to get the *exact* number, a QC "Reality Badger" verifies it (and can kick work back to an earlier agent), and the **`trcl-field-guide-writer` skill** emits the "Can it Run AI?" page (with potato + cyclist equivalents).

**The thesis (and the model-selection story):** the load-bearing part — the physics — is **deterministic**, so correctness needs **no model at all**. A small local model (`granite4:micro`) and a frontier model (Claude) are **opt-in** for the only two genuinely fuzzy jobs — *seeing the photo* and *writing the voice*. We can *prove* the cheap/local/free path carries the math; we pay for a model only where it earns its keep.

## Pipeline
```
            ┌──────── ⟲ kick back (≤2×) ────────┐
            ↓                                    │
 antique → goblin → sherlock → accountant → reality-badger ─(pass)→ page → field-guide
          (sees)   (research)  (power_calc,    (verifies units)            (frozen math)
                                deterministic)
```

## Quickstart
```bash
uv sync

# run any of the 4 demo antiques (fully local, zero keys, zero network):
uv run python orchestrator.py pinwheel          # cases: pinwheel | punched_cards | ti_82 | nokia_3590

# validate the two skills against the agentskills.io spec:
uv run agentskills validate ./skills/antique-power-math
uv run agentskills validate ./skills/trcl-field-guide-writer

# the eval delta (the whole point — skill vs no-skill):
uv run python -m evals

# the single-page field-guide UI:
uv run python app.py        # → http://127.0.0.1:8000
```

## Does the skill actually help? (Skill Quality)
Measured by `evals/run.py` over the 4 fixtures, **with-skill vs a real `granite4:micro`-alone baseline**:

| | passed |
|---|---|
| **with `antique-power-math`** | **24 / 24** |
| no-skill (granite guesses the math) | **0 / 4** |
| **delta** | **+24** |

The skill doesn't make the prose nicer — it makes the math *true*. Granite alone confuses seconds and years and treats punched cards as instant memory; the deterministic calculator is exact and reproducible (pinwheel **443.63 yr** · TI-82 **6.48 h** · Nokia **10.1 min** · punch cards **Never ∞**).

## Model selection (mandatory gate)
| Task | Model | Why |
|---|---|---|
| The math | **Python (`power_calc.py`)** | deterministic, exact, $0, 0 tokens — *the correctness is here, not in a model* |
| Path classify + QC | **rule-based deterministic** (FLOOR) → **`granite4:micro`** (`--live`) | constrained, local, free; the small model is the verification membrane when enabled |
| See the photo | **Claude** (`--live`, `ANTHROPIC_API_KEY`) | granite can't see |
| Write the voice | **Claude** (`--live`) | comedic precision |

Runs **fully local with zero keys** by default (the demo can't die on Wi-Fi). Frontier features are opt-in via `.env` (`cp .env.example .env`). Full rationale: [`docs/MODEL_SELECTION.md`](docs/MODEL_SELECTION.md).

## Docs
- [`docs/ADLC.md`](docs/ADLC.md) — the worked iteration loop (v1 model-guessed → v2 script), with evidence
- [`docs/MODEL_SELECTION.md`](docs/MODEL_SELECTION.md) — per-task routing + measured receipts
- [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) — the 2–3 minute run-of-show

## License
MIT (see [`LICENSE`](LICENSE)).
