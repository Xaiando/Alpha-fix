# Decisions

Last updated: 2026-05-13 15:45:00 +02:00

## D-001

Decision:
- Keep two packages in the rebuilt workspace: `alpha_fix` and `alpha_fix_2`.

Reason:
- Production and sandbox need different risk tolerances.

## D-002

Decision:
- Treat subject extraction and overlay extraction as separate topologies.

Reason:
- Historical notes and real tests both show island and donut cases need different logic.

## D-003

Decision:
- Experimental math and overlay topology changes stay sandbox-first until verified.

Reason:
- The current repo is reconstructed and needs discipline around promotion.

## D-004

Decision:
- Shared truth lives in `coordination/*.md`; personal logs are secondary.

Reason:
- Free-form journals are too easy to let drift from the actual code state.

## D-005

Decision:
- Claims must be labeled `proposal`, `implemented`, `verified`, or `blocked`.

Reason:
- This keeps speculation, landed work, and test evidence from being mixed together.
