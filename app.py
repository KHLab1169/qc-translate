"""Step 5: scratchpad with first-run key setup, friendly errors and a quota meter."""
import sys

import deepl
from PySide6.QtCore import QEvent, QObject, QRunnable, Qt, QThreadPool, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from config import load_key, save_key
from translator import QcTranslator, friendly_error

if sys.platform.startswith("linux"):
    import kwin_pin  # KDE-only helper; not needed (or bundled) on Windows/macOS
else:
    kwin_pin = None

DEBOUNCE_MS = 400  # how long you must pause typing before we call DeepL
HINT = "Enter: copy  ·  Shift+Enter: new line  ·  Esc: clear"
WAYLAND_PIN_TIP = (
    "This desktop doesn't let apps pin themselves on top.\n"
    "Use your window menu's \"keep above\" option instead."
)


# --- Background jobs ----------------------------------------------------------

class JobSignals(QObject):
    """A worker thread can't touch the window directly; it sends signals instead."""
    done = Signal(int, str)    # (request id, French text)
    failed = Signal(int, str)  # (request id, error message)


class TranslateJob(QRunnable):
    """One DeepL call, run on a background thread so the window never freezes."""

    def __init__(self, translator: QcTranslator, request_id: int, text: str, register: str):
        super().__init__()
        self.translator = translator
        self.request_id = request_id
        self.text = text
        self.register = register
        self.signals = JobSignals()

    def run(self):
        try:
            french = self.translator.translate(self.text, self.register)
            self.signals.done.emit(self.request_id, french)
        except Exception as e:
            self.signals.failed.emit(self.request_id, friendly_error(e))


class UsageSignals(QObject):
    done = Signal(str)


class UsageJob(QRunnable):
    """Asks DeepL how much of this month's quota is used."""

    def __init__(self, translator: QcTranslator):
        super().__init__()
        self.translator = translator
        self.signals = UsageSignals()

    def run(self):
        try:
            usage = self.translator.usage()
            text = f"DeepL: {usage[0]:,} / {usage[1]:,}" if usage else ""
        except Exception:
            text = "DeepL: usage unavailable"
        self.signals.done.emit(text)


# --- Window --------------------------------------------------------------------

class Scratchpad(QWidget):
    def __init__(self, translator: QcTranslator):
        super().__init__()
        self.translator = translator
        self.request_id = 0           # increases with every request; used to spot stale replies
        self.waiting = False          # a request for the latest text is in flight
        self.copy_when_ready = False  # Enter was pressed before the French caught up

        # One worker thread for translations: they run one at a time, in order.
        self.pool = QThreadPool()
        self.pool.setMaxThreadCount(1)

        # --- Widgets ---
        self.setWindowTitle("QC Translate")
        self.resize(480, 340)

        self.register_box = QComboBox()
        self.register_box.addItem("tu (informel)", "tu")
        self.register_box.addItem("vous (formel)", "vous")
        self.register_box.currentIndexChanged.connect(self.translate_now)

        self.pin_box = QCheckBox("Always on top")
        self.pin_mode = self.pick_pin_mode()
        if self.pin_mode == "unsupported":
            # The request would be ignored, so don't offer a switch that does nothing.
            self.pin_box.setChecked(False)
            self.pin_box.setEnabled(False)
            self.pin_box.setToolTip(WAYLAND_PIN_TIP)
        else:
            self.pin_box.setChecked(True)
        self.pin_box.toggled.connect(self.set_pinned)  # connected after setup on purpose

        options = QHBoxLayout()
        options.addWidget(QLabel("Registre :"))
        options.addWidget(self.register_box)
        options.addStretch()
        options.addWidget(self.pin_box)

        self.english = QPlainTextEdit()
        self.english.setPlaceholderText("Type in English…")
        self.english.installEventFilter(self)  # lets us intercept Enter and Esc

        self.french = QPlainTextEdit()
        self.french.setReadOnly(True)
        self.french.setPlaceholderText("Le français apparaîtra ici…")

        self.status = QLabel(HINT)
        self.usage_label = QLabel("")
        self.usage_label.setStyleSheet("color: gray;")

        bottom = QHBoxLayout()
        bottom.addWidget(self.status)
        bottom.addStretch()
        bottom.addWidget(self.usage_label)

        layout = QVBoxLayout(self)
        layout.addLayout(options)
        layout.addWidget(self.english)
        layout.addWidget(self.french)
        layout.addLayout(bottom)

        if self.pin_mode == "qt":
            # Set before the window is first shown.
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self.pin_box.isChecked())
        elif self.pin_mode == "kwin":
            # KWin can only pin a window that's already on screen, so wait a moment.
            QTimer.singleShot(500, lambda: self.set_pinned(self.pin_box.isChecked()))

        # --- Debounce ---
        # Every keystroke restarts the timer. Only when you pause for
        # DEBOUNCE_MS does it fire and trigger a translation.
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(DEBOUNCE_MS)
        self.timer.timeout.connect(self.start_translation)
        self.english.textChanged.connect(self.timer.start)

        self.refresh_usage()

    # --- Keyboard handling ---------------------------------------------------

    def eventFilter(self, obj, event):
        """Sees every event for the English box before the box itself does."""
        if obj is self.english and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            shift = event.modifiers() & Qt.KeyboardModifier.ShiftModifier

            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if shift:
                    self.english.insertPlainText("\n")  # a real newline
                else:
                    self.copy_french()
                return True  # handled: the box never sees this key

            if key == Qt.Key.Key_Escape:
                self.english.clear()
                return True

        return super().eventFilter(obj, event)

    # --- Translation ---------------------------------------------------------

    def translate_now(self):
        """Skip the debounce wait (used when the tu/vous choice changes)."""
        self.timer.stop()
        self.start_translation()

    def start_translation(self):
        text = self.english.toPlainText()
        self.request_id += 1  # any reply still in flight is now out of date

        if not text.strip():
            self.french.clear()
            self.waiting = False
            self.copy_when_ready = False
            self.status.setText(HINT)
            return

        self.waiting = True
        self.status.setText("Translating…")
        register = self.register_box.currentData()
        job = TranslateJob(self.translator, self.request_id, text, register)
        job.signals.done.connect(self.show_translation)
        job.signals.failed.connect(self.show_error)
        self.pool.clear()  # drop any older request still waiting its turn
        self.pool.start(job)

    def show_translation(self, request_id: int, french: str):
        if request_id != self.request_id:
            return  # stale: you kept typing after this request went out
        self.waiting = False
        self.french.setPlainText(french)
        if self.copy_when_ready:
            self.copy_when_ready = False
            self.copy_to_clipboard()
        else:
            self.status.setText(HINT)

    def show_error(self, request_id: int, message: str):
        if request_id != self.request_id:
            return
        self.waiting = False
        self.copy_when_ready = False
        self.status.setText(f"⚠ {message}")

    # --- Copy, pin and quota -------------------------------------------------

    def copy_french(self):
        """Enter pressed. If the French is behind your typing, catch up first."""
        if self.timer.isActive() or self.waiting:
            self.copy_when_ready = True
            self.status.setText("Translating… will copy when ready")
            if self.timer.isActive():
                self.translate_now()  # don't make you wait out the debounce
            return
        self.copy_to_clipboard()

    def copy_to_clipboard(self):
        french = self.french.toPlainText()
        if not french:
            return
        QApplication.clipboard().setText(french)
        self.status.setText("Copied ✓  ·  paste it anywhere")
        self.refresh_usage()

    def refresh_usage(self):
        job = UsageJob(self.translator)
        job.signals.done.connect(self.usage_label.setText)
        # The shared global pool, so pool.clear() above can never cancel it.
        QThreadPool.globalInstance().start(job)

    @staticmethod
    def pick_pin_mode() -> str:
        if QApplication.platformName() != "wayland":
            return "qt"           # Windows, macOS, X11: Qt's own flag works
        if kwin_pin and kwin_pin.available():
            return "kwin"         # KDE Plasma on Wayland: ask KWin directly
        return "unsupported"      # other Wayland desktops

    def set_pinned(self, pinned: bool):
        if self.pin_mode == "kwin":
            if not kwin_pin.set_keep_above(pinned):
                self.status.setText("⚠ KDE didn't accept the pin request")
            return
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, pinned)
        self.show()  # changing window flags hides the window; show it again


# --- Startup -------------------------------------------------------------------

def get_translator() -> QcTranslator | None:
    """Use the saved key, or ask for one on first run. None means the user gave up."""
    key = load_key()
    if key:
        return QcTranslator(key)

    prompt = "Paste your DeepL API key\n(a free key ends in :fx):"
    while True:
        key, ok = QInputDialog.getText(
            None, "QC Translate · setup", prompt, QLineEdit.EchoMode.Password
        )
        if not ok:
            return None  # Cancel pressed
        key = key.strip()
        if not key:
            continue

        translator = QcTranslator(key)
        try:
            translator.usage()  # quick call that fails on a bad key
        except deepl.AuthorizationException:
            prompt = "DeepL rejected that key. Try again:"
            continue
        except Exception as e:
            prompt = f"{friendly_error(e)}\nTry again:"
            continue

        try:
            path = save_key(key)
        except OSError:
            QMessageBox.warning(
                None, "QC Translate",
                "The key works, but it couldn't be saved.\nYou'll be asked again next time.",
            )
            return translator
        QMessageBox.information(None, "QC Translate", f"Key saved to:\n{path}")
        return translator


def main():
    app = QApplication(sys.argv)
    translator = get_translator()
    if translator is None:
        return  # no key, nothing to do
    window = Scratchpad(translator)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
