# Model Selection Rationale — Antique Infernal Engine
*Mandatory gate (all lanes): which model does which task + cost/latency/quality justification. Fill measured numbers from one smoke run.*

## Principle
The hard part is **deterministic**, so we deliberately don't need a big model for it. Small local model = the discipline/verification membrane; frontier = sight + voice; **Python = exact math.**

## Per-task routing (log receipts in `runs/<id>/trace.json`: model · latency · tokens · pass/fail)
| Task | Model | Why | Latency (measured) | Tokens | $ |
|---|---|---|---|---|---|
| Photo vision | Claude (`ANTHROPIC_API_KEY`) | granite can't see; accuracy on antique photos | _fill_ | _fill_ | _fill_ |
| Taxonomy classify | granite4:micro (local) | cheap, fast, constrained JSON | _fill_ | _fill_ | $0 |
| Math assumptions | granite4:micro + Python | small model structures; script computes | _fill_ | _fill_ | $0 |
| QC (Reality Badger) | granite4:micro (local) | local model as verifier | _fill_ | _fill_ | $0 |
| Final prose | Claude | voice + comedic precision | _fill_ | _fill_ | _fill_ |
| Illustration prompt | Claude + fal.ai | brand image pipeline | _fill_ | _fill_ | _fill_ |

## One-liner
*"Granite classifies and verifies; frontier sees and writes; Python calculates."*

## Hybrid note
Runs fully local (zero keys) for cost/privacy; frontier opt-in for the two tasks that genuinely need it (vision, prose). Document the local-only vs hybrid pass-rate delta if time allows.
