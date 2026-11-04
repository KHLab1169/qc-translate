"""QC Translate: type English, get Quebec French. Enter copies it."""
import sys

import deepl
from PySide6.QtCore import QEvent, QObject, QRunnable, Qt, QThreadPool, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import theme
from config import load_key, save_key
from translator import QcTranslator, friendly_error

if sys.platform.startswith("linux"):
    import kwin_pin  # KDE-only helper; not needed (or bundled) on Windows/macOS
else:
    kwin_pin = None

DEBOUNCE_MS = 400  # how long you must pause typing before we call DeepL
HINT = "Enter copies the French. Esc clears."
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
    done = Signal(str, str)  # (short label, exact numbers for the tooltip)


class UsageJob(QRunnable):
    """Asks DeepL how much of this month's quota is used."""

    def __init__(self, translator: QcTranslator):
        super().__init__()
        self.translator = translator
        self.signals = UsageSignals()

    def run(self):
        try:
            usage = self.translator.usage()
        except Exception:
            self.signals.done.emit("Quota unavailable", "")
            return
        if not usage:
            self.signals.done.emit("", "")
            return
        used, limit = usage
        pct = used / limit * 100
        short = "Under 1% of quota used" if pct < 1 else f"{pct:.0f}% of quota used"
        self.signals.done.emit(short, f"{used:,} of {limit:,} characters this month")


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

        self.setObjectName("root")  # the stylesheet targets widgets by these names
        self.setWindowTitle("QC Translate")
        self.resize(520, 400)
        self.setMinimumSize(380, 300)

        # --- Header: "English" on the left, tu|vous and Keep on top on the right ---
        english_label = QLabel("English")
        english_label.setProperty("role", "caption")

        self.register_group = QButtonGroup(self)  # exclusive: one segment at a time
        segmented = QFrame()
        segmented.setObjectName("segmented")
        seg_layout = QHBoxLayout(segmented)
        seg_layout.setContentsMargins(2, 2, 2, 2)
        seg_layout.setSpacing(2)
        for value, tip in (("tu", "Informal"), ("vous", "Formal")):
            button = QPushButton(value)
            button.setCheckable(True)
            button.setToolTip(tip)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setProperty("register", value)
            self.register_group.addButton(button)
            seg_layout.addWidget(button)
        self.register_group.buttons()[0].setChecked(True)
        self.register_group.buttonToggled.connect(self.on_register_toggled)

        self.pin_box = QPushButton("Keep on top")
        self.pin_box.setObjectName("pin")
        self.pin_box.setCheckable(True)
        self.pin_box.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pin_mode = self.pick_pin_mode()
        if self.pin_mode == "unsupported":
            # The request would be ignored, so don't offer a switch that does nothing.
            self.pin_box.setChecked(False)
            self.pin_box.setEnabled(False)
            self.pin_box.setToolTip(WAYLAND_PIN_TIP)
        else:
            self.pin_box.setChecked(True)
        self.pin_box.toggled.connect(self.set_pinned)  # connected after setup on purpose

        header = QHBoxLayout()
        header.addWidget(english_label)
        header.addStretch()
        header.addWidget(segmented)
        header.addSpacing(6)
        header.addWidget(self.pin_box)

        # --- The two text panes ---
        self.english = QPlainTextEdit()
        self.english.setObjectName("english")
        self.english.setPlaceholderText("Type in English…  (Shift+Enter for a new line)")
        self.english.installEventFilter(self)  # lets us intercept Enter and Esc

        french_label = QLabel("Français (Québec)")
        french_label.setProperty("role", "caption")

        self.french = QPlainTextEdit()
        self.french.setObjectName("french")
        self.french.setReadOnly(True)
        self.french.setPlaceholderText("Le français apparaîtra ici…")

        # --- Footer: hint or status on the left, quota on the right ---
        self.status = QLabel(HINT)
        self.status.setObjectName("status")
        self.usage_label = QLabel("")
        self.usage_label.setObjectName("usage")

        footer = QHBoxLayout()
        footer.addWidget(self.status, 1)
        footer.addWidget(self.usage_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 12)
        layout.setSpacing(8)
        layout.addLayout(header)
        layout.addWidget(self.english, 1)
        layout.addSpacing(4)
        layout.addWidget(french_label)
        layout.addWidget(self.french, 1)
        layout.addLayout(footer)

        self.apply_theme()
        QApplication.styleHints().colorSchemeChanged.connect(self.apply_theme)

        if self.pin_mode == "qt":
            # Set before the window is first shown.
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self.pin_box.isChecked())
        elif self.pin_mode == "kwin":
            # KWin can only pin a window that's already on screen, so wait a moment.
            QTimer.singleShot(500, self, lambda: self.set_pinned(self.pin_box.isChecked()))

        # --- Debounce ---
        # Every keystroke restarts the timer. Only when you pause for
        # DEBOUNCE_MS does it fire and trigger a translation.
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(DEBOUNCE_MS)
        self.timer.timeout.connect(self.start_translation)
        self.english.textChanged.connect(self.timer.start)

        self.refresh_usage()

    # --- Look and feel -------------------------------------------------------

    def apply_theme(self, *_):
        """Called at startup and whenever the system switches light/dark."""
        self.setStyleSheet(theme.stylesheet())
        t = theme.tokens()
        theme.set_placeholder(self.english, t["muted"])
        theme.set_placeholder(self.french, t["panel_hint"])

    def set_state(self, widget: QWidget, name: str, value: str):
        """Change a property the stylesheet reacts to, then make Qt re-read the styles."""
        widget.setProperty(name, value)
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def show_status(self, text: str, error: bool = False):
        self.status.setText(text)
        self.set_state(self.status, "state", "error" if error else "")

    def flash_copied(self):
        """Brief lighter flash on the French panel: visible proof the copy happened."""
        self.set_state(self.french, "copied", "true")
        # Passing self.french as the context ties the timer to the panel: if the
        # window closes before it fires, Qt cancels it instead of touching a deleted widget.
        QTimer.singleShot(450, self.french, lambda: self.set_state(self.french, "copied", "false"))

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

    def current_register(self) -> str:
        return self.register_group.checkedButton().property("register")

    def on_register_toggled(self, button, checked: bool):
        if checked:  # fires for both buttons; act once, for the newly chosen one
            self.translate_now()
            self.english.setFocus()

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
            self.show_status(HINT)
            return

        self.waiting = True
        self.show_status("Translating…")
        job = TranslateJob(self.translator, self.request_id, text, self.current_register())
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
            self.show_status(HINT)

    def show_error(self, request_id: int, message: str):
        if request_id != self.request_id:
            return
        self.waiting = False
        self.copy_when_ready = False
        self.show_status(message, error=True)

    # --- Copy, pin and quota -------------------------------------------------

    def copy_french(self):
        """Enter pressed. If the French is behind your typing, catch up first."""
        if self.timer.isActive() or self.waiting:
            self.copy_when_ready = True
            self.show_status("Translating… it will copy when ready.")
            if self.timer.isActive():
                self.translate_now()  # don't make you wait out the debounce
            return
        self.copy_to_clipboard()

    def copy_to_clipboard(self):
        french = self.french.toPlainText()
        if not french:
            return
        QApplication.clipboard().setText(french)
        self.show_status("Copied. Paste it anywhere.")
        self.flash_copied()
        self.refresh_usage()

    def refresh_usage(self):
        job = UsageJob(self.translator)
        job.signals.done.connect(self.show_usage)
        # The shared global pool, so pool.clear() above can never cancel it.
        QThreadPool.globalInstance().start(job)

    def show_usage(self, short: str, detail: str):
        self.usage_label.setText(short)
        self.usage_label.setToolTip(detail)

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
                self.show_status("KDE didn't accept the request to keep the window on top.", error=True)
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
            None, "QC Translate setup", prompt, QLineEdit.EchoMode.Password
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
    # Fusion is Qt's own neutral style: the stylesheet then looks the same
    # on Windows, macOS and KDE instead of mixing with each system's theme.
    app.setStyle("Fusion")
    translator = get_translator()
    if translator is None:
        return  # no key, nothing to do
    window = Scratchpad(translator)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
