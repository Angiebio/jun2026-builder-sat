# 🥔🔥 Antiques Inference Engine — Concept Brief

> Upload a photo of an antique and get a TRCL field-guide page that works out, with **real physics**, whether the thing could power or run AI.
>
> **The humor is decorative. The math is structural.**

**Team:** The Real Cat AI Labs · **Lane 3** (most innovative use of multiple agents and skills) · The Open Accelerator, Agent Build Day, Fort Point, Boston, 27 June 2026
**Repo:** <https://github.com/Angiebio/jun2026-builder-sat> · **License:** MIT · **Runs fully local, zero keys**

---

## The concept

The **Antiques Inference Engine** asks the least efficient question in history, *could this antique run AI?*, and then it actually does the math. Hand it a photo and five agents work together to write one field-guide page. They work out what the object is, whether it can **make power** (watts) or **do compute** (operations over time), and how many **potato batteries**, or centuries, it would take to reach one *"AI hello."* It's Angie's book *100 Ways to Power Artificial Intelligence*, built into a working agent.

Think of it as *Antiques Roadshow* for the AI age. Same dramatic appraisal of some dusty heirloom, except instead of "what's it worth?" the expert squints and asks "could it run a neural network?"

The verdict is rarely the point. The point is the math you have to survive to get there.

![Architecture, the adjudication loop](../documentation/orchestration-overview.png)

## What makes it Lane 3

It isn't a pipeline, it's a cooperating system with a bounded loop.

- **Five agents.** Artifact Goblin (sees), Sherlock Ohms (researches), Potato Accountant (classifies and calls the calculator), **Reality Badger** (verifies), Page Goblin (writes).
- **The delegation mechanism.** The Reality Badger doesn't just pass or fail. It returns a `route_to` that names which earlier agent is at fault, and the orchestrator hands the work back, re-look or re-research, with the reason attached, bounded at `MAX_LOOPS = 2`. The whole loop shows up in `trace.json`.
- **Two custom [Agent Skills](https://agentskills.io).** `antique-power-math` (the deterministic physics) and `trcl-field-guide-writer` (voice and template). Both pass `agentskills validate`.

## Why the skills are the point (Skills Day)

Today the skill itself is what gets graded, so here's what makes these two worth grading.

Most skills add a capability. Ours add discipline. They don't make the model do more, they make a small, cheap, local model trustworthy.

- **`antique-power-math` is a correctness skill, not a feature skill.** It tells the model to stop doing arithmetic and hand the numbers to `scripts/power_calc.py`. The model only picks a category and one input value. The deterministic work lives in code, where it's right every time. That's exactly the build-day pattern, deterministic work belongs in a script, never in the model. And the payoff is measurable. **24 of 24 assertions pass with the skill, 0 of 4 without it.** A skill that can't beat its own no-skill baseline can't earn full marks, so we measured it.
- **`trcl-field-guide-writer` is a constraint skill.** It owns the voice and a fixed output template, and it's explicitly forbidden from touching the math. It receives the frozen numbers and only narrates them. One skill computes, the other writes, and neither does the other's job. That separation is what keeps a funny page honest.

Both keep `SKILL.md` small with the heavy material pushed into `references/` and `scripts/`, both carry trigger-rich descriptions (what they do and when to use them), and both run unchanged on a 3B local model and on a frontier model. They also run in any agentskills.io client, including Claude Code, not just this app. The skills are the membrane that turns a cheap local model into a reliable one, and that's the whole reason it works.

## Model selection (the gate)

**Granite classifies and verifies, the frontier models see and write, and Python does the calculating, in both profiles.**

The hard part, the physics, is deterministic, so the default **FLOOR** profile uses no model in the correctness path at all. That's the thesis, not a gap. We can prove the free, local, offline path carries the math, and we pay for a model only where it earns its keep, the seeing and the writing, on an opt-in `--live` profile (Claude vision and prose, `granite4:micro` classify and QC, with real receipts logged in `trace.json`).

## The proof

Measured over all four fixtures, with the math skill against a real `granite4:micro`-only baseline.

| | passed |
|---|---|
| **with `antique-power-math`** | **24 / 24** |
| no-skill (granite guesses the math) | **0 / 4** |
| **delta** | **+24** |

The skills don't make the writing prettier, they make the math true. Granite on its own confuses seconds with years. The deterministic calculator is exact and reproducible.

**Punched cards, never. Pinwheel calculator, 443 years. TI-82, 6.5 hours. Nokia 3590, 10 minutes.** The hardware gets younger and the verdict gets faster, same question, same physics, every time.

## Why it matters, digital literacy in a potato

<img src="../static/book-hero.png" alt="100 Ways to Power Artificial Intelligence, by Angela N. Johnson, PhD" width="300" align="right">

Most people never get to see the **material** reality of AI. One "hello" is 14 billion operations. Power and compute and access are physical, finite, and political. Putting a model's appetite in terms of **potato batteries** and **pedaling cyclists** makes all of that click for anyone, with no machine-learning background needed. The silliness is the way in, and the digital literacy is what you leave with.

> "It's a Trojan Horse for Digital Literacy." *Gemini (Google), reviewing the book*

> "Power, compute, infrastructure, and access are all political and material. The distance between absurdity and viability is much smaller than industry mythology wants people to think." *ChatGPT (OpenAI)*

## Run it

```bash
uv sync
uv run python orchestrator.py pinwheel     # fully local, zero keys, writes runs/pinwheel/article.md
uv run python app.py                        # the single-page field guide at http://127.0.0.1:8000
```

**More:** [README](../README.md) · [ADLC](ADLC.md) · [Model selection](MODEL_SELECTION.md) · [Demo script](DEMO_SCRIPT.md) · [Illustrated manual](../documentation/antique-infernal-engine-guide.html)

---

<sub>🥔🔥 Antiques Inference Engine · v0.1.0 (build-day) · MIT © 2026 The Real Cat Labs, Inc. / Angela N. Johnson · therealcat.ai</sub>
