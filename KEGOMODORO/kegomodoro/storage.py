"""Storage and persistence handling for KEGOMODORO configuration, time snapshots, and notes."""

import csv
import datetime as dt
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from kegomodoro.paths import get_persistent_path, get_persistent_root


@dataclass
class AppConfig:
    work_min: int = 25
    short_break_min: int = 5
    long_break_min: int = 20
    notepad_mode: bool = True
    note_path: Path | None = None

    def __post_init__(self):
        if self.note_path is None:
            self.note_path = get_persistent_path("config/notes.txt")


def parse_bool(value: object, default: bool = False) -> bool:
    """Parse boolean from various string or numeric representations."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    val_str = str(value).strip().lower()
    if val_str in ("true", "1", "yes", "correct", "t", "y", "yeah", "yup"):
        return True
    if val_str in ("false", "0", "no", "f", "n", "nope"):
        return False
    return default


def resolve_note_path(
    note_path_value: str | Path | None,
    persistent_root: Path | None = None,
    default_note_path: Path | None = None,
) -> Path:
    """Resolve a note path to an absolute path, expanding env vars and ~."""
    if persistent_root is None:
        persistent_root = get_persistent_root()
    if default_note_path is None:
        default_note_path = persistent_root / "config" / "notes.txt"

    val_str = str(note_path_value or "").strip()
    if not val_str:
        resolved = default_note_path
    else:
        expanded = os.path.expandvars(os.path.expanduser(val_str))
        path = Path(expanded)
        if not path.is_absolute():
            resolved = persistent_root / path
        else:
            resolved = path

    try:
        resolved.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return resolved


def _atomic_write_text(target_path: Path, content: str, encoding: str = "utf-8") -> None:
    """Write text atomically to target_path using a temporary file in the same directory."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path_str = tempfile.mkstemp(
        dir=str(target_path.parent), prefix=f".{target_path.name}.", suffix=".tmp"
    )
    with os.fdopen(tmp_fd, "w", encoding=encoding, newline="") as f:
        f.write(content)
    os.replace(tmp_path_str, target_path)


def load_configuration(
    config_path: Path | None = None, persistent_root: Path | None = None
) -> AppConfig:
    """Load configuration from CSV, falling back per-field to defaults on corruption."""
    if persistent_root is None:
        persistent_root = get_persistent_root()
    if config_path is None:
        config_path = persistent_root / "config" / "configuration.csv"

    default_note_path = persistent_root / "config" / "notes.txt"
    config = AppConfig(note_path=default_note_path)

    if not config_path.is_file():
        return config

    try:
        with open(config_path, "r", encoding="utf-8", newline="") as file:
            reader = csv.reader(file)
            rows = [row for row in reader if row and any(cell.strip() for cell in row)]

        if not rows:
            return config

        header = [col.strip().upper() for col in rows[0]]
        if "WORK_MIN" in header:
            # Header row exists
            if len(rows) < 2:
                return config
            data_row = rows[1]
            row_dict = {
                header[i]: data_row[i].strip()
                for i in range(min(len(header), len(data_row)))
            }
        else:
            # Legacy headless row
            data_row = rows[0]
            header_keys = [
                "WORK_MIN",
                "SHORT_BREAK_MIN",
                "LONG_BREAK_MIN",
                "NOTEPAD_MODE",
                "NOTE_PATH",
            ]
            row_dict = {
                header_keys[i]: data_row[i].strip()
                for i in range(min(len(header_keys), len(data_row)))
            }

        # Field-by-field validation
        if "WORK_MIN" in row_dict:
            try:
                val = int(row_dict["WORK_MIN"])
                if val > 0:
                    config.work_min = val
            except (ValueError, TypeError):
                pass

        if "SHORT_BREAK_MIN" in row_dict:
            try:
                val = int(row_dict["SHORT_BREAK_MIN"])
                if val > 0:
                    config.short_break_min = val
            except (ValueError, TypeError):
                pass

        if "LONG_BREAK_MIN" in row_dict:
            try:
                val = int(row_dict["LONG_BREAK_MIN"])
                if val > 0:
                    config.long_break_min = val
            except (ValueError, TypeError):
                pass

        if "NOTEPAD_MODE" in row_dict:
            config.notepad_mode = parse_bool(row_dict["NOTEPAD_MODE"], default=True)

        if "NOTE_PATH" in row_dict:
            config.note_path = resolve_note_path(
                row_dict["NOTE_PATH"],
                persistent_root=persistent_root,
                default_note_path=default_note_path,
            )

    except Exception:
        return config

    return config


def save_configuration(
    config: AppConfig,
    config_path: Path | None = None,
    persistent_root: Path | None = None,
) -> None:
    """Save configuration to CSV using atomic write."""
    if persistent_root is None:
        persistent_root = get_persistent_root()
    if config_path is None:
        config_path = persistent_root / "config" / "configuration.csv"

    note_path_str = str(config.note_path) if config.note_path else ""
    lines = [
        "WORK_MIN,SHORT_BREAK_MIN,LONG_BREAK_MIN,NOTEPAD_MODE,NOTE_PATH\r\n",
        f"{config.work_min},{config.short_break_min},{config.long_break_min},{int(config.notepad_mode)},{note_path_str}\r\n",
    ]
    _atomic_write_text(config_path, "".join(lines))


def load_time_snapshot(time_path: Path) -> Tuple[int, int, int]:
    """Load time snapshot (hours, minute, second), supporting legacy multi-row files."""
    if not time_path.is_file():
        return 0, 0, 0

    try:
        with open(time_path, "r", encoding="utf-8", newline="") as file:
            reader = csv.reader(file)
            rows = [row for row in reader if row and any(cell.strip() for cell in row)]

        if not rows:
            return 0, 0, 0

        header = [c.strip().lower() for c in rows[0]]
        if "hours" in header or "minute" in header or "second" in header:
            data_rows = rows[1:]
        else:
            data_rows = rows

        if not data_rows:
            return 0, 0, 0

        # Read last valid row
        for row in reversed(data_rows):
            try:
                parts = [int(p.strip()) for p in row if p.strip()]
                if len(parts) == 3:
                    return max(0, parts[0]), max(0, parts[1]), max(0, parts[2])
                if len(parts) == 2:
                    return 0, max(0, parts[0]), max(0, parts[1])
            except (ValueError, TypeError):
                continue

        return 0, 0, 0
    except Exception:
        return 0, 0, 0


def save_time_snapshot(hours: int, minute: int, second: int, time_path: Path) -> None:
    """Save single-row canonical time snapshot atomically."""
    content = f"hours,minute,second\r\n{max(0, hours)},{max(0, minute)},{max(0, second)}\r\n"
    _atomic_write_text(time_path, content)


def load_floating_preference(pref_path: Path, default: bool = False) -> bool:
    """Read boolean floating window preference."""
    if not pref_path.is_file():
        return default

    try:
        text = pref_path.read_text(encoding="utf-8").strip()
        if not text:
            return default
        return parse_bool(text, default=default)
    except Exception:
        return default


def save_floating_preference(enabled: bool, pref_path: Path) -> None:
    """Save boolean floating window preference atomically."""
    _atomic_write_text(pref_path, f"{bool(enabled)}\n")


def parse_saved_date(line: str) -> dt.date | None:
    """Parse date from supported historical formats: mm/dd/yyyy, mm.dd.yyyy, dd/mm/yyyy, dd.mm.yyyy."""
    stripped_line = str(line or "").strip()
    for date_format in ("%m/%d/%Y", "%m.%d.%Y", "%d/%m/%Y", "%d.%m.%Y"):
        try:
            return dt.datetime.strptime(stripped_line, date_format).date()
        except ValueError:
            continue
    return None


def format_time_str(hours: int, minute: int, second: int, show_hours: bool) -> str:
    """Format time string for note entries."""
    if show_hours or hours > 0:
        return f"{hours:02d}:{minute:02d}:{second:02d}"
    return f"{minute:02d}:{second:02d}"


def append_saved_entry(
    note_path: Path,
    time_str: str,
    saved_note: str = "",
    today_date: dt.date | None = None,
) -> Path:
    """
    Append or merge note entry for today's date into the plain-text note file.
    Preserves existing content, merging into an existing section for today without duplicate headers.
    """
    note_path = note_path.resolve()
    note_path.parent.mkdir(parents=True, exist_ok=True)

    if today_date is None:
        today_date = dt.datetime.now().date()
    today_date_slash = today_date.strftime("%m/%d/%Y")

    existing_content = ""
    if note_path.exists():
        existing_content = note_path.read_text(encoding="utf-8")

    lines = existing_content.split("\n") if existing_content else []
    today_index = -1
    for i, line in enumerate(lines):
        if parse_saved_date(line) == today_date:
            today_index = i
            break

    clean_note = saved_note.strip() if saved_note else ""

    if today_index >= 0 and today_index + 1 < len(lines):
        existing_time_line = lines[today_index + 1]
        existing_notes = ""
        space_idx = existing_time_line.find(" ")
        if space_idx > 0:
            existing_notes = existing_time_line[space_idx + 1 :].strip()

        new_time_line = time_str
        if existing_notes:
            new_time_line += " " + existing_notes

        lines[today_index + 1] = new_time_line

        entry_end_index = today_index + 2
        while entry_end_index < len(lines):
            if parse_saved_date(lines[entry_end_index]) is not None:
                break
            entry_end_index += 1

        has_inline_note = " " in new_time_line
        has_notes_below = entry_end_index > today_index + 2

        if clean_note:
            if not has_inline_note and not has_notes_below:
                lines[today_index + 1] = new_time_line + " " + clean_note
            else:
                lines.insert(entry_end_index, "")
                lines.insert(entry_end_index + 1, clean_note)

        _atomic_write_text(note_path, "\n".join(lines))
    else:
        new_entry = f"{today_date_slash}\n{time_str}"
        if clean_note:
            new_entry += f" {clean_note}"

        if existing_content.strip():
            combined = f"{existing_content.rstrip()}\n\n{new_entry}\n"
        else:
            combined = f"{new_entry}\n"

        _atomic_write_text(note_path, combined)

    return note_path
