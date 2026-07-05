# KEGOMODORO

KEGOMODORO is a desktop Pomodoro and Stopwatch app built with Python and Tkinter. The current version focuses on a simple local workflow: track time, save notes, keep a floating mini-timer on screen, and optionally sync worked hours to Pixela.

The active application source lives in [`KEGOMODORO/main.py`](KEGOMODORO/main.py). This repository root contains project docs; the runnable app and packaged builds are inside the [`KEGOMODORO/`](KEGOMODORO) folder.

## Tomato and Berserk Theme
<img width="1054" height="845" alt="image" src="https://github.com/user-attachments/assets/d5cf77ef-9922-46b3-abce-520b97e4ad30" />

## Current Features

- Pomodoro mode and Stopwatch mode in one desktop app.
- Floating mini-window timer that can stay visible while you work.
- Journal saving from Stopwatch mode.
- Same-day note merging: repeated saves on the same date update the time line and append new notes under the same day instead of creating duplicate headers.
- Configurable note workflow through `configuration.csv`.
- Optional Notepad-based workflow with a custom note file path.
- Optional Pixela sync loaded from `.env` instead of hardcoded credentials.
- Persistent user data for packaged builds under the user's Documents folder.

## Repository Layout

```text
kegomodoro/
|- README.md
|- KEGOMODORO/
|  |- main.py
|  |- main.spec
|  |- .env.example
|  |- dependencies/
|  `- dist_*/ build_* outputs
```

## Running From Source

1. Clone the repository and open a terminal in the repo root:

```bash
git clone git@github.com:aribaskagan/KEGOMODORO.git
cd KEGOMODORO/KEGOMODORO
```

2. Install the runtime dependencies:

```bash
pip install pillow requests pygame pyautogui keyboard
```

Notes:
- `tkinter` ships with most standard Windows Python installs.
- The app is Windows-oriented and uses Notepad and Windows Documents paths in packaged mode.

3. Start the app:

```bash
python main.py
```

## Packaged Build Behavior

When you run the packaged `.exe`, KEGOMODORO stores persistent user files in your Documents folder:

```text
Documents/KEGOMODORO/config/
```

Typical files in that folder:
- `configuration.csv`
- `time.csv`
- `notes.txt`
- `floating_window_checker.txt`

This means your data survives app updates and does not need to live beside the `.exe`.

## Notes and Save Flow

The `Save` button is intended for Stopwatch mode.

Current save behavior:
- The current stopwatch time is written to `time.csv` as a single clean snapshot.
- Notes are stored in a text file, not scattered across many duplicate daily entries.
- If you save multiple notes on the same day, KEGOMODORO keeps one date section and appends later notes underneath it.
- Older journal files that used `dd/mm/yyyy` date headers are still recognized and merged correctly.
- After saving, the note file opens in Notepad.

## configuration.csv

The app writes and maintains this header automatically:

```csv
WORK_MIN,SHORT_BREAK_MIN,LONG_BREAK_MIN,NOTEPAD_MODE,NOTE_PATH
```

What each field does:
- `WORK_MIN`: Pomodoro work session length in minutes.
- `SHORT_BREAK_MIN`: Short break length in minutes.
- `LONG_BREAK_MIN`: Long break length in minutes.
- `NOTEPAD_MODE`: `1` to skip the in-app note prompt, `0` to keep it.
- `NOTE_PATH`: Absolute or relative path to the note file you want to use.

Example:

```csv
WORK_MIN,SHORT_BREAK_MIN,LONG_BREAK_MIN,NOTEPAD_MODE,NOTE_PATH
25,5,20,1,C:\Users\YourName\Documents\MyJournal\kegomodoro_notes.txt
```

If `NOTE_PATH` is empty, the app falls back to the default note file in the config folder.

## Pixela Setup

Pixela is optional. If the required environment variables are missing, the app simply skips Pixela sync.

1. From the app folder, copy the template:

```bash
cp .env.example .env
```

2. Fill in your values in `.env`:

```env
PIXELA_ENDPOINT=https://pixe.la/v1/users
PIXELA_USERNAME=your_pixela_username
PIXELA_TOKEN=your_pixela_token
PIXELA_GRAPH_ID=your_graph_id
```

The app looks for `.env` in these locations:
- next to the app (`KEGOMODORO/.env` in source mode, or next to the `.exe` in packaged mode)
- `Documents/KEGOMODORO/.env`

## Building

The project includes a PyInstaller spec file at [`KEGOMODORO/main.spec`](KEGOMODORO/main.spec).

From the app folder:

```bash
python -m PyInstaller --noconfirm main.spec
```

That will build a Windows executable using the bundled `dependencies/` assets.

## Troubleshooting

### Save button does nothing useful
- Make sure you are in Stopwatch mode. The save flow is tied to Stopwatch logging.

### Pixela is not updating
- Check that your `.env` values are correct.
- Confirm that `PIXELA_USERNAME`, `PIXELA_TOKEN`, and `PIXELA_GRAPH_ID` are all set.

### I want to open my own journal file
- Set `NOTE_PATH` in `configuration.csv` to your existing text file.
- Set `NOTEPAD_MODE=1` if you want a fully Notepad-first flow.

## Contributing

If you want to contribute, please open an issue or send a pull request. The main implementation is currently concentrated in [`KEGOMODORO/main.py`](KEGOMODORO/main.py), so most behavior changes will start there.

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE) for details.
