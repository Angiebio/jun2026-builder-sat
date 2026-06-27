# 🥔🔥 Antique Infernal Engine

> Upload a photo of an antique. Get a TRCL field-guide page that computes, with real physics, whether it could power or run AI.

**The humor is decorative. The math is structural.**

[![License: MIT](https://img.shields.io/badge/License-MIT-4a0873.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-5bb545.svg)](https://www.python.org/)
[![Local-first](https://img.shields.io/badge/runs-fully%20local-5bb545.svg)](#quickstart)
[![Models: Claude + Granite](https://img.shields.io/badge/models-Claude%20%2B%20Granite-f5841f.svg)](#model-selection--the-gate)
[![Lane 3](https://img.shields.io/badge/lane-3%20·%20multi--agent%20%2B%20skills-e8e52a.svg)](#how-it-works)

A multi-agent system from [therealcat.ai](https://therealcat.ai) that answers the least efficient question in history: *could this antique run AI?* It is Angie's book *100 Ways to Power AI* turned into a working agent — five cooperating sub-agents, two skills, three models, and an adjudication loop that argues with itself until the numbers hold up.

The answer is always yes. The interesting part is the math you have to survive to get there.

---

## Contents

- [What it does](#what-it-does)
- [How it works](#how-it-works)
- [Quickstart](#quickstart)
- [Usage](#usage)
- [Project structure](#project-structure)
- [The two skills](#the-two-skills)
- [Model selection — the gate](#model-selection--the-gate)
- [Evals](#evals)
- [The agent crew](#the-agent-crew)
- [License](#license)

---

## What it does

Hand it a photo of an antique — a pinwheel calculator, a voltaic pile, a Jacquard punch card — and it produces a single **field-guide page**:

- **Identifies** the artifact and its real mechanism
- **Classifies** whether it sits on a *power-producing* path (can it generate watts?) or a *compute* path (can it actually run operations?)
- **Calculates**, with frozen deterministic math, how many units it would take to power one "AI hello," plus the equivalent in **potatoes** and in **pedaling cyclists**
- **Writes** it all up in the TRCL field-guide voice: absurd but numerate, every joke sitting on a real number

Every page is reproducible. The prose model never touches arithmetic — it receives frozen math and is only then allowed to be funny.

---

## How it works

This is **not** a linear chain. The **Reality Badger** verifies the math and, on failure, returns a `route_to` telling the orchestrator which earlier agent is at fault. The orchestrator **adjudicates and re-dispatches** — back to the Artifact Goblin to *re-look* at the photo, or to Sherlock Ohms to *re-research* the mechanism — bounded by `MAX_LOOPS`. That feedback loop is what makes this a cooperating multi-agent system instead of a pipeline, and it is fully visible in `trace.json`.

![Architecture: the adjudication loop](docs/architecture.svg)

```python
# orchestrator.py — planner + 5 sub-agents with a bounded adjudication loop
MAX_LOOPS = 2  # the Badger can kick work back; the orchestrator never loops forever

def run_infernal_engine(image_path, run_id):
    obs      = artifact_goblin(image_path)          # vision   → observation.json
    research = sherlock_ohms(obs)                    # research → research.json
    for attempt in range(MAX_LOOPS):
        math = potato_accountant(obs, research)      # skill + power_calc.py → math.json (FROZEN)
        qc   = reality_badger(math, research, obs)   # → {"pass": bool, "reason": str, "route_to": str|None}
        if qc["pass"]:
            break
        # ⟲ adjudication: re-dispatch to the agent the Badger blames, with the reason as a hint
        if   qc["route_to"] == "artifact_goblin": obs      = artifact_goblin(image_path, hint=qc["reason"])
        elif qc["route_to"] == "sherlock_ohms":   research = sherlock_ohms(obs, hint=qc["reason"])
    article = page_goblin(math, qc)                  # writer skill → article.json (frozen math only)
    write_trace(run_id, attempts=attempt + 1)        # the loop is VISIBLE in trace.json
    return article
```

**The five agents**

| Agent | Job | Runs on |
|---|---|---|
| 🔎 Artifact Goblin | Sees the photo, separates *visible* from *inferred*, guesses the path | Claude (vision) |
| 🧪 Sherlock Ohms | Researches the real mechanism and its numbers | fixture / search |
| 🥔 Potato Accountant | Classifies the path, calls the deterministic calculator | granite4:micro + Python |
| 🦡 Reality Badger | Verifies units and claims, returns `route_to` on failure | granite4:micro |
| 📝 Page Goblin | Writes the field-guide page from frozen math | Claude (prose) |

The Badger fails a run when confidence is too low, watts and joules get confused, *"powers AI"* is overclaimed as *"runs AI,"* or the potato/cyclist math is inconsistent.

---

## Quickstart

**Runs fully local with zero keys** (Granite via [Ollama](https://ollama.com)). Frontier vision and prose are optional add-ons.

```bash
# 1. clone
git clone https://github.com/Angiebio/jun2026-builder-sat
cd jun2026-builder-sat

# 2. install
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. pull the local model
ollama pull granite4:micro

# 4. run on a bundled fixture — zero network required
python agent.py run --fixture fixtures/pinwheel.jpg
```

That's it. You'll get a field-guide page in `runs/<id>/article.md` and the full decision trail in `runs/<id>/trace.json`.

**Optional — turn on frontier features** (live vision on your own photos, sharper prose):

```bash
cp .env.example .env        # then add your keys
# ANTHROPIC_API_KEY=...      ($50 attendee credits at the event)
```

---

## Usage

```bash
# Run on one of the bundled fixtures (fully local, deterministic)
python agent.py run --fixture fixtures/voltaic.jpg

# Run on your own antique photo (uses frontier vision if ANTHROPIC_API_KEY is set)
python agent.py run --image ~/photos/mystery-gadget.jpg

# Serve the single-page web UI at http://localhost:8000
python agent.py serve

# Run the eval suite (with and without skills) → benchmark.json
python agent.py eval

# Compare against the no-skill baseline
python agent.py eval --no-skill
```

Every run writes a self-contained folder:

```
runs/<id>/
├── input.jpg          observation.json     research.json
├── math.json          qc.json              article.json / article.md
└── trace.json         ← model, latency, tokens, pass/fail, loop count
```

Open `trace.json` to watch the Badger reject a first pass and send it back to re-classify. That trail is the demo.

---

## Project structure

```
jun2026-builder-sat/
├── README.md  LICENSE                    # MIT
├── agent.py                              # CLI + upload + serve
├── orchestrator.py                       # planner + adjudication loop
├── agents/
│   ├── goblin.py  ohms.py  accountant.py  badger.py  page.py
├── models.py                             # Pydantic membrane — strict types at every boundary
├── skills/
│   ├── antique-power-math/               # SKILL.md  scripts/power_calc.py  references/{constants.yaml,taxonomy.json}
│   └── trcl-field-guide-writer/          # SKILL.md  assets/article_template.md  references/voice_guide.md
├── fixtures/                             # 3 demo antiques: photo + observation.json + research.json each
├── evals/   evals.json  benchmark.json
├── docs/    ADLC.md  MODEL_SELECTION.md  DEMO_SCRIPT.md  architecture.svg
├── static/  index.html  main.js          # single page served by FastAPI (not a build step)
└── runs/<id>/                            # one folder per run, fully reproducible
```

A small note on JSON discipline: small models fumble loose JSON, so every boundary is a strict Pydantic model (`ArtifactObservation`, `ResearchNotes`, `MathResult`) that **auto-retries once with the validation error fed back as context**. The schema is the membrane.

---

## The two skills

### `antique-power-math`

The deterministic, judge-friendly skill. The LLM proposes physical assumptions; **Python does the arithmetic.** Constants are frozen:

```yaml
# references/constants.yaml
ai_hello_watts: 30          # power to run one "AI hello"
potato_watts:   0.0001      # a potato battery
cyclist_watts:  100         # one human pedaling
ai_hello_ops:   14000000000 # operations behind one hello
```

```
power-producing artifact:  units_for_ai_hello = 30 / watts_per_unit
                           potatoes_per_unit  = watts_per_unit / 0.0001
                           cyclists_per_unit  = watts_per_unit / 100
```

Guard: any `value <= 0` raises and **fails loud** — no silent zero, no fabricated unit. Outputs are rounded once, at the end.

### `trcl-field-guide-writer`

Enforces the field-guide voice and a fixed article schema: *Title · Subtitle · Era Badge · Artifact Guess · Confidence · What it actually did · How we bully it into powering AI · **Can it Run AI?** · With what · Output · Unit · Watts/Compute · **Math** · Potato Equivalent · Cyclist Equivalent · Historical note · Gotcha · Illustration prompt.*

Voice: absurd but numerate, every joke on a real mechanism, never hide uncertainty, one memorable line per page. **The writer receives frozen math and never does arithmetic.**

---

## Model selection — the gate

> **Granite classifies and verifies; frontier sees and writes; Python calculates.**

A small local model is the **discipline membrane** inside a frontier creative system.

| Task | Model | Why |
|---|---|---|
| Photo vision | **Claude** | accuracy on antique photos; a small local model can't see |
| Taxonomy classify | **granite4:micro** (local) | cheap, fast, constrained JSON |
| Math assumptions | **granite4:micro + Python** | the model structures; the script does exact arithmetic |
| QC / Reality Badger | **granite4:micro** (local) | a local model as judge and verifier — the strong claim |
| Final prose | **Claude** | voice and comedic precision |
| Illustration prompt | **Claude + fal.ai** | brand image pipeline |

Full cost / latency / quality rationale lives in [`docs/MODEL_SELECTION.md`](docs/MODEL_SELECTION.md). Per-run receipts (model, latency, tokens, pass/fail) are logged in every `trace.json`.

---

## Evals

Three cases in `evals/evals.json`, each run **with and without** the skill:

| Fixture | Path | What it must get right |
|---|---|---|
| Pinwheel calculator | `mechanical_decimal_compute` | time from ops/sec; uncertainty on ops/sec |
| Voltaic pile | `galvanic_dc` | watts per unit; units for 30 W; mentions current limits |
| Jacquard punch card | `punched_card_parallel_binary` | distinguishes programmability from general AI compute |

Assertions are **script-checked, not LLM-judged**: the article contains *"Can it Run AI?"*, includes watts or ops/sec, includes the potato and cyclist equivalents, the math JSON exactly matches the calculator output, QC passes, Granite appears in the trace for classify and QC, and at least two skills loaded.

> Without the math skill, the prose model hallucinated units. With it, the calculator matched **3/3**.

A skill that can't beat its `--no-skill` baseline isn't earning its place — so we measure it.

---

## The agent crew

Built live at **TOA Agent Build Day**, Fort Point, Boston, on June 27, 2026, by one human directing a cooperative of AI collaborators:

- **Flame** — orchestrator, skill wiring, integration (the spine)
- **Codex / TV** — `power_calc.py`, pytest, FastAPI endpoint
- **Jim** — `models.py` membrane, QC validation gate, eval assertions
- **Parallax** — fixtures, model-selection numbers, backup recording
- **Kai** — README, documentation, architecture diagram
- **Angie** — the voice, antique selection, decisions, direction

This README is part of the public deliverable. Planning, peer reviews, and research stay private upstream.

---

## License

[MIT](LICENSE) © 2026 The Real Cat Labs, Inc. / Angela N. Johnson

---

<sub>🥔🔥 <b>Antique Infernal Engine</b> · v0.1.0 (build-day) · therealcat.ai<br>
Authored Saturday, June 27, 2026 · 11:24 AM EDT — live, inside the 5-hour build window.</sub>
