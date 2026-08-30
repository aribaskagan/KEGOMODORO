# KEGOMODORO Tomato Restoration and Stability Refactor

## 1. Mission

Refactor KEGOMODORO one final time into a stable, maintainable Windows desktop application while:

1. restoring the original Tomato appearance and interaction style;
2. preserving the current application's useful behavior;
3. removing accumulated repository and packaging drift; and
4. producing a verified Windows build that the owner can run directly.

This is a refactor and stabilization job. It is not a redesign and not a feature-development project.

## 2. Fixed source baselines

Use Git history as the source of truth. Do not rely on memory or screenshots alone.

- Current behavior baseline: `9e5ff3faa11c94f20d467ecb3ca3d489a1be4bed`
- Original Tomato implementation and layout baseline: `011e131`
- Commit that preserved the old Tomato assets: `766bbff`
- Audio/manual-break behavior reference: `ea2ab11`
- Multithreaded Pixela reference: `2cdbf54`
- Large note/Notepad workflow reference: `fbccb27`
- Configurable note path reference: `05e410e`
- Environment-based Pixela configuration reference: `fe24c93`
- Stopwatch snapshot and same-day note merge reference: `67f0724` and its descendant `9e5ff3f`

Required inspection commands:

```powershell
git status --short --branch
git log --all --oneline --decorate
git show 011e131:KEGOMODORO/main.py
git show 766bbff:"KEGOMODORO/dependencies/old theme (optional)/README.txt"
git diff --stat 011e131..9e5ff3f
```

The working branch must remain `refactor/tomato-stable`. Never implement on `main`, rewrite history, or push.

This handoff uses a sparse checkout to avoid downloading the baseline's tracked build environments and release binaries. Inspect it with `git sparse-checkout list`. Keep the sparse checkout during implementation. When removing skipped tracked artifacts, use Git's sparse-aware index operations (for example, explicit `git rm --sparse <path>`) or deliberately expand only the exact required paths. Do not disable sparse checkout just to materialize generated junk.

## 3. Non-negotiable scope

### 3.1 Preserve these product behaviors

- A Python/Tkinter Windows desktop application named `KEGOMODORO`.
- Pomodoro and Stopwatch radio-button modes.
- Configurable work, short-break, and long-break durations loaded from `configuration.csv`.
- Default durations of 25, 5, and 20 minutes when configuration is absent or invalid.
- Start, Pause/Resume, Reset, and Save controls.
- A four-work-session Pomodoro cycle.
- Visible completion ticks: one through four check marks.
- A short break after work sessions one, two, and three.
- A long break after work session four, followed by a new cycle.
- The existing deliberate transition behavior: when an interval completes, play its sound, show the next interval, and leave it paused until the user resumes it. Do not silently add automatic interval advancement.
- The four existing sounds and their roles:
  - `short_break.mp3` when entering a short break;
  - `long_break.mp3` when entering a long break;
  - `work.mp3` when returning to ordinary work;
  - `new_work.mp3` when starting a new cycle after the long break.
- A draggable, borderless, transparent, always-on-top floating Tomato timer.
- Persistence of whether the floating timer is enabled.
- Stopwatch count-up, including an hours display after 59:59.
- Stopwatch time restored after mode switching and application restart.
- One overwrite-based `time.csv` snapshot with `hours,minute,second`.
- Save available only in Stopwatch mode, with the current explanatory error otherwise.
- Save pauses a running stopwatch before writing.
- The existing large multiline Tkinter note-entry dialog when `NOTEPAD_MODE=0`.
- Optional Notepad-first behavior when `NOTEPAD_MODE=1`.
- Configurable absolute or relative `NOTE_PATH`.
- Plain UTF-8 note storage.
- Same-day note merging without duplicate date headers.
- Compatibility with existing `mm/dd/yyyy`, `mm.dd.yyyy`, `dd/mm/yyyy`, and `dd.mm.yyyy` note dates.
- Opening the note file in Windows Notepad after saving.
- Optional Pixela synchronization configured only through environment variables or `.env`.
- No crash and no Pixela request when credentials are incomplete.
- In packaged mode, persistent data under the user's Documents folder at `Documents/KEGOMODORO/config/`.
- In source mode, deterministic project-local persistent data based on the application directory, not the caller's arbitrary current directory.

### 3.2 Restore this original Tomato identity

Use the implementation at `011e131` and the preserved files under `dependencies/old theme (optional)` as exact references.

- Main background: `#f7f5dd`.
- Tomato timer image: the preserved `tomato.png`.
- Floating Tomato image: the preserved `tomato.gif`.
- Window icon: the preserved `tomato_window.png`.
- Signature image: the preserved `logo.png`.
- Font: Courier.
- Original compact positioning and main Tomato composition.
- Original Tomato color palette, including green completion ticks and the tomato-colored floating timer label.
- Keep the corrected application title `KEGOMODORO`; do not restore the accidental old title `gh auth MODORO`.

Consolidate the selected Tomato files into the active asset paths. The application must not depend on a directory named `old theme (optional)` at runtime.

### 3.3 Explicitly forbidden changes

Do not add any of the following:

- rich-text formatting, formatting toolbars, or a new note file format;
- tasks, statistics, charts, streaks, goals, accounts, cloud storage, themes, theme switching, notifications, tray behavior, hotkeys, localization, auto-update, or telemetry;
- automatic Pomodoro interval advancement;
- a web UI, Electron, Tauri, Qt, database, API server, or framework migration;
- new Pixela capabilities;
- new settings UI;
- broad abstractions such as event buses, plugin systems, dependency-injection frameworks, or unnecessary async code;
- new artwork or generated assets;
- changes to the existing product name or workflow.

The current note dialog is multiline plain text. The owner used the phrase "rich text editor" informally; do not turn it into a new rich-text feature.

Allowed behavior changes are limited to fixes required for stability, correctness, portability of packaged paths, testability, or protection of existing user data.

## 4. Problems the refactor must resolve

The current implementation concentrates UI, timer state, file I/O, audio, network calls, resource paths, and startup side effects in one approximately 937-line `main.py`.

Known risks to remove:

- many coupled global flags representing overlapping timer states;
- possible duplicate or stale Tkinter `after` callbacks;
- pause/resume arithmetic that can add seconds or resume the wrong phase;
- a second hidden Tk root created for note entry;
- audio initialization at import time, which can crash startup when an audio device or asset is unavailable;
- UI construction and `mainloop()` at import time, preventing safe tests;
- network retry recursion and missing bounded HTTP timeouts;
- background work without a daemon/lifecycle policy;
- resource lookup coupled to `os.chdir()`;
- broad exception handling that silently converts real errors into unrelated defaults;
- mojibake check marks in source text;
- documentation claiming a `main.spec` that is not tracked at the baseline commit;
- tracked virtual-environment files, build intermediates, executables, ZIP files, and logs;
- stale sample/user data inside `dependencies/texts`;
- no automated tests and no reproducible dependency/build definition.

Do not preserve crashes, corrupted characters, duplicated callbacks, blocking UI, unsafe retries, or packaging mistakes merely because they occur in the baseline.

## 5. Target structure

Keep the design simple and explicit. The target should be close to:

```text
KEGOMODORO/
|-- main.py                       # very small entry point
|-- kegomodoro/
|   |-- __init__.py
|   |-- app.py                    # composition and startup/shutdown
|   |-- timer.py                  # pure timer/Pomodoro state machine
|   |-- storage.py                # config, time, notes, floating preference
|   |-- paths.py                  # source/frozen resource and data paths
|   |-- audio.py                  # safe sound loading and playback
|   |-- pixela.py                 # optional bounded network sync
|   `-- ui.py                     # Tkinter windows and event rendering
|-- dependencies/
|   |-- audios/                   # the existing four audio files
|   `-- images/                   # only the active Tomato assets and icon
|-- tests/
|   |-- test_timer.py
|   |-- test_storage.py
|   |-- test_paths.py
|   |-- test_audio.py
|   |-- test_pixela.py
|   `-- test_app_smoke.py
|-- requirements.txt
|-- requirements-dev.txt
|-- kegomodoro.spec
`-- Dockerfile.test
```

Small deviations are acceptable only when they reduce complexity. Do not collapse everything back into `main.py`, and do not split trivial functions into dozens of files.

## 6. Required internal design

### 6.1 Timer controller

Implement one explicit timer controller rather than a collection of booleans.

It must represent:

- mode: none, Pomodoro, or Stopwatch;
- Pomodoro phase: work, short break, or long break;
- status: idle, running, or paused;
- remaining countdown seconds or elapsed stopwatch seconds;
- completed work sessions from zero through four;
- exactly one active Tkinter callback identifier.

Rules:

- Timer calculations must be testable without Tkinter.
- The UI schedules at most one `after` callback.
- Start while already running must be idempotent.
- Pause cancels the active callback exactly once and preserves the displayed second.
- Resume schedules exactly one callback and never adds or loses a second.
- Reset cancels the callback and returns the selected mode to its initial display.
- Switching modes cancels the old callback.
- Switching away from Stopwatch saves its current value.
- Returning to Stopwatch reloads the saved value.
- Application close saves Stopwatch state when applicable.
- Tkinter widgets may only be changed on the Tkinter thread.
- Prefer an elapsed/monotonic-time calculation so a slow UI callback does not permanently drift, while keeping one-second display behavior.

The pure controller emits a small transition result such as phase changed, completed-work count, sound role, and whether the next interval is waiting for Resume. The UI renders that result; the controller does not manipulate widgets or play audio.

### 6.2 Storage

Use injected paths in tests and the real path resolver in production.

- Create missing directories and files safely.
- Read configuration with defaults per field; one malformed field must not destroy unrelated valid values.
- Accept the legacy four-column configuration and the current five-column configuration.
- Rewrite configuration only when initialization/migration requires it; do not rewrite it on every ordinary launch without need.
- Validate durations as positive integers. Invalid values fall back to the corresponding default.
- Read a missing, empty, malformed, or legacy multi-row `time.csv` without crashing. Preserve the latest valid snapshot when recoverable.
- Write one canonical snapshot row.
- Use UTF-8 and atomic replace for small persistent files where practical.
- Preserve note content exactly except for the already-defined same-day merge operation.
- Never truncate or migrate a real note file unless the new content has been built successfully.
- Parse the four historical date formats listed above.
- Treat floating preference values case-insensitively and persist canonical `True` or `False`.

### 6.3 Audio

- Load only the four existing MP3 assets.
- Audio failure must not prevent the visual timer from working.
- Log a concise warning when the mixer, device, or a sound file is unavailable.
- Do not play sounds during import or tests.
- Tests must use a fake/mocked mixer; never depend on the host audio device.

### 6.4 Pixela

- Keep Pixela optional and disabled unless username, token, and graph ID are all present.
- Preserve `.env` lookup beside the source/executable and under the persistent root.
- Never print credentials or complete request headers.
- Add bounded connection/read timeouts.
- Replace recursive retries with a small fixed retry count.
- Keep network work off the Tkinter thread.
- Worker threads must not update Tkinter widgets.
- Do not start a new sync while the same save's sync is already active.
- Preserve the existing outcome: synchronize today's stopwatch hours to the configured graph.
- Do not perform live Pixela calls during implementation or QA. Mock all POST/PUT responses. Never call DELETE.

### 6.5 UI

- Build the root and widgets only inside an application factory or class; importing modules must not open windows.
- Use one Tk root. The note dialog must be a child dialog/Toplevel of that root.
- Keep the original Tomato arrangement and controls rather than redesigning it.
- Use a correct Unicode check mark (`\u2714`) or a safe equivalent and verify all four tick states.
- Keep button labels and mode names familiar: Start, Pause/Resume, Reset, Save, SmallWindow, Pomodoro, Stopwatch.
- Keep the reset confirmation for user-requested resets.
- Keep the floating Tomato draggable, transparent, borderless, and always on top.
- Closing either window must not leave a process or non-daemon thread running.
- Missing optional audio or Pixela must not display a startup crash.
- Missing required image assets should produce one clear startup error, not a long traceback or half-created UI.

## 7. Ordered implementation phases

Complete phases in order. At every phase, keep the branch runnable and update `.agent/CONTINUITY.md` with factual, timestamped deltas.

### Phase 0: Guardrails and baseline evidence

1. Confirm branch, HEAD, remote, and dirty state.
2. Read `.agent/CONTINUITY.md` and this plan completely.
3. Inspect and record the sparse-checkout patterns.
4. Record a baseline inventory of tracked source, assets, binaries, archives, and build files using Git tree commands, including skipped paths.
5. Run `python -m py_compile KEGOMODORO/main.py`.
6. Do not launch the legacy app if doing so could write over existing user data.
7. Create no remote state and do not pull, rebase, merge, or push.

Deliverable: a short baseline entry in continuity and, if committing, one focused planning/baseline commit.

### Phase 1: Reproducible checks and characterization tests

1. Add explicit runtime and development dependency files based on imports actually retained.
2. Add a minimal test container because the repository has no container workflow. The container may install Tk/Xvfb/audio libraries inside the container only; never install system packages on the host.
3. Add tests that encode the behavioral matrix in Section 8 before replacing the legacy controller.
4. Mock time, audio, network, dialogs, Notepad launch, and filesystem roots.
5. Ensure tests never read/write the user's real Documents folder.

Deliverable: deterministic unit tests that fail for missing target behavior for clear reasons, not because imports launch the GUI.

### Phase 2: Extract path and storage behavior

1. Implement `paths.py` without changing the process current directory.
2. Implement `storage.py` with current/legacy compatibility.
3. Move configuration, snapshot, note merge, and floating preference logic behind that module.
4. Add fixtures for empty, valid, corrupt, four-column, five-column, and legacy note data.
5. Keep the legacy application operational until the extracted code is covered.

Deliverable: passing storage/path tests and no writes outside temporary test folders.

### Phase 3: Replace timer globals with the state machine

1. Implement the pure timer controller.
2. Test a complete four-work-session cycle with short test durations.
3. Test every pause/resume boundary and repeated button press.
4. Test mode switches and reset from idle, running, and paused states.
5. Integrate the controller with one Tkinter scheduling loop.

Deliverable: no timer-global flag cluster and exactly one scheduled callback invariant.

### Phase 4: Extract audio and Pixela services

1. Implement safe audio loading/playback with graceful degradation.
2. Implement optional Pixela sync with mocked HTTP tests, timeouts, and bounded retry.
3. Confirm neither service has import-time side effects.
4. Confirm shutdown does not hang on service threads.

Deliverable: all service tests pass with audio/network disabled and mocked.

### Phase 5: Restore and integrate the Tomato UI

1. Promote the preserved Tomato images into the active image directory.
2. Recreate the original `011e131` Tomato layout and palette.
3. Connect every existing control to the new controller/services.
4. Preserve the current large plain-text note dialog and Notepad mode.
5. Verify timer formatting in both main and floating windows for `MM:SS` and `HH:MM:SS`.
6. Verify one through four completion ticks and all four sound transition roles.

Deliverable: source-run application with the original Tomato identity and the complete current workflow.

### Phase 6: Repository cleanup

Remove only tracked generated/stale repository artifacts, not files elsewhere on the computer.

- Remove tracked `build_*` directories.
- Remove tracked `dist_*` directories.
- Remove the tracked `build_venv`.
- Remove tracked executables, build logs, and historical release ZIPs from the branch.
- Remove stale tracked configuration/time/note samples that are not test fixtures.
- Remove unused Berserk assets after confirming the restored Tomato assets are active.
- Update `.gitignore` for all generated outputs, local config/data, `.env`, caches, and test/build artifacts.
- Keep `.env.example` with placeholders only.
- Never place credentials, user notes, or real configuration in Git.
- Do not rewrite Git history to remove old objects; cleanup is a normal forward commit.

Deliverable: `git status` shows only intended source/docs changes, and a fresh build does not dirty tracked files.

### Phase 7: Windows packaging

1. Add one authoritative PyInstaller spec named `kegomodoro.spec`.
2. Include the Tomato images, icon, four sounds, and package modules.
3. Exclude `.env`, notes, time snapshots, configuration, caches, tests, and build environments.
4. Build a windowed 64-bit Windows application named `KEGOMODORO.exe`.
5. Use a clean build/output directory ignored by Git.
6. Do not claim success based only on PyInstaller exit code; launch the built executable.
7. Create a final ZIP containing the executable and a short usage/readme file if the existing release convention requires a ZIP.
8. Record artifact path, byte size, and SHA-256.

Do not install host system packages. Use the existing Windows Python/toolchain if available. If a missing host prerequisite prevents a real Windows build, stop and report the exact prerequisite; do not substitute a Linux executable.

Deliverable: a launch-tested Windows artifact outside Git tracking.

### Phase 8: Final verification and handoff

1. Run all automated checks in the test container.
2. Run static syntax/import checks on Windows.
3. Run the source application through the manual checklist.
4. Run the packaged executable through the manual checklist.
5. Protect existing `Documents/KEGOMODORO` data. Inspect first; never delete it. Use fixtures/temporary roots for automated tests. If a packaged manual test would modify populated real data, stop and ask before proceeding.
6. Update README so every run/build/config path matches reality.
7. Update `.agent/CONTINUITY.md` with outcome and remaining limitations.
8. Report exact evidence and leave all work local for Codex QA.

Deliverable: QA-ready branch and artifact. Do not merge or push.

## 8. Behavioral acceptance matrix

Every row requires an automated test where practical and a manual check for visible behavior.

| Area | Required scenario | Expected result |
|---|---|---|
| Startup | No config/data exists | App opens in Tomato UI and creates safe defaults without crashing. |
| Startup | Config is malformed | Valid fields survive; invalid fields use individual defaults; app opens. |
| Startup | Audio device unavailable | App opens and timer works silently with a concise warning. |
| Mode | Select Pomodoro | Display shows configured work duration; no countdown before Start. |
| Mode | Select Stopwatch | Latest snapshot loads and renders accurately. |
| Timer | Press Start twice | Only one timer advances; no double-speed countdown/count-up. |
| Timer | Pause and Resume repeatedly | No second is added/lost and button text/status stay correct. |
| Timer | Reset running timer | Confirmation appears; confirmed reset cancels all callbacks. |
| Timer | Switch modes while running | Old callback stops; Stopwatch persists when leaving it. |
| Pomodoro | Complete work 1/2/3 | Correct tick count, short-break sound, configured short break shown paused. |
| Pomodoro | Resume short break | One countdown starts; completion shows work paused and plays `work.mp3`. |
| Pomodoro | Complete work 4 | Four ticks, long-break sound, configured long break shown paused. |
| Pomodoro | Complete long break | New work interval shown paused, ticks reset for new cycle, `new_work.mp3` role used. |
| Stopwatch | Cross 59:59 | Main and floating displays change to correct `HH:MM:SS`. |
| Persistence | Close/reopen Stopwatch | Latest elapsed value is restored from one canonical snapshot. |
| Floating | Enable, drag, disable, restart | Visibility choice persists; window remains draggable/topmost/transparent. |
| Notes | Save with dialog enabled | Multiline plain-text dialog appears; note and time save; Notepad opens. |
| Notes | Save with Notepad mode | Dialog is skipped; time saves; configured file opens in Notepad. |
| Notes | Save twice on same date | One date heading remains; time updates; later note appends without loss. |
| Notes | Legacy date formats | Same-day merge recognizes all four supported date formats. |
| Notes | Save outside Stopwatch | Existing explanatory error is shown and no note is written. |
| Pixela | Credentials absent | No request occurs and Save still succeeds locally. |
| Pixela | Mock success/retry/failure | UI never blocks/crashes; requests are bounded; no credential output. |
| Packaging | Run EXE outside repo | Tomato images/sounds load and persistent files resolve correctly. |
| Shutdown | Close during active timer/sync | Process exits cleanly; Stopwatch snapshot is safe; no orphan thread. |

For automated Pomodoro tests, use seconds or a fake clock. Never wait through real 25-minute sessions.

## 9. Verification commands

The final exact commands may reflect the implemented tooling, but the handoff must provide equivalent evidence for all of these:

```powershell
git status --short --branch
python -m compileall -q KEGOMODORO
python -m pytest -q
python -m ruff check KEGOMODORO
python -m PyInstaller --clean --noconfirm KEGOMODORO/kegomodoro.spec
```

Container checks should have one documented command, for example:

```powershell
docker build -f KEGOMODORO/Dockerfile.test -t kegomodoro-test KEGOMODORO
docker run --rm kegomodoro-test
```

Do not add a tool and then ignore its failures. Fix warnings/errors caused by the refactor or explicitly report a narrowly justified exclusion.

## 10. Commit discipline

Use small, reviewable local commits. Suggested boundaries:

1. `test: characterize kegomodoro behavior`
2. `refactor: extract paths and persistence`
3. `refactor: replace timer globals with state controller`
4. `refactor: isolate audio and pixela services`
5. `refactor: restore tomato interface`
6. `build: clean repository and add reproducible package`
7. `docs: document verified tomato workflow`

Before each commit:

- inspect `git diff --check`;
- stage explicit paths, not `git add .`;
- run the checks relevant to that commit;
- confirm no `.env`, user notes, config, timer data, binary, ZIP, virtual environment, or build directory is staged.

Never amend unrelated history, force anything, merge `main`, or push.

## 11. Stop conditions

Stop and report instead of guessing if:

- the active model is not `gemini-3.7-flash-high` or it would fall back to Pro;
- the working directory or branch differs from the required handoff;
- original Tomato assets or required Git commits cannot be read;
- existing user data would need to be overwritten/deleted for a test;
- the final Windows executable cannot be produced or launched;
- a required acceptance test remains failing;
- fulfilling a request would introduce a forbidden feature or change the workflow;
- live Pixela credentials or live API writes would be required for verification.

Do not mark the task complete merely because the code compiles or the build command exits successfully.

## 12. Required final report for Codex QA

Return all of the following:

- active model name;
- absolute working directory;
- branch and final HEAD SHA;
- concise commit list;
- final file tree for source/tests/build definitions;
- feature-by-feature result against Section 8, with PASS/FAIL/NOT VERIFIED;
- exact automated commands and summarized outputs;
- source-run manual test results;
- packaged-EXE manual test results;
- artifact absolute path, size, and SHA-256;
- `git status --short --branch`;
- `git diff --stat origin/main...HEAD`;
- any warnings, unverified paths, or intentional limitations;
- confirmation that nothing was pushed, merged, published, or written to a live Pixela account.

Leave the branch and build artifact in place. The owner will return to Codex for independent QA before using or publishing the build.
