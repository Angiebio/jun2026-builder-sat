---
name: antique-power-math
description: "Compute whether an antique or object could power or run AI inference. Use when given an artifact plus a proposed mechanism or power source and a rigorous deterministic AI-equivalence calculation is needed: power path in watts, compute path in operations per second, potato equivalent, cyclist equivalent, and AI Hello timing."
---

# antique-power-math

Use this skill to produce frozen math for the Antique Infernal Engine article. The model may classify the artifact path and extract assumptions; `scripts/power_calc.py` performs the arithmetic.

Constants live in `references/constants.yaml`. Taxonomy lives in `references/taxonomy.json`.

## Defaults

Choose exactly one taxonomy path from `references/taxonomy.json`.

- Use a power path when the artifact produces usable watts.
- Use a compute path when the artifact performs operations over time.
- Use `decorative_or_unknown` only when no defensible power or compute assumption exists.
- Prefer a conservative explicit assumption over a confident invented value.
- Treat "AI Hello" as a playful demo target, not a formal benchmark.

## Workflow

1. Classify the artifact into one taxonomy path.
2. Extract one numeric input:
   - power path: watts per artifact
   - compute path: operations per second
3. If the value is negative for a calculable path, fail loudly and request a better assumption.
4. If the value is exactly zero for a calculable path, preserve the result as sentinel `-1.0` so downstream JSON stays standard and the writer can render "Never" or "Infinite."
5. Run the deterministic calculator:

```bash
python skills/antique-power-math/scripts/power_calc.py <path> <value>
```

6. Return the calculator JSON without changing the numbers.
7. Send the frozen math JSON to QC and the writer. The writer must not recalculate.

## Gotchas

- Watts are power; joules are energy.
- "Powers AI" is not the same as "runs AI."
- Cranks provide input power; gears perform mechanical computation.
- Passive storage, including punched cards, stores information but does not compute unless a reader/computer assumption is supplied.
- For zero compute or zero power, the calculator returns `-1.0` in the relevant output fields instead of JSON `Infinity`.
- Battery-powered calculators and phones are compute artifacts even when their batteries also have wattage.
- `silicon_microprocessor_compute` covers real build-day fixtures such as TI-82 and Nokia candybar phones.
- Never hide uncertainty around estimated ops/sec or watts.

## Output Template

Return the frozen calculator JSON:

```json
{
  "path": "mechanical_decimal_compute",
  "mode": "compute",
  "input_value": 1.0,
  "input_unit": "ops_per_second",
  "units_for_ai_hello": 0.0,
  "potatoes_equivalent": 0.0,
  "cyclists_equivalent": 0.0,
  "time_seconds": 14000000000.0,
  "time_years": 443.6332294,
  "can_evaluate": true,
  "calculation_log": []
}
```

## Edge cases — never refuse (the book's spirit)
This skill assesses **any object** — antique or not — and **never refuses**. When the thing in
front of it neither produces power nor computes (a rubber duck, a houseplant, a USB stick, a
person), the engine finds an **absurd-but-real energy angle** and runs the *same* exact math.

**The division of labor holds — the model never multiplies:**
- The model estimates **one number**: the object's **mass in grams** (rubber duck ≈ 35 g,
  brick ≈ 2000 g). If the object is alive, a **metabolic wattage** (~100 W for a human) instead.
- **Python does the combustion**, deterministically: `watts = mass_g × 30000 J/g ÷ 60 s`
  (~30 kJ/g of chemical energy released over ~60 s). A 35 g duck → **17,500 W**.
- Those watts run the **same power-path math**: `units_for_ai_hello = 30 / W` ·
  `potatoes = W / 0.0001` · `cyclists = W / 100`. The duck → **175,000,000 potatoes** (and 175 cyclists).
- Output `mode` = **`absurd_power`**, `input_unit` = `"watts (absurd angle)"`, and the
  `calculation_log` names the angle (*"combustion of ~35 g over ~60 s (~30 kJ/g)"*).

**Fallbacks (still never refuse):** a direct watts / metabolic / joule estimate is used as-is;
if the model offers nothing, assume a palm-sized **~100 g** object burned over a minute.

**The writer owns the tone, not the number** (`trcl-field-guide-writer`): *"This is not an
antique. The calculator has spoken anyway."* → *"Yes — if you're prepared to commit arson on a
bath toy."* The joke is the writer's; the 17,500 W is Python's.

*(The novel-object path runs on `--live`, where a model proposes the mass; the combustion and
equivalence math are deterministic Python in every profile.)*
