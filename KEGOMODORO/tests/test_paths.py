"""Unit tests for kegomodoro.paths."""

import os
import sys
from pathlib import Path

from kegomodoro.paths import (
    get_app_dir,
    get_documents_dir,
    get_persistent_root,
    get_resource_path,
    load_env_file,
    load_runtime_env,
)


def test_get_app_dir():
    app_dir = get_app_dir()
    assert app_dir.is_dir()
    assert (app_dir / "kegomodoro").is_dir()


def test_get_resource_path_dev_mode():
    res_path = get_resource_path("dependencies/images/tomato.png")
    assert res_path.name == "tomato.png"
    assert res_path.is_absolute()


def test_get_resource_path_frozen_mode(monkeypatch, tmp_path):
    meipass_dir = tmp_path / "meipass"
    meipass_dir.mkdir()
    monkeypatch.setattr(sys, "_MEIPASS", str(meipass_dir), raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    res_path = get_resource_path("dependencies/images/tomato.png")
    assert str(res_path).startswith(str(meipass_dir))


def test_get_documents_dir():
    docs_dir = get_documents_dir()
    assert isinstance(docs_dir, Path)
    assert docs_dir.is_absolute()


def test_get_persistent_root_frozen(monkeypatch, tmp_path):
    fake_docs = tmp_path / "Documents"
    fake_docs.mkdir()
    monkeypatch.setattr("kegomodoro.paths.get_documents_dir", lambda: fake_docs)
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    root = get_persistent_root()
    assert root == fake_docs / "KEGOMODORO"
    assert root.is_dir()


def test_load_env_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "PIXELA_USERNAME=test_user\nPIXELA_TOKEN='secret_token'\n# Comment line\nINVALID_LINE\nEMPTY_VAL=\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("PIXELA_USERNAME", raising=False)
    monkeypatch.delenv("PIXELA_TOKEN", raising=False)

    loaded = load_env_file(env_file)
    assert loaded is True
    assert os.getenv("PIXELA_USERNAME") == "test_user"
    assert os.getenv("PIXELA_TOKEN") == "secret_token"


def test_load_runtime_env(tmp_path, monkeypatch):
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (app_dir / ".env").write_text("APP_SETTING=app_val\n", encoding="utf-8")

    persistent_dir = tmp_path / "persist"
    persistent_dir.mkdir()
    (persistent_dir / ".env").write_text("PERSIST_SETTING=persist_val\n", encoding="utf-8")

    monkeypatch.delenv("APP_SETTING", raising=False)
    monkeypatch.delenv("PERSIST_SETTING", raising=False)

    loaded = load_runtime_env(app_dir=app_dir, persistent_root=persistent_dir)
    assert len(loaded) == 2
    assert os.getenv("APP_SETTING") == "app_val"
    assert os.getenv("PERSIST_SETTING") == "persist_val"
