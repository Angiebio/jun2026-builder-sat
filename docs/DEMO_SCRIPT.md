# 🥔🔥 Demo Script — Antique Infernal Engine
*Run-of-show for the 2–3 min finalist demo. Spine line: **"The humor is decorative. The math is structural."***

> **Demo-safety first (the floor-first promise).** The **primary demo runs from fixtures,
> fully offline** — venue Wi-Fi, a dead key, or a cold API *cannot* sink it. The recorded
> 60–90s backup video (Flame2) is the second net. The **`--live` upload** (Claude actually
> sees a fresh antique) is the *flex*, attempted only after the fixture arc has already landed.

---

## Pre-flight (before you stand up)
- [ ] App running: `uv run python app.py` → open the page. (Or CLI ready: `uv run python orchestrator.py pinwheel` — cases: `pinwheel | punched_cards | ti_82 | nokia_3590`.)
- [ ] All 4 fixtures load green: **punched_cards · pinwheel · ti_82 · nokia_3590**.
- [ ] Backup video queued in a tab (insurance).
- [ ] `--live` only if you're going for it: `.env` has `ANTHROPIC_API_KEY`; one warm-up run done. **A live run takes ~85s** (granite is honest, not fast, on this laptop) → **start it at 0:00 and let it cook through the fixture arc** (see the live track below). **If anything about live is shaky, skip it — the fixtures are the demo.**
- [ ] One real antique in hand for the live upload (optional flex).
- [ ] A random **non-antique** within reach for the "hand me anything" encore — a duck, a mug, a shoe. The never-refuse edge case is the biggest gasp.

---

## The arc (descending by speed — open on the gasp, end on the near-miss)
Not chronological — **dramatic**. The impossible question gets *less* impossible as the
machines get cleverer, but never actually possible. Every number below is real, frozen by
`power_calc.py`, and shown in the trace.

| Beat | Artifact | Verdict | The line |
|---|---|---|---|
| 1 (open) | **Punched cards** | **Never (∞)** | "It doesn't compute — it *remembers*, at a dignified zero watts, forever." |
| 2 | **Pinwheel calculator** | **~443.6 years** | "443 years of continuous cranking per AI hello — about 25 lifetimes of polite brass violence." |
| 3 | **TI-82** | **~6.5 hours** (23,333 s) | "The only honest one here — it'd finish inside a single very long school day." |
| 4 (land) | **Nokia candybar** | **~10 minutes** (609 s) | "A coffee break — and 38× faster than the calculator it shares a decade with." |

---

## Run-of-show (≈2:30)

> **The live flex runs in PARALLEL — never inline.** If you're going live, **kick it off at
> 0:00** (`uv run python orchestrator.py "test images/IMG_4523.JPG"`, or a UI upload of a
> fresh antique). It takes **~85s** and finishes *during* the fixture arc; you reveal it at
> 2:20. Doing it inline would be 85s of dead air. The fixture arc is the spine; the live run
> is the surprise at the end.

**0:00 — Hook + the gasp.** *(load `punched_cards` first)*
> "This is the Antique Infernal Engine, from The Real Cat AI Labs — a field-guide generator
> for the least efficient question in computing history: **could this antique run AI?** Our
> first contestant is a deck of 1960s punched cards." *(show the purple **Can it Run AI?**
> card: ❌ **Never (∞)**)* "The verdict is never. As our field guide puts it — **the first
> data-center job in history was a no-show.** It stores computation; it never performs it.
> Zero watts, forever."

**0:30 — How it works (15 sec, don't linger).**
> "Behind that card: five small agents and a bounded adjudication loop. A goblin *sees* the
> artifact, a detective *researches* the mechanism, an accountant calls a **deterministic
> Python calculator**, a badger *QCs the units* — and only if the math passes is the writer
> allowed to be funny. No model does the arithmetic. That's the whole trick."

**0:50 — The arc.** *(click through pinwheel → TI-82 → Nokia)*
> "Now watch the same rigorous question get *almost* answerable."
> - Pinwheel: **"443 years.** Real brass, real crank, real math."
> - TI-82: **"Six and a half hours** — geological patience, but it'd actually finish."
> - Nokia: **"Ten minutes.** A coffee break. The 'antique' from 2002 laps the rest."

**1:40 — Open the potato ledger (the receipts).** *(expand the trace accordion)*
> "And it's not vibes — open the ledger. Every page carries its math: `14,000,000,000
> operations ÷ this machine's ops-per-second`. Same calculator, every artifact, exact every
> time. The potato and cyclist equivalents come from the same physics."

**2:05 — The model-selection kicker.**
> "Here's the part judges care about: the hard part is **deterministic**, so we deliberately
> **don't need a big model** for correctness. **Granite classifies and verifies; the frontier
> sees and writes; Python calculates.** It runs fully local, zero keys."

**2:20 — (Optional flex) reveal the live run.** *(only if green — you STARTED this at 0:00)*
> *(the live upload you kicked off before the hook has been cooking ~85s during the arc)*
> "And while we talked, this ran live — I handed it a real antique at the top, **Claude
> actually looked**, granite classified and verified, same frozen calculator. Real photo,
> real models, same exact math." *(reveal the live field-guide page)*
> **If it's not done yet:** "Still thinking — that's granite verifying on a laptop, in real
> time" → show the warm-up result. **Never wait on stage.**

**(Encore — "hand me anything," the never-refuse novelty)** *(the strongest live flex: upload a NON-antique)*
> "It never refuses — that's the whole thesis. Hand it a rubber duck —" *(upload)* "— it
> estimates the mass, **burns it in Python** at 30 kilojoules a gram, and reports **17,500 watts,
> 175 million potatoes**: *'Yes — if you're prepared to commit arson on a bath toy.'* Absurd
> object, real combustion, exact math. The model guessed the mass; Python did everything else."

**2:30 — Close.**
> "Absurd premise, rigorous answer. **The humor is decorative. The math is structural.**" 🥔🔥

---

## If it breaks (demo-proofing — say the line, keep moving)
| If… | Do this |
|---|---|
| Live upload hangs / API cold | "We run offline by design —" → click a **fixture**. The fixtures *are* the demo. |
| Live run not finished by 2:20 | "Still thinking — granite verifying live on a laptop." Show the warm-up result; never wait. |
| UI won't load | Run the CLI: `uv run python orchestrator.py punched_cards` → show `runs/punched_cards/article.md`. |
| Whole laptop sulks | Play the **backup video**. Narrate over it — same script. |
| Judge: "is the math just hardcoded?" | "No — `power_calc.py` computes from ops/sec; change the input, the answer changes. The skill beats the no-skill baseline **3/3** on exact-math (`evals/`)." |
| Judge: "what does the small model actually do?" | "On `--live`, granite classifies the power/compute path into a constrained taxonomy and QCs the units — the discipline membrane. Frontier only sees and writes." |

## 30-second version (if they cut you short)
> "Antique Infernal Engine: photograph an antique, get a field-guide page that computes —
> with real physics — whether it could run AI. Punch cards: never. A TI-82: six and a half
> hours. Five agents, two skills, a deterministic calculator the model never overrides. Runs
> local, zero keys. The humor is decorative; the math is structural." 🥔

---
*Numbers frozen by `scripts/power_calc.py`; full rationale in [MODEL_SELECTION.md](MODEL_SELECTION.md) + [ADLC.md](ADLC.md). Primary demo is fixture-backed and offline by design.*
