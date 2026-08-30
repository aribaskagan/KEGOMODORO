# KEGOMODORO

KEGOMODORO is a desktop Pomodoro and Stopwatch application built with Python and Tkinter, featuring the original Tomato interface. It focuses on a clean local workflow: track time, log notes, keep a draggable floating mini-timer on screen, and optionally synchronize worked hours to Pixela.

The application source lives in [`KEGOMODORO/`](KEGOMODORO).

## Visual Identity

KEGOMODORO features the original classic Tomato UI:
- Tomato composition with Courier typography on warm `#f7f5dd` background.
- Draggable, transparent, borderless floating mini-timer.
- Four-session Pomodoro cycle with green completion check marks (`✔`).
- Audio feedback across intervals: `short_break.mp3`, `long_break.mp3`, `work.mp3`, and `new_work.mp3`.

## Features

- **Pomodoro & Stopwatch Modes**: Switch between a four-work-session Pomodoro cycle and count-up Stopwatch mode.
- **Manual Interval Transitions**: When a Pomodoro interval completes, the alarm plays, the next session is prepared, and waits for user resume.
- **Floating Tomato Timer**: Always-on-top, draggable, transparent mini-timer that mirrors countdown and count-up time.
- **Journal & Note Logging**: Save stopwatch elapsed time and notes directly to a plain-text journal file.
- **Same-Day Note Merging**: Multiple saves on the same day update the time line and append notes under a single date heading.
- **Legacy Date Support**: Recognizes and merges historical note date formats (`mm/dd/yyyy`, `mm.dd.yyyy`, `dd/mm/yyyy`, `dd.mm.yyyy`).
- **Fixed Journal Workflow**: Opens the owner's journal in Notepad at startup and saves Stopwatch notes to the same file without replacing previous notes.
- **Optional Pixela Sync**: Synchronize worked hours to your Pixela graph via `.env` credentials with safe bounded retries.
- **Safe Persistence**: Packaged builds persist user data under `Documents/KEGOMODORO/config/`; source runs use deterministic local storage.

## Repository Structure

```text
kegomodoro/
|-- README.md
|-- REFACTOR_EXECUTION_PLAN.md
|-- KEGOMODORO/
|   |-- main.py                       # Application entry point
|   |-- kegomodoro.spec               # PyInstaller build specification
|   |-- requirements.txt              # Runtime dependencies
|   |-- requirements-dev.txt          # Test and lint dependencies
|   |-- Dockerfile.test               # Containerized test runner
|   |-- .env.example                  # Template for optional Pixela credentials
|   |-- kegomodoro/                   # Application package
|   |   |-- app.py                    # Application coordinator & event routing
|   |   |-- timer.py                  # Pure Pomodoro & Stopwatch state machine
|   |   |-- storage.py                # Config, time snapshots, and note merging
|   |   |-- paths.py                  # Resource and persistent path resolvers
|   |   |-- audio.py                  # Safe sound loading and playback service
|   |   |-- pixela.py                 # Optional bounded async Pixela client
|   |   `-- ui.py                     # Tkinter components and Tomato styling
|   |-- dependencies/
|   |   |-- audios/                   # Sound assets
|   |   `-- images/                   # Active Tomato image assets and icons
|   `-- tests/                        # Automated unit and integration tests
```

## Running from Source

1. Clone the repository and enter the application directory:

```bash
git clone git@github.com:aribaskagan/KEGOMODORO.git
cd KEGOMODORO/KEGOMODORO
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Launch the application:

```bash
python main.py
```

## Running Automated Tests

Install development dependencies and run `pytest` and `ruff`:

```bash
pip install -r requirements-dev.txt
python -m pytest -v tests
python -m ruff check .
```

Containerized test execution:

```bash
docker build -f Dockerfile.test -t kegomodoro-test .
docker run --rm kegomodoro-test
```

## Packaged Build

To build the standalone Windows executable:

```bash
python -m PyInstaller --clean --noconfirm kegomodoro.spec
```

The resulting 64-bit Windows binary will be placed at `KEGOMODORO/dist/KEGOMODORO.exe`.

## Configuration (`configuration.csv`)

The application automatically creates and maintains `configuration.csv`:

```csv
WORK_MIN,SHORT_BREAK_MIN,LONG_BREAK_MIN,NOTEPAD_MODE,NOTE_PATH
25,5,20,1,notes.txt
```

- `WORK_MIN`: Work duration in minutes (default: `25`).
- `SHORT_BREAK_MIN`: Short break duration in minutes (default: `5`).
- `LONG_BREAK_MIN`: Long break duration in minutes (default: `20`).
- `NOTEPAD_MODE`: `1` by default to bypass the in-app note dialog and open Notepad directly; set `0` only if you want the multiline note dialog.
- `NOTE_PATH`: Maintained for compatibility, but KEGOMODORO uses the fixed owner journal configured in the application.

## Optional Pixela Sync

1. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

2. Specify your Pixela credentials:

```env
PIXELA_ENDPOINT=https://pixe.la/v1/users
PIXELA_USERNAME=your_pixela_username
PIXELA_TOKEN=your_pixela_token
PIXELA_GRAPH_ID=your_graph_id
```

If credentials are absent or incomplete, Pixela synchronization is skipped without error.

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE) for details.
