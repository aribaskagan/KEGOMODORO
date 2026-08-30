You are implementing a strictly bounded stability refactor of KEGOMODORO. Work in this exact directory:

`C:\Users\ariba\OneDrive\Documenti\Software Projects\AI Projects\kegomodoro-stopwatch`

Model requirement: use `gemini-3.7-flash-high` for the master and for every worker/subagent, if any. Do not use or fall back to any Pro model. If Flash High is unavailable, stop and report that; do not begin implementation.

Before changing anything:

1. Print and verify the absolute working directory.
2. Verify the active branch is `refactor/tomato-stable` and HEAD descends from `9e5ff3faa11c94f20d467ecb3ca3d489a1be4bed`.
3. Inspect `git sparse-checkout list`. This checkout intentionally omits tracked build/dist/venv/ZIP junk; keep it sparse and use sparse-aware Git removal as described in the plan.
4. Read the repository instructions available to you, `.agent/CONTINUITY.md`, and `REFACTOR_EXECUTION_PLAN.md` completely.
5. Inspect the historical commits and files named in the plan, especially `011e131`, `766bbff`, and current `KEGOMODORO/main.py`.
6. Record the baseline state before editing.

Then execute `REFACTOR_EXECUTION_PLAN.md` phase by phase until the complete acceptance matrix is satisfied and a real Windows build is produced. This is implementation work, not another planning exercise.

Critical product boundary:

- Restore the original Tomato UI and assets.
- Preserve the current Pomodoro, four ticks, four sounds, manual interval transitions, Stopwatch, persistence, multiline plain-text note dialog, optional Notepad workflow, same-day note merging, floating timer, configuration, packaged paths, and optional Pixela behavior.
- Do not invent features. In particular, do not add rich-text formatting, tasks, statistics, themes, tray features, notifications, hotkeys, accounts, new integrations, or automatic interval advancement.
- Refactor and stabilize only. Fix crashes, timer callback/state bugs, unsafe persistence, blocking/unbounded network behavior, resource-path problems, and packaging problems without changing the intended workflow.

Execution constraints:

- Keep work on `refactor/tomato-stable`.
- Never modify or merge `main`; never pull, rebase, push, or publish.
- Never use live Pixela credentials or make live API writes. Mock network tests.
- Never print or request secrets.
- Never delete or overwrite existing user data under Documents. Inspect it before any packaged manual test.
- Do not install system packages on the host. Use the test container for dependencies/checks; use only an already-available Windows toolchain for the final Windows build.
- Use small local commits and stage explicit paths.
- Maintain `.agent/CONTINUITY.md` with short factual timestamped entries after meaningful deltas.
- Do not report completion while any required test, manual flow, or packaged launch is failing or unverified.

When finished, leave the branch, source, tests, and artifact in place and return the exact final report required by Section 12 of `REFACTOR_EXECUTION_PLAN.md`. The next step will be independent Codex QA, so include evidence rather than assurances.
