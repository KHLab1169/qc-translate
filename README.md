# QC Translate

[![Tests](https://github.com/KHLab1169/qc-translate/actions/workflows/tests.yml/badge.svg)](https://github.com/KHLab1169/qc-translate/actions/workflows/tests.yml)

A small desktop app that translates English into **Quebec French** as you type.
Type in the top box, pause, and the Québécois translation appears below.
Press Enter to copy it, then paste it wherever you need it.

It runs from a USB stick on Windows and macOS with nothing to install, and on
Linux from your own drive.

Translations come from [DeepL](https://www.deepl.com/pro-api) using its Canadian
French (`fr-CA`) target, so you get *fin de semaine* and *courriel*, not
*week-end* and *e-mail*.

## Features

- **Live translation.** It translates once you pause typing, not on every
  keystroke, which keeps it fast and saves quota.
- **tu or vous.** One click switches between informal and formal French.
- **Keep on top.** The window can stay above your other windows while you work.
  On KDE Plasma under Wayland, the button asks KDE to do this.
- **Light and dark mode.** It follows your system setting by default.
- **Plain-language errors** for no internet, a rejected key, or a used-up quota.
- **Quota meter.** Shows how much of your monthly DeepL allowance you've used.
  Hover over it for the exact count.

## Keyboard shortcuts

| Key | What it does |
|---|---|
| Enter | Copies the French. If a translation is still on its way, it copies as soon as it arrives. |
| Shift+Enter | Adds a new line |
| Esc | Clears both boxes |

## Using it from a USB stick

The stick holds one copy for each system:

```
USB stick/
├── Windows/
│   └── QC Translate/
│       ├── QC Translate.exe
│       └── _internal/
└── QC-Translate-Mac.dmg
```

**Windows:** open `Windows\QC Translate` and run `QC Translate.exe`. If Windows
shows "Windows protected your PC", choose **More info → Run anyway**.

**Mac:** double-click `QC-Translate-Mac.dmg`, then open the app inside.
If macOS says it can't verify the developer, right-click the app and choose
**Open** (macOS 14 and older), or go to **System Settings → Privacy & Security**
and click **Open Anyway** (macOS 15 and newer).
**Eject the "QC Translate" drive in Finder before unplugging the stick.**

The Mac build is for Apple Silicon (M1 and newer).

### Your DeepL key

The first time you open the app, it asks for a DeepL API key. A free key works
and ends in `:fx`. You can get one at [deepl.com/pro-api](https://www.deepl.com/pro-api).

The app checks the key with DeepL, then saves it in a file called
`qc-translate.ini` next to the app. On the stick, that means you enter it once
per system: once for Windows, once inside the Mac disk image.

It looks for the key in this order:

1. the `DEEPL_AUTH_KEY` environment variable
2. `qc-translate.ini` next to the app
3. `qc-translate.ini` in your settings folder on this computer
   (`%APPDATA%\qc-translate`, `~/Library/Application Support/qc-translate`
   or `~/.config/qc-translate`)

The key is stored as plain text, so anyone with the stick can read it. If you
lose the stick, delete the key in your DeepL account and create a new one.

## Privacy

Everything you type in the English box is sent to DeepL to be translated.
Nothing else leaves your computer. The app does not watch your keyboard
outside its own window.

## Running from source

You need Python 3.10 or newer.

```bash
git clone https://github.com/KHLab1169/qc-translate.git
cd qc-translate
python -m venv .venv
source .venv/bin/activate          # fish: source .venv/bin/activate.fish
                                   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

`try_translator.py` is a small terminal test for the translation part on its own.

## Running the tests

The tests use [pytest](https://pytest.org) and
[pytest-qt](https://pytest-qt.readthedocs.io). A fake DeepL client stands in
for the real one, so they need no key, no internet and use no quota.

```bash
pip install -r requirements-dev.txt
python -m pytest
```

| Test file | What it checks |
|---|---|
| `tests/test_translator.py` | Requests use Canadian French and the right tu/vous setting; caching; quota; error messages |
| `tests/test_config.py` | Where the key is read from and saved to on each system, including the USB stick |
| `tests/test_theme.py` | Every accent has valid colours for light and dark mode, and the stylesheet builds |
| `tests/test_app.py` | The window: live translation, typing pauses, Enter to copy, Esc to clear, error messages |

GitHub runs the same tests on Windows, macOS and Linux after every push
(`.github/workflows/tests.yml`). The badge at the top of this page shows the
latest result.

## Building

[PyInstaller](https://pyinstaller.org) turns the app into a folder you can run
without Python. It can only build for the system it runs on.

**Linux** (on your own machine):

```bash
pyinstaller --noconfirm --windowed --name "QC Translate" app.py
```

The result is in `dist/QC Translate/`. Rebuilding wipes `dist`, so copy the
folder somewhere else if you want to keep it. The Linux build has to run from a
Linux drive; FAT32 and exFAT sticks won't run it.

**Windows and macOS** are built by GitHub Actions
(`.github/workflows/build.yml`). Start a build from the **Actions** tab with
**Run workflow**, or push a tag such as `v1.0`. When it finishes, download the
results:

```bash
gh run download --dir ~/qc-builds
```

`gh` won't overwrite earlier downloads, so delete `~/qc-builds` first if it
already exists. That gives you `QC-Translate-Windows.zip` and
`QC-Translate-Mac.dmg`. The Mac
version comes as a disk image because FAT32 and exFAT sticks can't store some
of the files inside a Mac app.

## Changing the look

The colours live in `theme.py`. Two settings at the top control them:

```python
ACCENT = "fleuve"   # "quebec", "fleuve", "verte", "sirop" or "aubergine"
MODE = "auto"       # "auto" follows the system; "dark" or "light" forces one
```

| Accent | Inspired by |
|---|---|
| `quebec` | the blue of the Québec flag |
| `fleuve` | the St. Lawrence river |
| `verte` | the métro's green line |
| `sirop` | maple syrup |
| `aubergine` | deep plum |

## Project layout

| File | What it does |
|---|---|
| `app.py` | The window: typing, translating in the background, copying, keep on top |
| `translator.py` | Talks to DeepL, caches recent translations, turns errors into plain messages |
| `config.py` | Finds, checks and saves your DeepL key |
| `theme.py` | Colours and styling for light and dark mode |
| `kwin_pin.py` | Keep on top for KDE Plasma under Wayland (Linux only) |
| `try_translator.py` | Terminal test for `translator.py` |
| `requirements.txt` | Exact library versions used for every build |
| `requirements-dev.txt` | Adds the test tools (pytest, pytest-qt) |
| `tests/` | Automated tests |
| `.github/workflows/tests.yml` | Runs the tests on Windows, macOS and Linux on GitHub |
| `.github/workflows/build.yml` | Builds the Windows and Mac versions on GitHub |

## Known limits

- **Keep on top** works on Windows, macOS, Linux under X11, and KDE Plasma under
  Wayland. On other Wayland desktops, such as GNOME, the button is greyed out;
  use your window menu's "keep above" option instead.
- **Intel Macs** aren't built yet. Only Apple Silicon is.
- **Work computers** may block programs that run from a USB stick.
