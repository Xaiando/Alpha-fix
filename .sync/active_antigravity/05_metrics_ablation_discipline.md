# Metrics And Ablation Discipline

**Claim:** `active`
**Owner:** Antigravity
**Scope:** `sandbox_only_alpha_fix_2`
**Component:** `tests/`, `test_runs/`, future metrics helpers

**Context:**
`SDR-Pow` and `OSA-v2` now exist in the sandbox, but we do not yet have a stable pass table that decides whether a new method is actually better on real assets.

**Task:**
Create a repeatable sandbox comparison workflow:
1. define a fixed asset set
2. record mean alpha, center-hole score, frame-band opacity, chatter, and jitter where applicable
3. require the same metric table for every new branch math pass

**Why it matters:**
This prevents descriptive hype from outrunning measured results.
