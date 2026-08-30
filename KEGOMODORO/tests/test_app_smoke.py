"""Smoke and integration tests for KegomodoroApp GUI."""

import tkinter as tk
from unittest.mock import MagicMock, patch
import pytest

from kegomodoro.app import KegomodoroApp
from kegomodoro.audio import SoundService
from kegomodoro.pixela import PixelaClient
from kegomodoro.storage import load_configuration, load_time_snapshot
from kegomodoro.timer import TimerMode, TimerStatus


@pytest.fixture
def tk_root():
    """Create a hidden Tk root for GUI smoke testing."""
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


def test_app_init_and_defaults(tk_root, tmp_path):
    config_file = tmp_path / "config.csv"
    time_file = tmp_path / "time.csv"
    pref_file = tmp_path / "floating.txt"
    note_file = tmp_path / "notes.txt"
    opened_files = []

    audio_mock = MagicMock(spec=SoundService)
    pixela_mock = MagicMock(spec=PixelaClient)
    pixela_mock.is_configured.return_value = False

    app = KegomodoroApp(
        root=tk_root,
        config_path=config_file,
        time_path=time_file,
        pref_path=pref_file,
        audio_service=audio_mock,
        pixela_client=pixela_mock,
        enable_audio=False,
        journal_path=note_file,
        open_notepad_func=opened_files.append,
    )

    assert app.timer.work_min == 25
    assert app.timer.short_break_min == 5
    assert app.timer.long_break_min == 20
    assert app.timer.mode == TimerMode.NONE
    assert config_file.is_file()
    assert load_configuration(config_file, persistent_root=tmp_path).note_path == note_file

    tk_root.update_idletasks()
    assert opened_files == [note_file]


def test_app_mode_selection_and_timer_flow(tk_root, tmp_path):
    config_file = tmp_path / "config.csv"
    time_file = tmp_path / "time.csv"
    pref_file = tmp_path / "floating.txt"

    audio_mock = MagicMock(spec=SoundService)
    pixela_mock = MagicMock(spec=PixelaClient)
    pixela_mock.is_configured.return_value = False

    app = KegomodoroApp(
        root=tk_root,
        config_path=config_file,
        time_path=time_file,
        pref_path=pref_file,
        audio_service=audio_mock,
        pixela_client=pixela_mock,
        enable_audio=False,
        journal_path=tmp_path / "notes.txt",
        open_journal_on_startup=False,
    )

    # 1. Select Pomodoro
    app.on_select_pomodoro()
    assert app.timer.mode == TimerMode.POMODORO
    assert app.timer.status == TimerStatus.IDLE
    assert app.canvas.itemcget(app.timer_text, "text") == "25:00"

    # 2. Start Pomodoro
    app.on_start()
    assert app.timer.status == TimerStatus.RUNNING
    assert app.active_after_id is not None

    # 3. Pause Pomodoro
    app.on_toggle_pause()
    assert app.timer.status == TimerStatus.PAUSED
    assert app.active_after_id is None

    # 4. Resume Pomodoro
    app.on_toggle_pause()
    assert app.timer.status == TimerStatus.RUNNING

    # 5. Reset (without dialog confirmation for test)
    app.on_reset(confirm=False)
    assert app.timer.status == TimerStatus.IDLE
    assert app.canvas.itemcget(app.timer_text, "text") == "25:00"

    # 6. Switch to Stopwatch
    app.on_select_stopwatch()
    assert app.timer.mode == TimerMode.STOPWATCH
    assert app.canvas.itemcget(app.timer_text, "text") == "00:00"


def test_app_save_in_stopwatch(tk_root, tmp_path):
    config_file = tmp_path / "config.csv"
    time_file = tmp_path / "time.csv"
    pref_file = tmp_path / "floating.txt"
    note_file = tmp_path / "notes.txt"

    # Configure notepad mode True to bypass interactive dialog
    config_file.write_text(
        f"WORK_MIN,SHORT_BREAK_MIN,LONG_BREAK_MIN,NOTEPAD_MODE,NOTE_PATH\n25,5,20,1,{note_file}\n",
        encoding="utf-8",
    )

    opened_files = []

    def mock_open_notepad(path):
        opened_files.append(path)

    audio_mock = MagicMock(spec=SoundService)
    pixela_mock = MagicMock(spec=PixelaClient)
    pixela_mock.is_configured.return_value = False

    app = KegomodoroApp(
        root=tk_root,
        config_path=config_file,
        time_path=time_file,
        pref_path=pref_file,
        audio_service=audio_mock,
        pixela_client=pixela_mock,
        open_notepad_func=mock_open_notepad,
        enable_audio=False,
        journal_path=note_file,
        open_journal_on_startup=False,
    )

    app.on_select_stopwatch()
    app.timer.stopwatch_seconds = 125  # 02:05

    app.on_save()

    # Verify time snapshot
    h, m, s = load_time_snapshot(time_file)
    assert (h, m, s) == (0, 2, 5)

    # Verify note file written
    assert note_file.is_file()
    assert "02:05" in note_file.read_text(encoding="utf-8")

    # Verify notepad opened
    assert len(opened_files) == 1


@patch("tkinter.messagebox.showerror")
def test_app_save_outside_stopwatch_shows_error(mock_error, tk_root, tmp_path):
    app = KegomodoroApp(
        root=tk_root,
        config_path=tmp_path / "config.csv",
        time_path=tmp_path / "time.csv",
        pref_path=tmp_path / "floating.txt",
        enable_audio=False,
        journal_path=tmp_path / "notes.txt",
        open_journal_on_startup=False,
    )

    app.on_select_pomodoro()
    app.on_save()

    mock_error.assert_called_once()
