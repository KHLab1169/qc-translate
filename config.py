"""Where the app keeps its DeepL key.

Search order:
  1. DEEPL_AUTH_KEY environment variable (handy while developing)
  2. qc-translate.ini next to the app      (the USB stick)
  3. qc-translate.ini in the user's config folder on this machine (fallback)
"""
import configparser
import os
import sys
from pathlib import Path

CONFIG_NAME = "qc-translate.ini"


def app_dir() -> Path:
    """The folder the app lives in: the USB stick once packaged."""
    if getattr(sys, "frozen", False):  # True when running as a packaged app
        exe = Path(sys.executable).resolve()
        # On macOS the executable sits inside "QC Translate.app/Contents/MacOS/",
        # so climb out of the bundle to the folder that holds the .app.
        if sys.platform == "darwin" and exe.parent.name == "MacOS":
            return exe.parents[3]
        return exe.parent
    return Path(__file__).resolve().parent  # running as a script: the project folder


def user_dir() -> Path:
    """This machine's per-user settings folder, the normal place for each OS."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "qc-translate"


def candidate_files() -> list[Path]:
    return [app_dir() / CONFIG_NAME, user_dir() / CONFIG_NAME]


def _parser() -> configparser.ConfigParser:
    # interpolation=None: treat values literally, so a "%" can never be misread
    return configparser.ConfigParser(interpolation=None)


def load_key() -> str | None:
    env = os.environ.get("DEEPL_AUTH_KEY", "").strip()
    if env:
        return env
    for path in candidate_files():
        if path.is_file():
            cp = _parser()
            cp.read(path, encoding="utf-8")
            key = cp.get("deepl", "auth_key", fallback="").strip()
            if key:
                return key
    return None


def save_key(key: str) -> Path:
    """Save beside the app if that folder is writable, else in the user folder."""
    cp = _parser()
    cp["deepl"] = {"auth_key": key.strip()}
    for path in candidate_files():
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                cp.write(f)
            return path
        except OSError:
            continue  # read-only location; try the next one
    raise OSError("Couldn't save the key to any settings location.")
