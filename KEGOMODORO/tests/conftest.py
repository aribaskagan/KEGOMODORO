"""Global pytest fixtures and test configuration."""

import sys
from pathlib import Path
import pytest

# Ensure KEGOMODORO is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


@pytest.fixture(autouse=True)
def isolate_persistent_storage(tmp_path, monkeypatch):
    """Ensure all tests use an isolated temporary persistent root instead of user Documents."""
    storage_root = tmp_path / "persistent_storage"
    storage_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        "kegomodoro.paths.get_persistent_root", lambda: storage_root
    )
    return storage_root


@pytest.fixture(autouse=True)
def block_live_network(monkeypatch):
    """Safety guard: prevent any un-mocked outgoing network requests."""
    import socket

    orig_connect = socket.socket.connect

    def guarded_connect(self, address):
        host = address[0] if isinstance(address, tuple) else address
        # Allow localhost / unix domain sockets if needed
        if host not in ("127.0.0.1", "localhost", "::1"):
            raise RuntimeError(
                f"Blocked attempt to establish live network connection to {address} during tests."
            )
        return orig_connect(self, address)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
