"""Step 2 test: a terminal loop to exercise the translation core."""
import time

from config import load_key
from translator import QcTranslator

key = load_key()
if not key:
    raise SystemExit("No DeepL key: set DEEPL_AUTH_KEY or run app.py once to save one.")
t = QcTranslator(key)
print("Type English and press Enter. Ctrl+D to quit.")

while True:
    try:
        line = input("EN> ")
    except EOFError:
        break
    start = time.perf_counter()
    fr = t.translate(line)
    ms = (time.perf_counter() - start) * 1000
    print(f"FR> {fr}   ({ms:.0f} ms)")

usage = t.usage()
if usage:
    used, limit = usage
    print(f"\nQuota: {used:,} / {limit:,} characters this month")
