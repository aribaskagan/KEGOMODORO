"""Unit tests for kegomodoro.timer state machine."""


from kegomodoro.timer import (
    PomodoroPhase,
    SoundRole,
    TimerController,
    TimerMode,
    TimerStatus,
)


def test_initial_state():
    timer = TimerController(work_min=25, short_break_min=5, long_break_min=20)
    assert timer.mode == TimerMode.NONE
    assert timer.status == TimerStatus.IDLE


def test_select_pomodoro():
    timer = TimerController(work_min=25, short_break_min=5, long_break_min=20)
    trans = timer.select_pomodoro()

    assert trans.mode == TimerMode.POMODORO
    assert trans.status == TimerStatus.IDLE
    assert trans.phase == PomodoroPhase.WORK
    assert trans.display_text == "25:00"
    assert trans.completed_work_ticks == 0
    assert trans.status_label == "TIMER"


def test_start_idempotency_and_pause_resume():
    timer = TimerController(work_min=25, short_break_min=5, long_break_min=20)
    timer.select_pomodoro()

    trans1 = timer.start()
    assert trans1.status == TimerStatus.RUNNING
    assert trans1.status_label == "Work"

    # Second start is idempotent
    trans2 = timer.start()
    assert trans2.status == TimerStatus.RUNNING

    # Tick 5 seconds
    for _ in range(5):
        timer.tick_second()

    assert timer.pomodoro_remaining_seconds == 25 * 60 - 5

    # Pause
    trans_pause = timer.pause()
    assert trans_pause.status == TimerStatus.PAUSED
    assert trans_pause.status_label == "Paused"
    assert trans_pause.display_text == "24:55"

    # Ticking while paused does nothing
    timer.tick_second()
    assert timer.pomodoro_remaining_seconds == 25 * 60 - 5

    # Resume
    trans_resume = timer.resume()
    assert trans_resume.status == TimerStatus.RUNNING
    assert trans_resume.status_label == "Work"
    assert trans_resume.display_text == "24:55"


def test_full_pomodoro_cycle_four_sessions():
    # Use 1-minute durations for fast testing
    timer = TimerController(work_min=1, short_break_min=1, long_break_min=2)
    timer.select_pomodoro()

    # --- Work Session 1 ---
    timer.start()
    for _ in range(59):
        trans = timer.tick_second()
        assert trans.status == TimerStatus.RUNNING
        assert trans.sound_role == SoundRole.NONE

    # Final second of Work 1
    trans = timer.tick_second()
    assert trans.completed_work_ticks == 1
    assert trans.phase == PomodoroPhase.SHORT_BREAK
    assert trans.sound_role == SoundRole.SHORT_BREAK
    assert trans.status == TimerStatus.PAUSED
    assert trans.waiting_for_resume is True
    assert trans.display_text == "01:00"

    # --- Short Break 1 ---
    timer.resume()
    for _ in range(59):
        timer.tick_second()
    trans = timer.tick_second()
    assert trans.completed_work_ticks == 1
    assert trans.phase == PomodoroPhase.WORK
    assert trans.sound_role == SoundRole.WORK
    assert trans.status == TimerStatus.PAUSED
    assert trans.waiting_for_resume is True
    assert trans.display_text == "01:00"

    # --- Work Session 2 ---
    timer.resume()
    for _ in range(60):
        trans = timer.tick_second()
    assert trans.completed_work_ticks == 2
    assert trans.phase == PomodoroPhase.SHORT_BREAK
    assert trans.sound_role == SoundRole.SHORT_BREAK

    # --- Short Break 2 ---
    timer.resume()
    for _ in range(60):
        trans = timer.tick_second()
    assert trans.phase == PomodoroPhase.WORK
    assert trans.sound_role == SoundRole.WORK

    # --- Work Session 3 ---
    timer.resume()
    for _ in range(60):
        trans = timer.tick_second()
    assert trans.completed_work_ticks == 3
    assert trans.phase == PomodoroPhase.SHORT_BREAK
    assert trans.sound_role == SoundRole.SHORT_BREAK

    # --- Short Break 3 ---
    timer.resume()
    for _ in range(60):
        trans = timer.tick_second()
    assert trans.phase == PomodoroPhase.WORK
    assert trans.sound_role == SoundRole.WORK

    # --- Work Session 4 ---
    timer.resume()
    for _ in range(60):
        trans = timer.tick_second()
    assert trans.completed_work_ticks == 4
    assert trans.phase == PomodoroPhase.LONG_BREAK
    assert trans.sound_role == SoundRole.LONG_BREAK
    assert trans.display_text == "02:00"

    # --- Long Break ---
    timer.resume()
    for _ in range(120):
        trans = timer.tick_second()
    # Cycle complete!
    assert trans.completed_work_ticks == 0
    assert trans.phase == PomodoroPhase.WORK
    assert trans.sound_role == SoundRole.NEW_WORK
    assert trans.display_text == "01:00"
    assert trans.waiting_for_resume is True


def test_stopwatch_countup_and_hour_crossing():
    timer = TimerController()
    timer.select_stopwatch(saved_hours=0, saved_minute=59, saved_second=58)

    assert timer.stopwatch_seconds == 3598
    trans = timer.start()
    assert trans.status == TimerStatus.RUNNING
    assert trans.status_label == "WORK"

    # Tick to 59:59
    trans = timer.tick_second()
    assert trans.display_text == "59:59"
    assert trans.show_hours is False

    # Tick to 01:00:00 (cross 59:59)
    trans = timer.tick_second()
    assert trans.hours == 1
    assert trans.minute == 0
    assert trans.second == 0
    assert trans.show_hours is True
    assert trans.display_text == "01:00:00"


def test_timer_reset():
    timer = TimerController(work_min=25)
    timer.select_pomodoro()
    timer.start()
    timer.tick_second()

    trans = timer.reset()
    assert trans.status == TimerStatus.IDLE
    assert trans.display_text == "25:00"
    assert trans.status_label == "TIMER"
    assert trans.completed_work_ticks == 0
