# Model Selection Rationale — Antiques Inference Engine
*Mandatory gate (all lanes): which model does which task + cost/latency/quality
justification. Measured numbers land from one smoke run into `runs/<id>/trace.json`.*

## Principle (the thesis)
The load-bearing part — the physics — is **deterministic**, so the **FLOOR deliberately
uses no model in the correctness path.** That is the thesis, not a gap: we can *prove* the
cheap/local/free path carries correctness, and we pay for a model only where it earns its
keep (senses + voice), on an opt-in `--live` profile. Small/local/free is not a fallback
here — it is the floor the whole verdict rests on.

## Two profiles
- **FLOOR (default · offline · zero keys):** fixtures + Python. Math = `power_calc.py`
  (exact). No classify/QC/vision/prose model in the correctness path. Trace honestly logs
  `deterministic` / `fixture`.
- **`--live` (ENHANCE · opt-in via `.env`):** `granite4:micro` classifies + QCs; Claude
  sees + writes. Real receipts (model · latency · tokens) logged in `trace.json`.

## Per-task routing
| Task | FLOOR | `--live` | Why the split |
|---|---|---|---|
| Photo vision | fixture `observation.json` | **Claude** | granite can't see; fixtures keep the demo offline-safe |
| Taxonomy classify | deterministic / fixture | **granite4:micro** (local) | constrained JSON into the `PowerOrComputePath` Literal; cheap, private |
| Math (assumptions -> arithmetic) | **Python (`power_calc.py`)** | **Python** | exact & reproducible in BOTH profiles — the model never does the math |
| QC (Reality Badger) | deterministic check | **granite4:micro** (local) | a local model as verifier — the strong claim |
| Final prose | deterministic template fill | **Claude** | voice + comedic precision (`trcl-field-guide-writer`) |
| Illustration prompt | — | Claude + **fal.ai** | brand image pipeline (STRETCH) |

## What's measured
- **FLOOR (measured now):** math is exact, ~instant, **$0**, **0 tokens**, **3/3** on the
  pinned fixtures (pinwheel 443.6332294 yr · TI-82 23,333.3333 s · punched cards -1.0).
- **`--live` (receipts pending the ENHANCE wiring — Flame1):** `granite4:micro` + Claude
  model/latency/token numbers populate `trace.json` from the smoke run. Until then we do
  not quote them — and we never print a model on a FLOOR trace that didn't run.

## One-liner
*"Granite classifies and verifies; frontier sees and writes; **Python calculates — in both
profiles.**"*

## Cost / latency note
FLOOR is free, offline, and demo-safe; `--live` spends event credits on exactly the two
tasks that need senses and style. The headline delta (`math_exact` 3/3 with-skill vs
granite-alone baseline) lives in [`evals/benchmark.json`](../evals/benchmark.json) /
[ADLC.md](ADLC.md) — and it is a **FLOOR** result, achieved with no frontier model.
