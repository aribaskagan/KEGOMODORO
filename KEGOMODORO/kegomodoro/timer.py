"""Pure timer and Pomodoro state machine for KEGOMODORO."""

from dataclasses import dataclass
from enum import Enum, auto


class TimerMode(Enum):
    NONE = auto()
    POMODORO = auto()
    STOPWATCH = auto()


class PomodoroPhase(Enum):
    WORK = auto()
    SHORT_BREAK = auto()
    LONG_BREAK = auto()


class TimerStatus(Enum):
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()


class SoundRole(Enum):
    NONE = auto()
    SHORT_BREAK = auto()
    LONG_BREAK = auto()
    WORK = auto()
    NEW_WORK = auto()


@dataclass(frozen=True)
class TimerTransition:
    mode: TimerMode
    status: TimerStatus
    phase: PomodoroPhase
    hours: int
    minute: int
    second: int
    show_hours: bool
    completed_work_ticks: int
    sound_role: SoundRole
    waiting_for_resume: bool
    status_label: str
    button_pause_label: str

    @property
    def display_text(self) -> str:
        if self.show_hours or self.hours > 0:
            return f"{self.hours:02d}:{self.minute:02d}:{self.second:02d}"
        return f"{self.minute:02d}:{self.second:02d}"


class TimerController:
    """Pure timer controller encapsulating all Pomodoro and Stopwatch timing logic."""

    def __init__(
        self,
        work_min: int = 25,
        short_break_min: int = 5,
        long_break_min: int = 20,
    ):
        self.work_min = max(1, work_min)
        self.short_break_min = max(1, short_break_min)
        self.long_break_min = max(1, long_break_min)

        self.mode = TimerMode.NONE
        self.status = TimerStatus.IDLE
        self.phase = PomodoroPhase.WORK

        # Pomodoro cycle tracking
        # Completed work sessions within current 4-session cycle (0..4)
        self.completed_work_ticks = 0
        self.pomodoro_remaining_seconds = self.work_min * 60
        self.waiting_for_resume = False
        self._was_long_break_transition = False

        # Stopwatch tracking
        self.stopwatch_seconds = 0

    def update_durations(
        self, work_min: int, short_break_min: int, long_break_min: int
    ) -> None:
        self.work_min = max(1, work_min)
        self.short_break_min = max(1, short_break_min)
        self.long_break_min = max(1, long_break_min)

    def select_pomodoro(self) -> TimerTransition:
        self.mode = TimerMode.POMODORO
        self.status = TimerStatus.IDLE
        self.phase = PomodoroPhase.WORK
        self.completed_work_ticks = 0
        self.pomodoro_remaining_seconds = self.work_min * 60
        self.waiting_for_resume = False
        self._was_long_break_transition = False
        return self._make_transition(sound=SoundRole.NONE)

    def select_stopwatch(
        self, saved_hours: int = 0, saved_minute: int = 0, saved_second: int = 0
    ) -> TimerTransition:
        self.mode = TimerMode.STOPWATCH
        self.status = TimerStatus.IDLE
        self.stopwatch_seconds = max(
            0, saved_hours * 3600 + saved_minute * 60 + saved_second
        )
        return self._make_transition(sound=SoundRole.NONE)

    def start(self) -> TimerTransition:
        if self.mode == TimerMode.NONE:
            return self._make_transition(sound=SoundRole.NONE)

        if self.status == TimerStatus.RUNNING:
            return self._make_transition(sound=SoundRole.NONE)

        if self.mode == TimerMode.POMODORO:
            self.status = TimerStatus.RUNNING
            self.waiting_for_resume = False
            return self._make_transition(sound=SoundRole.NONE)

        elif self.mode == TimerMode.STOPWATCH:
            self.status = TimerStatus.RUNNING
            return self._make_transition(sound=SoundRole.NONE)

        return self._make_transition(sound=SoundRole.NONE)

    def pause(self) -> TimerTransition:
        if self.mode == TimerMode.NONE or self.status != TimerStatus.RUNNING:
            return self._make_transition(sound=SoundRole.NONE)

        self.status = TimerStatus.PAUSED
        return self._make_transition(sound=SoundRole.NONE)

    def resume(self) -> TimerTransition:
        if self.mode == TimerMode.NONE or self.status != TimerStatus.PAUSED:
            return self._make_transition(sound=SoundRole.NONE)

        self.status = TimerStatus.RUNNING
        self.waiting_for_resume = False
        return self._make_transition(sound=SoundRole.NONE)

    def toggle_pause(self) -> TimerTransition:
        if self.status == TimerStatus.RUNNING:
            return self.pause()
        elif self.status == TimerStatus.PAUSED:
            return self.resume()
        return self._make_transition(sound=SoundRole.NONE)

    def reset(self) -> TimerTransition:
        if self.mode == TimerMode.POMODORO:
            self.status = TimerStatus.IDLE
            self.phase = PomodoroPhase.WORK
            self.completed_work_ticks = 0
            self.pomodoro_remaining_seconds = self.work_min * 60
            self.waiting_for_resume = False
            self._was_long_break_transition = False
        elif self.mode == TimerMode.STOPWATCH:
            self.status = TimerStatus.IDLE
            self.stopwatch_seconds = 0
        else:
            self.status = TimerStatus.IDLE

        return self._make_transition(sound=SoundRole.NONE, forced_status_label="TIMER")

    def tick_second(self) -> TimerTransition:
        """Advance time by one second if running."""
        if self.status != TimerStatus.RUNNING:
            return self._make_transition(sound=SoundRole.NONE)

        if self.mode == TimerMode.POMODORO:
            if self.pomodoro_remaining_seconds > 0:
                self.pomodoro_remaining_seconds -= 1

            if self.pomodoro_remaining_seconds == 0:
                # Current interval finished
                return self._advance_pomodoro_interval()
            else:
                return self._make_transition(sound=SoundRole.NONE)

        elif self.mode == TimerMode.STOPWATCH:
            self.stopwatch_seconds += 1
            return self._make_transition(sound=SoundRole.NONE)

        return self._make_transition(sound=SoundRole.NONE)

    def _advance_pomodoro_interval(self) -> TimerTransition:
        """Transition Pomodoro to the next interval and pause until resumed."""
        sound = SoundRole.NONE
        self.status = TimerStatus.PAUSED
        self.waiting_for_resume = True

        if self.phase == PomodoroPhase.WORK:
            self.completed_work_ticks += 1
            if self.completed_work_ticks >= 4:
                # Enter Long Break
                self.phase = PomodoroPhase.LONG_BREAK
                self.pomodoro_remaining_seconds = self.long_break_min * 60
                sound = SoundRole.LONG_BREAK
                self._was_long_break_transition = True
            else:
                # Enter Short Break
                self.phase = PomodoroPhase.SHORT_BREAK
                self.pomodoro_remaining_seconds = self.short_break_min * 60
                sound = SoundRole.SHORT_BREAK
                self._was_long_break_transition = False
        elif self.phase == PomodoroPhase.SHORT_BREAK:
            # Return to Work
            self.phase = PomodoroPhase.WORK
            self.pomodoro_remaining_seconds = self.work_min * 60
            sound = SoundRole.WORK
            self._was_long_break_transition = False
        elif self.phase == PomodoroPhase.LONG_BREAK:
            # Start new cycle after Long Break
            self.phase = PomodoroPhase.WORK
            self.completed_work_ticks = 0
            self.pomodoro_remaining_seconds = self.work_min * 60
            sound = SoundRole.NEW_WORK
            self._was_long_break_transition = False

        return self._make_transition(sound=sound)

    def get_stopwatch_hms(self) -> tuple[int, int, int]:
        h = self.stopwatch_seconds // 3600
        m = (self.stopwatch_seconds % 3600) // 60
        s = self.stopwatch_seconds % 60
        return h, m, s

    def _make_transition(
        self, sound: SoundRole = SoundRole.NONE, forced_status_label: str | None = None
    ) -> TimerTransition:
        if self.mode == TimerMode.POMODORO:
            h = 0
            m = self.pomodoro_remaining_seconds // 60
            s = self.pomodoro_remaining_seconds % 60
            show_h = False

            if forced_status_label is not None:
                lbl = forced_status_label
            elif self.status == TimerStatus.IDLE:
                lbl = "TIMER"
            elif self.status == TimerStatus.PAUSED:
                if self.waiting_for_resume:
                    lbl = "Break" if self.phase != PomodoroPhase.WORK else "Work"
                else:
                    lbl = "Paused"
            else:
                # Running
                lbl = "Break" if self.phase != PomodoroPhase.WORK else "Work"

            btn_pause = "Resume" if self.status == TimerStatus.PAUSED else "Pause"

            return TimerTransition(
                mode=self.mode,
                status=self.status,
                phase=self.phase,
                hours=h,
                minute=m,
                second=s,
                show_hours=show_h,
                completed_work_ticks=self.completed_work_ticks,
                sound_role=sound,
                waiting_for_resume=self.waiting_for_resume,
                status_label=lbl,
                button_pause_label=btn_pause,
            )

        elif self.mode == TimerMode.STOPWATCH:
            h, m, s = self.get_stopwatch_hms()
            show_h = h > 0

            if forced_status_label is not None:
                lbl = forced_status_label
            elif self.status == TimerStatus.IDLE:
                lbl = "TIMER"
            elif self.status == TimerStatus.PAUSED:
                lbl = "Paused"
            else:
                lbl = "WORK"

            btn_pause = "Resume" if self.status == TimerStatus.PAUSED else "Pause"

            return TimerTransition(
                mode=self.mode,
                status=self.status,
                phase=self.phase,
                hours=h,
                minute=m,
                second=s,
                show_hours=show_h,
                completed_work_ticks=0,
                sound_role=sound,
                waiting_for_resume=False,
                status_label=lbl,
                button_pause_label=btn_pause,
            )

        else:
            return TimerTransition(
                mode=TimerMode.NONE,
                status=TimerStatus.IDLE,
                phase=PomodoroPhase.WORK,
                hours=0,
                minute=0,
                second=0,
                show_hours=False,
                completed_work_ticks=0,
                sound_role=sound,
                waiting_for_resume=False,
                status_label="TIMER",
                button_pause_label="Pause",
            )
