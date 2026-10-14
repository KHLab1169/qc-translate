#!/usr/bin/env python3
"""
frtrans_portable.py — portable EN→FR hotkey translator (Windows / macOS / Linux-X11).

Run it, leave it in the background. Select English text in any app,
press Ctrl+Alt+F (same on Mac), and the selection is replaced with French.

Usage:
    frtrans_portable.py --setup    # one-time: download EN->FR model to ../models
    frtrans_portable.py            # start the hotkey listener
    frtrans_portable.py --stdin    # translate stdin -> stdout (testing)

Designed to be built with PyInstaller and run from a USB stick:
    USB/
      frtrans-win/   frtrans.exe       (built on Windows)
      frtrans-mac/   frtrans           (built on macOS)
      frtrans-linux/ frtrans           (built on Linux)
      models/                          (shared, created by --setup)
"""

import argparse
import os
import sys
import threading
import time
from pathlib import Path

HOTKEY = "<ctrl>+<alt>+f"
IS_MAC = sys.platform == "darwin"

# ---------------------------------------------------------------- paths
# Models live in a "models" folder NEXT TO the build folder, shared by all OSes.
if getattr(sys, "frozen", False):          # running as a PyInstaller build
    APP_DIR = Path(sys.executable).resolve().parent
else:                                      # running as a plain script
    APP_DIR = Path(__file__).resolve().parent

MODELS_DIR = APP_DIR.parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Point Argos at the USB before importing it.
os.environ["ARGOS_PACKAGES_DIR"] = str(MODELS_DIR / "packages")
os.environ["XDG_DATA_HOME"] = str(MODELS_DIR / "data")
os.environ["XDG_CACHE_HOME"] = str(MODELS_DIR / "cache")

FROM_CODE, TO_CODE = "en", "fr"


# ---------------------------------------------------------------- translation
def ensure_model():
    import argostranslate.package

    print("Fetching package index...")
    argostranslate.package.update_package_index()
    pkg = next(
        (p for p in argostranslate.package.get_available_packages()
         if p.from_code == FROM_CODE and p.to_code == TO_CODE),
        None,
    )
    if pkg is None:
        sys.exit("en→fr package not found in Argos index.")
    print(f"Downloading {pkg} into {MODELS_DIR} ...")
    argostranslate.package.install_from_path(pkg.download())
    print("Done. The models folder is now shared by all OS builds on this stick.")


def load_translator():
    """Load the model once at startup so hotkey presses are fast."""
    import argostranslate.translate

    langs = argostranslate.translate.get_installed_languages()
    src = next((l for l in langs if l.code == FROM_CODE), None)
    dst = next((l for l in langs if l.code == TO_CODE), None)
    if not src or not dst:
        sys.exit("Model not installed. Run with --setup first (needs internet once).")
    return src.get_translation(dst)


# ---------------------------------------------------------------- clipboard/keys
def make_hotkey_handler(translation):
    import pyperclip
    from pynput import keyboard

    kb = keyboard.Controller()
    mod = keyboard.Key.cmd if IS_MAC else keyboard.Key.ctrl
    busy = threading.Lock()

    def send(char):
        with kb.pressed(mod):
            kb.press(char)
            kb.release(char)

    def work():
        if not busy.acquire(blocking=False):
            return  # ignore re-triggers while translating
        try:
            time.sleep(0.30)          # let the user release Ctrl+Alt+F
            before = pyperclip.paste()
            pyperclip.copy("")        # so we can tell if copy worked
            send("c")                 # copy current selection
            time.sleep(0.30)
            text = pyperclip.paste().strip()
            if not text:
                pyperclip.copy(before)
                print("[!] Nothing selected.")
                return
            french = translation.translate(text)
            pyperclip.copy(french)
            time.sleep(0.10)
            send("v")                 # paste over the selection
            print(f"EN: {text}\nFR: {french}\n" + "-" * 40)
        except Exception as e:
            print(f"[!] Error: {e}")
        finally:
            busy.release()

    def on_hotkey():
        threading.Thread(target=work, daemon=True).start()

    return keyboard.GlobalHotKeys({HOTKEY: on_hotkey})


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--setup", action="store_true")
    ap.add_argument("--stdin", action="store_true")
    args = ap.parse_args()

    if args.setup:
        ensure_model()
        return

    translation = load_translator()

    if args.stdin:
        print(translation.translate(sys.stdin.read().strip()))
        return

    print(f"Model loaded. Listening for {HOTKEY} — select text, press it, done.")
    print("Keep this window open (minimize it). Ctrl+C here to quit.")
    listener = make_hotkey_handler(translation)
    listener.start()
    try:
        listener.join()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
