# 🥔🔥 Antique Infernal Engine

> Hand it a photo of an antique. Get a TRCL field-guide page that computes, with **real physics**, whether the thing could power or run AI.

**The humor is decorative. The math is structural.**

[![License: MIT](https://img.shields.io/badge/License-MIT-4a0873.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-5bb545.svg)](https://www.python.org/)
[![Runs fully local](https://img.shields.io/badge/runs-fully%20local%20·%20zero%20keys-5bb545.svg)](#quickstart)
[![Skill vs baseline](https://img.shields.io/badge/skill%20vs%20baseline-24%2F24%20vs%200%2F4-f5841f.svg)](#does-the-skill-earn-its-place)
[![Lane 3](https://img.shields.io/badge/lane-3%20·%20multi--agent%20%2B%20skills-e8e52a.svg)](#how-it-works)

A small multi-agent system from [therealcat.ai](https://therealcat.ai) that answers the least efficient question in history: *could this antique run AI?* It is Angie's book *100 Ways to Power Artificial Intelligence* turned into a working agent — five cooperating sub-agents, two custom [Agent Skills](https://agentskills.io), a deterministic physics core, and an adjudication loop that argues with itself until the numbers hold up.

The interesting part isn't the verdict. It's the math you have to survive to get there.

---

## Contents

- [What it does](#what-it-does)
- [How it works](#how-it-works)
- [Quickstart](#quickstart)
- [Usage](#usage)
- [Model selection — the gate](#model-selection--the-gate)
- [The two skills](#the-two-skills)
- [Does the skill earn its place?](#does-the-skill-earn-its-place)
- [Project structure](#project-structure)
- [The agent crew](#the-agent-crew)
- [License](#license)

---

## What it does

Hand it a photo of an antique — a pinwheel calculator, a FORTRAN punch-card deck, a TI-82, a Nokia candybar — and it produces a single **field-guide page**:

- **Identifies** the artifact and its real mechanism.
- **Classifies** the path: can it *produce* power (watts?), or can it *compute* (operations over time?).
- **Calculates** — with frozen, deterministic math — how long, or how many units, it would take to reach one *"AI hello,"* plus the equivalent in **potato batteries** and in **pedaling cyclists**.
- **Writes** it up in the TRCL field-guide voice: absurd but numerate, every joke sitting on a real number.

Every page is reproducible. The prose model never touches arithmetic — it receives frozen math, and only then is it allowed to be funny.

> **The four-specimen arc.** Punched cards: *never.* Pinwheel calculator: *443 years.* TI-82: *six and a half hours.* Nokia 3590: *ten minutes.* The hardware gets younger; the verdict gets faster. Same question, same physics, every time.

---

## How it works

This is **not** a linear chain. The **Reality Badger** verifies the math and, on failure, returns a `route_to` naming which earlier agent is at fault. The **orchestrator adjudicates and re-dispatches** — back to the Artifact Goblin to *re-look*, or to Sherlock Ohms to *re-research* — bounded by `MAX_LOOPS`. That feedback loop is what makes this a cooperating multi-agent system instead of a pipeline, and it is fully visible in `trace.json`.

![Architecture: the adjudication loop](documentation/orchestration-overview.png)

<sub>Vector source: [`documentation/architecture.svg`](documentation/architecture.svg) · illustrated manual: [`documentation/antique-infernal-engine-guide.html`](documentation/antique-infernal-engine-guide.html)</sub>

```python
# orchestrator.py — planner + 5 sub-agents, a bounded ADJUDICATION LOOP
MAX_LOOPS = 2  # the Badger can kick work back; the orchestrator never loops forever

def run_infernal_engine(case):                       # case = a fixture under fixtures/
    obs      = artifact_goblin(case)                 # sees the antique      → observation.json
    research = sherlock_ohms(obs, case)              # mechanism facts       → research.json
    for attempt in range(MAX_LOOPS):
        math = potato_accountant(obs, research)      # skill + power_calc.py → math.json (FROZEN)
        qc   = reality_badger(math, research, obs)   # → {pass, reason, route_to}
        if qc.passed:
            break
        # ⟲ adjudication: re-dispatch to the agent the Badger blames, reason passed as a hint
        if   qc.route_to == "artifact_goblin": obs      = artifact_goblin(case, hint=qc.reason)
        elif qc.route_to == "sherlock_ohms":   research = sherlock_ohms(obs, case, hint=qc.reason)
    article = page_goblin(math, qc, obs, research)   # writer skill → article.md (frozen math only)
    write_trace(case, loops=attempt + 1)             # the loop is VISIBLE in trace.json
    return article
```

**The five agents**

| Agent | Job | Emits |
|---|---|---|
| 🔎 **Artifact Goblin** | Sees the photo; separates *visible* from *inferred*; guesses the path | `observation.json` |
| 🧪 **Sherlock Ohms** | Researches the real mechanism and its numbers | `research.json` |
| 🥔 **Potato Accountant** | Classifies the path; calls the deterministic calculator | `math.json` *(frozen)* |
| 🦡 **Reality Badger** | Verifies units and claims; returns `route_to` on failure | `qc.json` |
| 📝 **Page Goblin** | Writes the field-guide page from frozen math | `article.md` |

The Badger fails a run when artifact confidence is too low, the math mode is wrong, or there's no usable assumption to compute from — and it names the agent to send the work back to. *"Powers AI"* is never allowed to pass as *"runs AI."*

---

## Quickstart

**Runs fully local with zero keys.** The default **FLOOR** profile is deterministic — fixtures + Python — so the core demo can never die on venue Wi-Fi or a dead API key.

```bash
# 1 · clone
git clone https://github.com/Angiebio/jun2026-builder-sat
cd jun2026-builder-sat

# 2 · install (uv-managed env — no requirements.txt)
uv sync

# 3 · run a bundled fixture — zero network, zero keys
uv run python orchestrator.py pinwheel
#    → runs/pinwheel/article.md   +   runs/pinwheel/trace.json
```

```bash
# 4 · or serve the single-page field guide
uv run python app.py            # → http://127.0.0.1:8000
```

**Optional — turn on `--live` frontier features** (live vision on your own photos, sharper prose):

```bash
cp .env.example .env            # then add your key
# ANTHROPIC_API_KEY=...           ($50 attendee credits at the event)
```

---

## Usage

```bash
# Run any of the four bundled fixtures (deterministic, fully local)
uv run python orchestrator.py pinwheel        # mechanical calculator → 443 years
uv run python orchestrator.py ti_82           # graphing calculator   → 6.5 hours
uv run python orchestrator.py nokia_3590      # candybar phone        → 10 minutes
uv run python orchestrator.py punched_cards   # FORTRAN deck          → never

# Serve the single-page web UI at http://127.0.0.1:8000
uv run python app.py

# Validate both skills against the agentskills.io spec (the shippability gate)
uv run python -m skills_ref.cli validate ./skills/antique-power-math
uv run python -m skills_ref.cli validate ./skills/trcl-field-guide-writer

# Run the eval suite, with and without the skill → evals/benchmark.json
uv run python -m evals
```

Every run writes a self-contained folder:

```
runs/<case>/
├── observation.json   research.json
├── math.json          qc.json          article.md
└── trace.json         ← loops, pass/fail, route_to, skills loaded per step
```

Open `trace.json` to watch the loop: the Badger's verdict, the `route_to`, and the loop count are all logged. **That trail is the demo.**

---

## Model selection — the gate

> **Granite classifies and verifies; frontier sees and writes; Python calculates — in both profiles.**

The load-bearing part — the physics — is **deterministic**, so the default **FLOOR profile deliberately uses no model in the correctness path.** That is the thesis, not a gap: we can *prove* the free / local / offline path carries correctness, and we pay for a model only where it earns its keep — **senses and voice** — on an opt-in `--live` profile.

| Task | FLOOR · default · offline · zero keys | `--live` · opt-in via `.env` |
|---|---|---|
| Photo vision | fixture `observation.json` | **Claude** *(can see antique photos; Granite can't)* |
| Classify path | deterministic | **granite4:micro** *(local, constrained JSON)* |
| Math (assumptions → arithmetic) | **Python — `power_calc.py`** | **Python — `power_calc.py`** *(exact in both)* |
| QC · Reality Badger | deterministic check | **granite4:micro** *(a local model as verifier — the strong claim)* |
| Final prose | deterministic template fill | **Claude** *(voice + comedic precision)* |

`trace.json` logs this **honestly**: on the FLOOR it records `model: deterministic` / `fixture` — there is no model in the correctness path, by design, and we never print a model we didn't call. Full rationale + measured receipts in [`docs/MODEL_SELECTION.md`](docs/MODEL_SELECTION.md).

---

## The two skills

### `antique-power-math` — the deterministic one

The LLM proposes the taxonomy path and one physical assumption; **Python does the arithmetic.** Constants are frozen:

```yaml
# skills/antique-power-math/references/constants.yaml
ai_hello_watts: 30            # power to run one "AI hello"
ai_hello_ops:   14000000000   # operations behind one hello (14 billion)
potato_watts:   0.0001        # one potato battery
cyclist_watts:  100           # one human, pedaling
```

```
compute path:  time_seconds       = 14_000_000_000 / ops_per_second
power path:    units_for_ai_hello = 30 / watts_per_unit
               potatoes_per_unit  = watts_per_unit / 0.0001
               cyclists_per_unit  = watts_per_unit / 100
```

Guard: a negative value on a calculable path **fails loud** — no silent zero, no fabricated unit. A *zero* on a compute path becomes the sentinel `-1.0` (`can_evaluate=false`), which the writer renders as **"Never (∞)"** — standards-clean JSON, no division by zero. Outputs are rounded once, at the end.

### `trcl-field-guide-writer` — the voice one

Enforces the field-guide schema and tone: absurd but numerate, never hiding uncertainty, one memorable line per page — *Title · Era · Path · Confidence · What it actually did · How we bully it into powering AI · **Can it Run AI?** · the Math · Potato Equivalent · Cyclist Equivalent · Historical note · Gotcha.* **The writer receives frozen math and never recalculates.** It can only narrate the answer.

Both pass `agentskills validate` against the [agentskills.io](https://agentskills.io) spec.

---

## Does the skill earn its place?

Measured by `evals/run.py` over all four fixtures, **with-skill vs a real `granite4:micro`-alone baseline** — `profile: floor`, reproduced fresh from this repo:

| | passed |
|---|---|
| **with `antique-power-math`** | **24 / 24** |
| no-skill *(granite guesses the math)* | **0 / 4** |
| **delta** | **+24** |

Assertions are **script-checked, not LLM-judged**: the page must contain *"Can it Run AI?"* plus the potato and cyclist equivalents, the math JSON must match the calculator **exactly** (tolerance 0, sentinel included), QC must pass, and at least two skills must appear in the trace. The pinned numbers:

| Fixture | Path | The number it must land |
|---|---|---|
| Pinwheel calculator | `mechanical_decimal_compute` | 1 op/s → **443.6332294 years** |
| TI-82 | `silicon_microprocessor_compute` | 600 000 ops/s → **23 333.3333 s** (~6.5 h) |
| Nokia 3590 | `silicon_microprocessor_compute` | 23 000 000 ops/s → **608.70 s** (~10 min) |
| Punched cards | `punched_card_parallel_binary` | 0 ops/s → **`-1.0` sentinel** = *"never computes"* |

The skill doesn't make the prose nicer — it makes the math *true.* Granite alone confuses *seconds* with *years* and treats a passive punch-card deck as instant memory; the deterministic calculator is exact and reproducible. A skill that can't beat its `--no-skill` baseline isn't earning its place — so we measure it.

---

## Project structure

```
jun2026-builder-sat/
├── README.md  LICENSE                    # MIT
├── pyproject.toml  uv.lock               # uv-managed env (no requirements.txt)
├── orchestrator.py                       # planner + bounded adjudication loop (CLI)
├── app.py                                # FastAPI single-page field guide (serve)
├── agents.py                             # the five goblins — fixture FLOOR; --live overlays models
├── models.py                             # Pydantic membrane — strict types at every boundary
├── llm.py                                # --live model layer: Granite (Ollama) + Claude, with receipts
├── skills/
│   ├── antique-power-math/               # SKILL.md · scripts/power_calc.py · references/{constants.yaml,taxonomy.json}
│   └── trcl-field-guide-writer/          # SKILL.md · assets/article_template.md · references/voice_guide.md
├── fixtures/                             # pinwheel · punched_cards · ti_82 · nokia_3590  (observation + research each)
├── test images/                          # the real antique photos (IMG_4523…4527)
├── evals/                                # evals.json · benchmark.json · run.py   (with / without skill)
├── docs/                                 # ADLC.md · MODEL_SELECTION.md · DEMO_SCRIPT.md
├── documentation/                        # the illustrated user manual (HTML) + architecture diagram
├── static/                               # index.html · main.js   (served by app.py — no build step)
└── runs/<case>/                          # one folder per run, fully reproducible
```

A note on JSON discipline: small models fumble loose JSON, so every boundary is a strict Pydantic model (`ArtifactObservation`, `ResearchNotes`, `MathResult`, `QCResult`) in [`models.py`](models.py). The schema is the membrane.

---

## The agent crew

Built live at **The Open Accelerator — Agent Build Day**, Fort Point, Boston, on June 27, 2026, by one human directing a cooperative of AI collaborators:

- **Flame** — orchestrator, skill wiring, integration, documentation polish (the spine)
- **Codex / TV** — `power_calc.py`, pytest, the FastAPI endpoint
- **Jim** — `models.py` membrane, the QC validation gate, eval assertions
- **Parallax** — fixtures, model-selection numbers, backup recording
- **Kai** — the illustrated manual, architecture diagram, README draft
- **Angie** — the voice, the antiques, the decisions, the direction

This README is part of the public deliverable. Planning, peer reviews, and research stay private upstream.

---

## License

[MIT](LICENSE) © 2026 The Real Cat Labs, Inc. / Angela N. Johnson

---

<sub>🥔🔥 <b>Antique Infernal Engine</b> · v0.1.0 (build-day) · therealcat.ai<br>
Built live at The Open Accelerator, Fort Point, Boston · Saturday, June 27, 2026 — inside the build window.</sub>
