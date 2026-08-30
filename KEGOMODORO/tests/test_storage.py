"""Unit tests for kegomodoro.storage."""

import datetime as dt

from kegomodoro.storage import (
    AppConfig,
    append_saved_entry,
    format_time_str,
    load_configuration,
    load_floating_preference,
    load_time_snapshot,
    parse_bool,
    parse_saved_date,
    resolve_note_path,
    save_configuration,
    save_floating_preference,
    save_time_snapshot,
)


def test_parse_bool():
    assert parse_bool("true") is True
    assert parse_bool("True") is True
    assert parse_bool("1") is True
    assert parse_bool("yes") is True
    assert parse_bool("correct") is True
    assert parse_bool("t") is True
    assert parse_bool("y") is True
    assert parse_bool("false") is False
    assert parse_bool("0") is False
    assert parse_bool("no") is False
    assert parse_bool(None, default=True) is True
    assert parse_bool(None, default=False) is False


def test_resolve_note_path(tmp_path):
    root = tmp_path / "persist"
    default_note = root / "config" / "notes.txt"

    assert resolve_note_path("", root, default_note) == default_note
    assert resolve_note_path("my_notes.txt", root, default_note) == root / "my_notes.txt"

    abs_custom = tmp_path / "custom" / "diary.txt"
    assert resolve_note_path(str(abs_custom), root, default_note) == abs_custom


def test_load_configuration_missing_file(tmp_path):
    missing_file = tmp_path / "non_existent.csv"
    cfg = load_configuration(missing_file, persistent_root=tmp_path)
    assert cfg.work_min == 25
    assert cfg.short_break_min == 5
    assert cfg.long_break_min == 20
    assert cfg.notepad_mode is True


def test_load_configuration_valid_5_column(tmp_path):
    cfg_file = tmp_path / "config.csv"
    cfg_file.write_text(
        "WORK_MIN,SHORT_BREAK_MIN,LONG_BREAK_MIN,NOTEPAD_MODE,NOTE_PATH\n50,10,30,1,custom_notes.txt\n",
        encoding="utf-8",
    )
    cfg = load_configuration(cfg_file, persistent_root=tmp_path)
    assert cfg.work_min == 50
    assert cfg.short_break_min == 10
    assert cfg.long_break_min == 30
    assert cfg.notepad_mode is True
    assert cfg.note_path == tmp_path / "custom_notes.txt"


def test_load_configuration_legacy_4_column(tmp_path):
    cfg_file = tmp_path / "config.csv"
    cfg_file.write_text(
        "WORK_MIN,SHORT_BREAK_MIN,LONG_BREAK_MIN,NOTEPAD_MODE\n35,7,25,0\n",
        encoding="utf-8",
    )
    cfg = load_configuration(cfg_file, persistent_root=tmp_path)
    assert cfg.work_min == 35
    assert cfg.short_break_min == 7
    assert cfg.long_break_min == 25
    assert cfg.notepad_mode is False


def test_load_configuration_malformed_fields_survive(tmp_path):
    cfg_file = tmp_path / "config.csv"
    cfg_file.write_text(
        "WORK_MIN,SHORT_BREAK_MIN,LONG_BREAK_MIN,NOTEPAD_MODE,NOTE_PATH\ncorrupt,-5,40,invalid_bool,\n",
        encoding="utf-8",
    )
    cfg = load_configuration(cfg_file, persistent_root=tmp_path)
    # Valid field 40 survives, corrupt/negative fields use defaults
    assert cfg.work_min == 25
    assert cfg.short_break_min == 5
    assert cfg.long_break_min == 40
    assert cfg.notepad_mode is True


def test_save_and_load_configuration_roundtrip(tmp_path):
    cfg_file = tmp_path / "config.csv"
    orig_cfg = AppConfig(
        work_min=30,
        short_break_min=6,
        long_break_min=15,
        notepad_mode=True,
        note_path=tmp_path / "notes.txt",
    )
    save_configuration(orig_cfg, cfg_file, persistent_root=tmp_path)

    loaded_cfg = load_configuration(cfg_file, persistent_root=tmp_path)
    assert loaded_cfg.work_min == 30
    assert loaded_cfg.short_break_min == 6
    assert loaded_cfg.long_break_min == 15
    assert loaded_cfg.notepad_mode is True
    assert loaded_cfg.note_path == tmp_path / "notes.txt"


def test_time_snapshot_missing_and_save(tmp_path):
    time_file = tmp_path / "time.csv"
    h, m, s = load_time_snapshot(time_file)
    assert (h, m, s) == (0, 0, 0)

    save_time_snapshot(2, 45, 30, time_file)
    h, m, s = load_time_snapshot(time_file)
    assert (h, m, s) == (2, 45, 30)


def test_time_snapshot_legacy_multi_row(tmp_path):
    time_file = tmp_path / "time.csv"
    time_file.write_text(
        "0,10,20\n1,15,30\n2,50,45\n",
        encoding="utf-8",
    )
    h, m, s = load_time_snapshot(time_file)
    assert (h, m, s) == (2, 50, 45)


def test_floating_preference_roundtrip(tmp_path):
    pref_file = tmp_path / "floating.txt"
    assert load_floating_preference(pref_file, default=False) is False

    save_floating_preference(True, pref_file)
    assert load_floating_preference(pref_file) is True

    save_floating_preference(False, pref_file)
    assert load_floating_preference(pref_file) is False


def test_parse_saved_date():
    assert parse_saved_date("08/30/2026") == dt.date(2026, 8, 30)
    assert parse_saved_date("08.30.2026") == dt.date(2026, 8, 30)
    assert parse_saved_date("30/08/2026") == dt.date(2026, 8, 30)
    assert parse_saved_date("30.08.2026") == dt.date(2026, 8, 30)
    assert parse_saved_date("invalid-date") is None


def test_format_time_str():
    assert format_time_str(0, 25, 30, show_hours=False) == "25:30"
    assert format_time_str(1, 25, 30, show_hours=True) == "01:25:30"
    assert format_time_str(2, 5, 9, show_hours=False) == "02:05:09"  # hours > 0 forces hours


def test_append_saved_entry_new_file(tmp_path):
    note_path = tmp_path / "notes.txt"
    test_date = dt.date(2026, 8, 30)

    append_saved_entry(note_path, "25:00", saved_note="First session", today_date=test_date)
    content = note_path.read_text(encoding="utf-8")
    assert "08/30/2026\n25:00 First session" in content


def test_append_saved_entry_same_day_merge(tmp_path):
    note_path = tmp_path / "notes.txt"
    test_date = dt.date(2026, 8, 30)

    # First entry on test_date
    append_saved_entry(note_path, "25:00", saved_note="Morning session", today_date=test_date)
    # Second entry on same test_date
    append_saved_entry(note_path, "50:00", saved_note="Afternoon session", today_date=test_date)

    content = note_path.read_text(encoding="utf-8")
    # Must only have ONE date header for 08/30/2026
    assert content.count("08/30/2026") == 1
    assert "50:00 Morning session" in content
    assert "Afternoon session" in content


def test_append_saved_entry_legacy_date_merge(tmp_path):
    note_path = tmp_path / "notes.txt"
    test_date = dt.date(2026, 8, 30)

    # Existing content with legacy dot format
    note_path.write_text("30.08.2026\n15:00 Initial work\n", encoding="utf-8")

    append_saved_entry(note_path, "45:00", saved_note="Followup work", today_date=test_date)

    content = note_path.read_text(encoding="utf-8")
    assert content.count("30.08.2026") == 1
    assert "45:00 Initial work" in content
    assert "Followup work" in content
