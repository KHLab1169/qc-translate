"""Tests for where the DeepL key is read from and saved to (config.py)."""
import sys
from pathlib import Path

import pytest

import config


@pytest.fixture
def folders(tmp_path, monkeypatch):
    """Point the app folder and user folder at empty temp folders."""
    app = tmp_path / "usb-stick"
    user = tmp_path / "user-config" / "qc-translate"
    app.mkdir()
    monkeypatch.setattr(config, "app_dir", lambda: app)
    monkeypatch.setattr(config, "user_dir", lambda: user)
    monkeypatch.delenv("DEEPL_AUTH_KEY", raising=False)
    return app, user


def write_ini(folder: Path, key: str):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / config.CONFIG_NAME).write_text(f"[deepl]\nauth_key = {key}\n", encoding="utf-8")


# --- Reading the key -----------------------------------------------------------

def test_no_key_anywhere(folders):
    assert config.load_key() is None


def test_environment_variable_wins(folders, monkeypatch):
    app, _ = folders
    write_ini(app, "from-file")
    monkeypatch.setenv("DEEPL_AUTH_KEY", "  from-env  ")
    assert config.load_key() == "from-env"


def test_reads_key_beside_the_app(folders):
    app, _ = folders
    write_ini(app, "usb-key:fx")
    assert config.load_key() == "usb-key:fx"


def test_app_folder_beats_user_folder(folders):
    app, user = folders
    write_ini(app, "usb-key")
    write_ini(user, "machine-key")
    assert config.load_key() == "usb-key"


def test_falls_back_to_user_folder(folders):
    _, user = folders
    write_ini(user, "machine-key")
    assert config.load_key() == "machine-key"


def test_blank_key_in_file_is_skipped(folders):
    app, user = folders
    write_ini(app, "   ")
    write_ini(user, "machine-key")
    assert config.load_key() == "machine-key"


# --- Saving the key ------------------------------------------------------------

def test_save_then_load_round_trip(folders):
    app, _ = folders
    path = config.save_key("  abc123:fx  ")
    assert path == app / config.CONFIG_NAME
    assert config.load_key() == "abc123:fx"  # stored without the spaces


def test_percent_sign_is_kept_literally(folders):
    # configparser treats "%" as special by default; the app turns that off.
    config.save_key("ab%cd%%ef")
    assert config.load_key() == "ab%cd%%ef"


def test_save_falls_back_when_app_folder_is_not_writable(tmp_path, monkeypatch):
    # A *file* where a folder should be makes saving there fail on every OS.
    blocker = tmp_path / "read-only-stick"
    blocker.write_text("not a folder")
    good = tmp_path / "user" / config.CONFIG_NAME
    monkeypatch.setattr(config, "candidate_files",
                        lambda: [blocker / "sub" / config.CONFIG_NAME, good])
    assert config.save_key("k") == good
    assert good.is_file()


def test_save_raises_when_nowhere_is_writable(tmp_path, monkeypatch):
    blocker = tmp_path / "blocker"
    blocker.write_text("not a folder")
    monkeypatch.setattr(config, "candidate_files",
                        lambda: [blocker / "a" / config.CONFIG_NAME,
                                 blocker / "b" / config.CONFIG_NAME])
    with pytest.raises(OSError):
        config.save_key("k")


# --- Folder locations ----------------------------------------------------------

def test_candidates_are_app_folder_then_user_folder(folders):
    app, user = folders
    assert config.candidate_files() == [app / config.CONFIG_NAME, user / config.CONFIG_NAME]


def test_running_as_script_uses_project_folder(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert config.app_dir() == Path(config.__file__).resolve().parent


def test_packaged_mac_app_uses_folder_holding_the_app(monkeypatch, tmp_path):
    exe = tmp_path / "USB" / "QC Translate.app" / "Contents" / "MacOS" / "QC Translate"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe))
    monkeypatch.setattr(sys, "platform", "darwin")
    assert config.app_dir() == (tmp_path / "USB").resolve()


def test_packaged_windows_app_uses_exe_folder(monkeypatch, tmp_path):
    exe = tmp_path / "USB" / "QC Translate" / "QC Translate.exe"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe))
    monkeypatch.setattr(sys, "platform", "win32")
    assert config.app_dir() == exe.parent.resolve()


def test_user_folder_on_windows(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
    assert config.user_dir() == tmp_path / "Roaming" / "qc-translate"


def test_user_folder_on_mac(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    assert config.user_dir() == Path.home() / "Library" / "Application Support" / "qc-translate"


def test_user_folder_on_linux_follows_xdg(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    assert config.user_dir() == tmp_path / "xdg" / "qc-translate"


def test_user_folder_on_linux_defaults_to_dot_config(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    assert config.user_dir() == Path.home() / ".config" / "qc-translate"
