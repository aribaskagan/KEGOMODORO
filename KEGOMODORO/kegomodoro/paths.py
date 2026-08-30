"""Resource and persistent path resolution for KEGOMODORO."""

import os
import sys
from pathlib import Path


def get_app_dir() -> Path:
    """Return the base directory of the application."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # kegomodoro package is inside KEGOMODORO directory
    return Path(__file__).resolve().parent.parent


def get_resource_path(relative_path: str | Path) -> Path:
    """Get absolute path to resource, working in both source and PyInstaller frozen mode."""
    if hasattr(sys, "_MEIPASS"):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = get_app_dir()
    return (base_path / relative_path).resolve()


def get_documents_dir() -> Path:
    """Resolve the user's Documents folder on Windows with safe fallback."""
    if os.name == "nt":
        try:
            from ctypes import create_unicode_buffer, windll

            csidl_personal = 5
            shgfp_type_current = 0
            buffer = create_unicode_buffer(260)
            if (
                windll.shell32.SHGetFolderPathW(
                    None, csidl_personal, None, shgfp_type_current, buffer
                )
                == 0
            ):
                return Path(buffer.value)
        except Exception:
            pass
    return Path.home() / "Documents"


def get_persistent_root() -> Path:
    """Choose the persistent root folder for user data (config, time, notes)."""
    if getattr(sys, "frozen", False):
        base_path = get_documents_dir() / "KEGOMODORO"
    else:
        base_path = get_app_dir()
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path


def get_persistent_path(relative_path: str | Path) -> Path:
    """Get full path for a persistent file or directory."""
    return get_persistent_root() / relative_path


def load_env_file(env_path: Path) -> bool:
    """Safely parse key=value lines from a .env file without overwriting existing environment vars."""
    if not env_path.is_file():
        return False

    loaded = False
    try:
        with open(env_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if not key:
                    continue

                if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                    value = value[1:-1]

                os.environ.setdefault(key, value)
                loaded = True
    except Exception:
        return False

    return loaded


def load_runtime_env(
    app_dir: Path | None = None, persistent_root: Path | None = None
) -> list[Path]:
    """Load .env files from application directory and persistent root if present."""
    if app_dir is None:
        app_dir = get_app_dir()
    if persistent_root is None:
        persistent_root = get_persistent_root()

    loaded_paths = []
    candidate_paths = [
        app_dir / ".env",
        persistent_root / ".env",
    ]

    seen: set[Path] = set()
    for env_path in candidate_paths:
        try:
            resolved = env_path.resolve()
        except Exception:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)

        if load_env_file(resolved):
            loaded_paths.append(resolved)

    return loaded_paths
