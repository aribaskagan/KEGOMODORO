"""Main application coordinator and GUI for KEGOMODORO."""

import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import Callable, Optional
from PIL import Image, ImageTk

from kegomodoro.audio import SoundService
from kegomodoro.paths import (
    get_persistent_root,
    get_resource_path,
    load_runtime_env,
)
from kegomodoro.pixela import PixelaClient
from kegomodoro.storage import (
    AppConfig,
    format_time_str,
    load_configuration,
    load_floating_preference,
    load_time_snapshot,
    save_configuration,
    save_floating_preference,
    save_time_snapshot,
    append_saved_entry,
)
from kegomodoro.timer import (
    PomodoroPhase,
    SoundRole,
    TimerController,
    TimerMode,
    TimerStatus,
    TimerTransition,
)
from kegomodoro.ui import (
    DEEP_GOLD_COLOR,
    FONT_NAME,
    GREEN,
    MAIN_HOUR_FONT_SIZE,
    MAIN_MINUTE_FONT_SIZE,
    ORANGE,
    RED,
    YELLOW,
    DraggableWindow,
    LargeAskStringDialog,
)

JOURNAL_PATH = Path(r"C:\Users\ariba\OneDrive\Desktop\KAÆ[Æß#.txt")


def default_open_in_notepad(filepath: Path) -> None:
    """Open the note file in Windows Notepad."""
    try:
        subprocess.Popen(["notepad.exe", str(filepath.resolve())])
    except Exception as e:
        print(f"Could not open notepad: {e}")


class KegomodoroApp:
    """Main application lifecycle, window management, and event routing."""

    def __init__(
        self,
        root: Optional[tk.Tk] = None,
        config_path: Optional[Path] = None,
        time_path: Optional[Path] = None,
        pref_path: Optional[Path] = None,
        audio_service: Optional[SoundService] = None,
        pixela_client: Optional[PixelaClient] = None,
        enable_audio: bool = True,
        open_notepad_func: Optional[Callable[[Path], None]] = None,
        journal_path: Optional[Path] = None,
        open_journal_on_startup: bool = True,
    ):
        # Load environment variables
        load_runtime_env()

        self.persistent_root = get_persistent_root()
        self.config_path = (
            config_path or self.persistent_root / "config" / "configuration.csv"
        )
        self.time_path = (
            time_path or self.persistent_root / "config" / "time.csv"
        )
        self.pref_path = (
            pref_path
            or self.persistent_root / "config" / "floating_window_checker.txt"
        )
        self.journal_path = (journal_path or JOURNAL_PATH).resolve()
        self.open_journal_on_startup = open_journal_on_startup

        # Load persisted data
        self.config: AppConfig = load_configuration(
            self.config_path, persistent_root=self.persistent_root
        )
        # The owner's journal is intentionally fixed. Keep existing notes intact;
        # this only creates or updates the small configuration file.
        self.config.note_path = self.journal_path
        save_configuration(
            self.config,
            self.config_path,
            persistent_root=self.persistent_root,
        )
        self.floating_enabled: bool = load_floating_preference(
            self.pref_path, default=False
        )

        # Services
        self.audio = audio_service or SoundService(enable_audio=enable_audio)
        self.pixela = pixela_client or PixelaClient()
        self.open_notepad = open_notepad_func or default_open_in_notepad

        # Timer state machine
        self.timer = TimerController(
            work_min=self.config.work_min,
            short_break_min=self.config.short_break_min,
            long_break_min=self.config.long_break_min,
        )

        # Active Tkinter callback
        self.active_after_id: Optional[str] = None

        # Build UI
        self._owns_root = root is None
        self.root = root or tk.Tk()
        self._build_ui()
        if self.open_journal_on_startup:
            self.root.after_idle(self._open_journal_on_startup)

    def _open_journal_on_startup(self) -> None:
        """Open the fixed journal without changing its existing contents."""
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)
        self.journal_path.touch(exist_ok=True)
        self.open_notepad(self.journal_path)

    def _build_ui(self) -> None:
        self.root.title("KEGOMODORO")
        self.root.config(padx=100, pady=50, bg=YELLOW)
        self.root.resizable(False, False)
        self.root.geometry("+700+300")

        # Window icon
        icon_path = get_resource_path("dependencies/images/tomato_window.png")
        if icon_path.is_file():
            try:
                self.icon_image = ImageTk.PhotoImage(Image.open(str(icon_path)))
                self.root.wm_iconphoto(False, self.icon_image)
            except Exception:
                pass

        # Floating window setup
        floating_gif_path = str(
            get_resource_path("dependencies/images/tomato.gif")
        )
        self.floating_window = DraggableWindow(self.root, floating_gif_path)
        if self.floating_enabled:
            self.floating_window.deiconify()
        else:
            self.floating_window.withdraw()

        # Logo / Signature canvas
        logo_path = str(get_resource_path("dependencies/images/logo.png"))
        self.logo_canvas = tk.Canvas(
            self.root, width=600, height=224, bg=YELLOW, highlightthickness=0
        )
        try:
            self.logo_img = tk.PhotoImage(file=logo_path)
            self.logo_canvas.create_image(300, 112, image=self.logo_img)
        except Exception:
            pass
        self.logo_canvas.grid(column=1, row=0)
        self.logo_canvas.place(x=-300, y=230)

        # Main Tomato timer canvas
        tomato_path = str(get_resource_path("dependencies/images/tomato.png"))
        self.canvas = tk.Canvas(
            self.root, width=200, height=240, bg=YELLOW, highlightthickness=0
        )
        try:
            self.tomato_img = tk.PhotoImage(file=tomato_path)
            self.canvas.create_image(100, 112, image=self.tomato_img)
        except Exception:
            pass
        self.timer_text = self.canvas.create_text(
            103, 130, text="00:00", font=(FONT_NAME, 30, "bold"), fill="white"
        )
        self.canvas.grid(column=1, row=1)

        # Labels
        self.timer_label = tk.Label(
            self.root, text="TIMER", font=(FONT_NAME, 40, "bold"), bg=YELLOW, fg=GREEN
        )
        self.timer_label.grid(column=1, row=0)

        self.modes_label = tk.Label(
            self.root, text="Modes", font=(FONT_NAME, 20, "bold"), bg=YELLOW, fg=ORANGE
        )
        self.modes_label.grid(column=1, row=0)
        self.modes_label.place(x=200, y=-50)

        self.check_mark = tk.Label(
            self.root, font=(FONT_NAME, 15, "bold"), bg=YELLOW, fg=GREEN
        )
        self.check_mark.grid(column=1, row=3)
        self.check_mark.place(x=120, y=300)

        # Buttons
        self.start_button = tk.Button(
            self.root, text="Start", command=self.on_start, highlightthickness=0
        )
        self.start_button.grid(column=0, row=2)
        self.start_button.place(x=-30, y=291)

        self.pause_button = tk.Button(
            self.root, text="Pause", command=self.on_toggle_pause, highlightthickness=0
        )
        self.pause_button.grid(column=0, row=2)
        self.pause_button.place(x=4, y=291)

        self.reset_button = tk.Button(
            self.root, text="Reset", highlightthickness=0, command=self.on_reset
        )
        self.reset_button.grid(column=2, row=2)
        self.reset_button.place(x=175, y=291)

        self.save_button = tk.Button(
            self.root, text="Save", highlightthickness=0, command=self.on_save
        )
        self.save_button.grid(column=2, row=2)
        self.save_button.place(x=213, y=291)

        # Floating window checkbox
        self.checked_state = tk.IntVar(value=1 if self.floating_enabled else 0)
        self.checkbutton = tk.Checkbutton(
            self.root,
            text="SmallWindow",
            variable=self.checked_state,
            command=self.on_toggle_floating,
            background=YELLOW,
        )
        self.checkbutton.place(x=200, y=20)

        # Radio buttons
        self.radio_state = tk.IntVar(value=0)
        self.radio_pomodoro = tk.Radiobutton(
            self.root,
            text="Pomodoro",
            value=1,
            variable=self.radio_state,
            command=self.on_select_pomodoro,
            bg=YELLOW,
            highlightthickness=0,
        )
        self.radio_stopwatch = tk.Radiobutton(
            self.root,
            text="Stopwatch",
            value=2,
            variable=self.radio_state,
            command=self.on_select_stopwatch,
            bg=YELLOW,
            highlightthickness=0,
        )
        self.radio_pomodoro.place(x=200, y=-20)
        self.radio_stopwatch.place(x=200, y=0)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_select_pomodoro(self) -> None:
        if self.timer.mode == TimerMode.STOPWATCH:
            h, m, s = self.timer.get_stopwatch_hms()
            save_time_snapshot(h, m, s, self.time_path)

        self._cancel_tick()
        trans = self.timer.select_pomodoro()
        self._render_transition(trans)

    def on_select_stopwatch(self) -> None:
        if self.timer.mode == TimerMode.STOPWATCH:
            h, m, s = self.timer.get_stopwatch_hms()
            save_time_snapshot(h, m, s, self.time_path)

        self._cancel_tick()
        h, m, s = load_time_snapshot(self.time_path)
        trans = self.timer.select_stopwatch(h, m, s)
        self._render_transition(trans)

    def on_start(self) -> None:
        if self.timer.mode == TimerMode.NONE:
            messagebox.showerror("Choose a mod", "No mode selected!")
            return

        trans = self.timer.start()
        self._render_transition(trans)

        if self.timer.status == TimerStatus.RUNNING and self.active_after_id is None:
            self._schedule_tick()

    def on_toggle_pause(self) -> None:
        if self.timer.mode == TimerMode.NONE:
            return

        trans = self.timer.toggle_pause()
        if trans.status == TimerStatus.PAUSED:
            self._cancel_tick()
        elif trans.status == TimerStatus.RUNNING:
            self._schedule_tick()

        self._render_transition(trans)

    def on_reset(self, confirm: bool = True) -> None:
        if confirm:
            if not messagebox.askyesno("Reset Timer", "Are you sure you want to reset the timer?"):
                return

        self._cancel_tick()
        trans = self.timer.reset()
        self._render_transition(trans)

    def _schedule_tick(self) -> None:
        self._cancel_tick()
        self.active_after_id = self.root.after(1000, self._on_timer_tick)

    def _cancel_tick(self) -> None:
        if self.active_after_id is not None:
            try:
                self.root.after_cancel(self.active_after_id)
            except Exception:
                pass
            self.active_after_id = None

    def _on_timer_tick(self) -> None:
        self.active_after_id = None
        trans = self.timer.tick_second()

        if trans.sound_role != SoundRole.NONE:
            self.audio.play(trans.sound_role)

        self._render_transition(trans)

        if self.timer.status == TimerStatus.RUNNING:
            self._schedule_tick()

    def _render_transition(self, trans: TimerTransition) -> None:
        display = trans.display_text

        # Update main canvas timer text and font size
        font_size = MAIN_HOUR_FONT_SIZE if trans.show_hours else MAIN_MINUTE_FONT_SIZE
        self.canvas.itemconfig(
            self.timer_text, text=display, font=(FONT_NAME, font_size, "bold")
        )

        # Update floating window
        self.floating_window.update_display(display, trans.show_hours)

        # Update timer label text and color
        if trans.mode == TimerMode.POMODORO:
            if trans.status == TimerStatus.IDLE:
                fg_color = GREEN
            elif trans.phase == PomodoroPhase.WORK:
                fg_color = RED
            else:
                fg_color = DEEP_GOLD_COLOR
        elif trans.mode == TimerMode.STOPWATCH:
            if trans.status == TimerStatus.IDLE:
                fg_color = GREEN
            else:
                fg_color = RED
        else:
            fg_color = GREEN

        self.timer_label.config(text=trans.status_label, fg=fg_color)

        # Update check marks
        ticks = trans.completed_work_ticks
        self.check_mark.config(text="✔" * ticks)
        if ticks == 1:
            self.check_mark.place(x=90, y=290)
        elif ticks == 2:
            self.check_mark.place(x=80, y=290)
        elif ticks == 3:
            self.check_mark.place(x=70, y=290)
        elif ticks == 4:
            self.check_mark.place(x=60, y=290)
        else:
            self.check_mark.place(x=120, y=300)

        # Update pause/resume button label
        self.pause_button.config(text=trans.button_pause_label)

    def on_toggle_floating(self) -> None:
        self.floating_enabled = bool(self.checked_state.get())
        if self.floating_enabled:
            self.floating_window.deiconify()
        else:
            self.floating_window.withdraw()
        save_floating_preference(self.floating_enabled, self.pref_path)

    def on_save(self) -> None:
        if self.timer.mode != TimerMode.STOPWATCH:
            messagebox.showerror(
                "Error", "You need to be in stopwatch mode to use save button."
            )
            return

        if self.timer.status == TimerStatus.RUNNING:
            trans = self.timer.pause()
            self._cancel_tick()
            self._render_transition(trans)

        h, m, s = self.timer.get_stopwatch_hms()
        save_time_snapshot(h, m, s, self.time_path)

        saved_note = ""
        if not self.config.notepad_mode:
            dialog = LargeAskStringDialog(
                self.root, title="Save your note", prompt="Write your note:"
            )
            res = dialog.result
            if res and res.strip() and res.strip().lower() not in ("pass", "none"):
                messagebox.showinfo("Your note:", res)
                saved_note = res

        time_str = format_time_str(h, m, s, show_hours=(h > 0))
        note_file_path = append_saved_entry(
            self.config.note_path, time_str, saved_note=saved_note
        )

        self.open_notepad(note_file_path)

        if self.pixela.is_configured():
            self.pixela.sync_hours_async(h)

    def on_closing(self) -> None:
        if self.timer.mode == TimerMode.STOPWATCH:
            h, m, s = self.timer.get_stopwatch_hms()
            save_time_snapshot(h, m, s, self.time_path)

        self._cancel_tick()
        self.root.destroy()

    def run(self) -> None:
        """Start the Tkinter event loop."""
        self.root.mainloop()
