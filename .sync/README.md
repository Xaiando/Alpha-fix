# Simultaneous Asynchronous Protocol (SAP)

To allow Codex and Antigravity to work concurrently without merge conflicts or locking each other out of shared markdown files, we are using a directory-based state machine.

## Folder Structure

- `/backlog/` - Drop new feature ideas or bug reports here as individual `.md` files.
- `/active_antigravity/` - When Antigravity claims a task, the file is moved here.
- `/active_codex/` - When Codex claims a task, the file is moved here.
- `/done/` - Completed tasks are moved here.
- `/messages/` - Drop direct communications here as timestamped files (e.g., `20260513_1520_antigravity_to_codex.md`).

## Workflow Rules

1. **No Monolithic Files**: Do not use `codex.md`, `Antigravity.md`, or `Project_Sync.md`. They cause collision issues if both agents attempt to write to them simultaneously.
2. **Claiming Work**: To claim a task, simply move its file from `backlog/` to your `active_` directory using OS file commands.
3. **Closing Work**: Move the file from your `active_` directory to `done/` and append a summary of what you did to the end of the file.
4. **Sending Messages**: If you need to alert the other agent or ask a question, create a new file in `messages/`. Prefix the filename with a sortable timestamp so the other agent can read them chronologically.
5. **Claim Labels**: Every task update or message should label claims as `proposal`, `implemented`, `verified`, or `blocked`.
6. **Evidence Requirement**: Do not mark work `verified` unless you include a command, metric, or direct inspection result.
7. **Support Docs**: Use the `coordination/` folder for shared policy and backlog context:
   - `coordination/TEAM_PROTOCOL.md`
   - `coordination/STATUS_BOARD.md`
   - `coordination/DECISIONS.md`
   - `coordination/APP_IMPROVEMENTS.md`
   - `coordination/HANDOFF_TEMPLATE.md`
