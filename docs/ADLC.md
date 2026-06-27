# ADLC Worksheet — Antique Infernal Engine
*One page per phase. Filled during the build; graded (20 pts).*

> **Two honest profiles.** **FLOOR** (default): deterministic, **model-free for
> correctness**, runs offline with zero keys — this is the thesis, not a gap. **`--live`**
> (ENHANCE): `granite4:micro` classifies + QCs, Claude sees + writes, with real model
> receipts in `trace.json`. The floor *guarantees* the answer; `--live` adds senses and voice.

## 1. Scope
**Problem:** given a photo of an antique, answer — with real physics, not vibes — whether
it could power or run AI inference, as a TRCL "Can it Run AI?" field-guide page.
**User:** build-day judges + readers of *100 Ways to Power Artificial Intelligence*.
**In:** one artifact; deterministic power/compute math; a one-page article + a
machine-readable trace. **Out:** marketplace/appraisal, multi-photo, training, and any use
where the number is allowed to be "about right" instead of exact.

## 2. Design
Five function-agents + an orchestrator running a **bounded adjudication loop**
(`MAX_LOOPS=2`): `artifact_goblin` (vision) -> `sherlock_ohms` (research) ->
[`potato_accountant` (skill + `power_calc.py`) -> `reality_badger` (QC)] re-loop ->
`page_goblin` (writer). File-backed JSON in `runs/<id>/`. Two skills: `antique-power-math`
(deterministic) + `trcl-field-guide-writer` (voice + template). Model placement is
**profile-aware**: the **FLOOR runs the loop deterministically (fixtures + Python math),
with no model in the correctness path**; **`--live` overlays `granite4:micro` on
classify+QC and Claude on vision+prose** (see [MODEL_SELECTION.md](MODEL_SELECTION.md)).

## 3. Build (floor-first)
Order, each tier independently demoable: (1) `power_calc.py` + pytest + constants/taxonomy
— the deterministic core. (2) `models.py` Pydantic membrane — strict types at every
boundary. (3) orchestrator + 5 agents on fixtures -> file-backed JSON + `trace.json`.
(4) two skills authored + `skills-ref validate`. (5) evals + docs. (6) ENHANCE (`--live`):
granite classify+QC, Claude vision+prose, FastAPI UI. **Rule:** nothing in ENHANCE breaks
the deterministic floor; the primary demo runs from fixtures, zero network.

## 4. Evaluate  ← the money phase
- **v1 — model guesses the physics.** Ask `granite4:micro` alone "how long would a TI-82
  take to run an AI inference?" It invents ops/sec and watts, and the answer drifts
  run-to-run. Not reproducible, not defensible. *(baseline numbers: `evals/benchmark.json`, TV.)*
- **v2 — physics moved into `scripts/power_calc.py`.** The model only proposes the
  taxonomy path + one input (ops/sec or watts); the script does the arithmetic.
  Verified-exact and reproducible (live calculator output):
  | Case | input | result |
  |---|---|---|
  | pinwheel | 1 ops/s | 14,000,000,000 s = **443.6332294 yr** |
  | TI-82 | 600,000 ops/s | **23,333.3333 s** (~6.5 h) |
  | punched cards | 0 ops/s | **-1.0 sentinel** ("never computes") |
  Each carries a `calculation_log` (the receipts): *"AI Hello target: 14000000000.0
  operations. Time required: 14000000000.0 / 600000.0 seconds."*
- **Result:** with-skill `math_exact` = **3/3** (calculator matches the pinned numbers
  exactly); no-skill granite-alone = `[X]/3` (`benchmark.json`). **This is the FLOOR
  headline and it needs no frontier model** — the skill doesn't make the prose nicer, it
  makes the math *true*, deterministically. The skill-vs-baseline delta is the proof the
  thesis is real, not merely asserted.

## 5. Deploy
The **FLOOR** runs from the README, local-first, **zero keys** (`granite4:micro` is only
used on `--live`; the floor itself needs no model). `skills-ref validate` passes on both
skills. Public repo + MIT. **`--live`** is opt-in via `.env` — never required for the floor demo.

## 6. Observe
`trace.json` records the loop on every run. **On the FLOOR profile it honestly logs
`model: deterministic` / `fixture`** — there is no model in the correctness path, by
design. What is real and visible on the floor: the loop control (`loops`, `passed`,
`route_to`) and the **skills loaded per step** (`antique-power-math` on the accountant,
`trcl-field-guide-writer` on the page goblin). Representative floor run: `loops=1,
passed=true` — the Badger passed the math first try, no re-dispatch; when it fails,
`route_to` names the blamed agent (`artifact_goblin`/`sherlock_ohms`) and the loop re-runs
with the reason as a hint, **bounded at 2** so it can never spin. **Under `--live`, the
same steps carry real model receipts** — `granite4:micro` on classify+QC, Claude on
vision+prose, each with model/latency/tokens — landing with the ENHANCE wiring (Flame1). We
do **not** print "granite" on a FLOOR trace; that would be a lie the eval is built to reject.

## 7. Iterate
A concrete fix driven by an observation: the punched-card case (0 ops/sec) originally hit
`power_calc`'s strictly-positive guard and **raised** — which would have crashed the demo
on artifact #1. Observation (Jim's QC note + a live run) -> fix: 0-ops on a compute path
now returns the **`-1.0` sentinel** + `can_evaluate=false` + an explanatory log, which the
writer renders as **"Never (∞)."** The edge case became the most quotable verdict in the
deck — no division-by-zero, and standards-clean JSON (no non-standard `Infinity` token).
