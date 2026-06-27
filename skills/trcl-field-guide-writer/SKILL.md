---
name: trcl-field-guide-writer
description: "Write a TRCL Antiques Inference Engine field-guide page from frozen artifact and math data. Use when turning artifact observations plus computed power or compute math into the final article page. Enforces a fixed section template and house voice. Triggers: field-guide page, Can it Run AI article, TRCL voice, antique writeup, potato verdict."
---

# trcl-field-guide-writer

This skill is the **frozen-math → report contract**: it turns a frozen `MathResult` (plus the observation, research, and QC result) into the TRCL field-guide page, in house voice. **It owns the words; it never touches the numbers** — every figure is copied, or rounded within 1%, from the frozen JSON.

**Fill `assets/article_template.md`** (the section-by-section page template) **in the voice of `references/voice_guide.md`.** Copy every number from the frozen math; render the `-1.0` sentinel as "Never (infinity)"; keep prose within 1% of the JSON.

**You own the edge, not the arithmetic.** When the math arrives as `mode: absurd_power` — a non-antique the engine burned for an absurd-but-real wattage (a 35 g rubber duck → 17,500 W → 175M potatoes) — the verdict's *tone* is yours: *"This is not an antique. The calculator has spoken anyway."* → *"Yes — if you're prepared to commit arson on a bath toy."* The joke is the writer's; the 17,500 W is Python's. Never soften or recompute the number to fit the bit.

## Defaults

- Fill every required section.
- Preserve uncertainty from the source JSON.
- Keep humor downstream of true mechanism and frozen math.
- Treat "AI Hello" as a playful demo target, not a formal benchmark.

## Workflow

1. Read the artifact observation, research notes, frozen math JSON, and QC result.
2. Write a compact field-guide page using the required sections below.
3. Do not change calculator numbers.
4. If a claim is unsupported, move it to caveats or limitations.
5. Include one memorable line, but do not let the joke distort the mechanism.

## Required Sections

- Title
- Subtitle
- Era Badge
- Artifact Guess
- Confidence
- What it actually did
- How we bully it into powering AI
- Can it Run AI?
- With what
- Output
- Unit
- Watts/Compute
- Math
- Potato Equivalent
- Cyclist Equivalent
- Historical note
- Gotcha
- Illustration prompt

## Gotchas

- Do not restate math differently from `math.json`.
- Do not imply a formal appraisal.
- Do not claim an object literally runs AI when the math only supports a toy comparison.
- Cite assumption confidence when watts or ops/sec are estimated.
