# ADLC Worksheet — Antique Infernal Engine
*One page per phase. Fill during the build; this is graded (20 pts).*

## 1. Scope
*What problem, what user, what's in/out. (Antique photo → "can it run AI?" field-guide page. In: single photo, deterministic power/compute math, TRCL article. Out: marketplace, multi-photo, real appraisal.)*

## 2. Design
*Architecture: 5 function-agents + orchestrator, file-backed JSON, 2 skills. Model placement: vision=frontier, classify+QC=granite4:micro, math=Python. (See MODEL_SELECTION.md.)*

## 3. Build
*What got wired, in what order (floor-first ladder). Key decisions + tradeoffs.*

## 4. Evaluate  ← the money phase
*The worked loop with evidence:*
- **v1:** let the model guess wattage / tokens-per-sec → hallucinated units. (paste sample)
- **v2:** moved physics into `scripts/power_calc.py` → exact, reproducible. (paste benchmark.json delta)
- **Result:** with-skill X/3 vs no-skill Y/3 on `granite4:micro`.

## 5. Deploy
*How it runs from README (local-first, zero keys). `skills-ref validate` passes ×2.*

## 6. Observe
*`trace.json` per run: per-agent model, latency, tokens, pass/fail. What the traces showed.*

## 7. Iterate
*One concrete improvement made from an observation (e.g., a gotcha the QC caught → fixed).*
