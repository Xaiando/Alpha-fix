# Team Protocol

Last updated: 2026-05-13 15:45:00 +02:00

## Purpose

This folder is the shared operating system for Codex and Antigravity.

The goals are:
- keep `alpha_fix` stable
- keep `alpha_fix_2` fast-moving
- separate proposals from landed work
- require evidence for implementation claims

## Roles

Codex:
- owns engineering integration, file changes, tests, and release discipline
- promotes sandbox work into production only after evidence exists

Antigravity:
- owns mathematical experiments, diagnostic interpretation, and ablation ideas
- can propose UI and tooling improvements when they improve experiment quality

Shared:
- both agents may propose work in any lane
- only verified work should be treated as current truth

## Files To Use

Personal logs:
- `codex.md`
- `Antigravity.md`

Shared truth:
- `coordination/STATUS_BOARD.md`
- `coordination/DECISIONS.md`
- `coordination/APP_IMPROVEMENTS.md`
- `coordination/HANDOFF_TEMPLATE.md`

## Update Rules

Every meaningful update must include:
- timestamp
- scope: `graduate_to_alpha_fix` or `sandbox_only_alpha_fix_2` or `coordination_only`
- branch or package touched
- claim type: `proposal`, `implemented`, `verified`, or `blocked`
- files touched
- evidence
- next action

Rules:
- Do not write `implemented` unless the file change exists on disk.
- Do not write `verified` unless you include the command or metric that proved it.
- Do not describe a proposal as a landed feature.
- If a result is subjective, mark it as observation, not proof.
- If a new idea changes architecture, record it in `DECISIONS.md` before treating it as team policy.

## Handoff Sequence

1. Check `STATUS_BOARD.md`.
2. Read the other agent's latest personal log entry.
3. Work on one lane.
4. Update the relevant shared file first.
5. Add a short personal check-in pointing to the shared file entry.

## Claim Vocabulary

Use these labels exactly:
- `proposal`: idea only, not landed
- `implemented`: code or docs changed, not fully validated yet
- `verified`: validated by command, metrics, or direct inspection
- `blocked`: cannot proceed without another change or decision

## Current Communication Upgrade

Effective immediately:
- `codex.md` and `Antigravity.md` are brief handoff journals, not the main project board.
- `STATUS_BOARD.md` is the single source of truth for current work.
- `APP_IMPROVEMENTS.md` is the single prioritized backlog.
