"""Behaviour tests for the window (app.py), driven like a user would.

pytest-qt's `qtbot` types into the window and waits for results. The real
DeepL client is replaced by FakeTranslator, so nothing goes over the network.
"""
import deepl
import pytest
from PySide6.QtCore import QThreadPool, Qt
from PySide6.QtWidgets import QApplication

import app

WAIT_MS = 3000  # generous: CI machines can be slow


class FakeTranslator:
    """Stands in for QcTranslator: same methods, predictable answers."""

    def __init__(self):
        self.calls = []   # (text, register) for every translate() call
        self.error = None

    def translate(self, text, register="tu"):
        if self.error:
            raise self.error
        self.calls.append((text, register))
        return f"FR-{register}: {text.strip()}"

    def usage(self):
        return 1_234, 500_000


@pytest.fixture
def fake():
    return FakeTranslator()


@pytest.fixture
def window(qtbot, fake):
    w = app.Scratchpad(fake)
    qtbot.addWidget(w)
    w.show()
    yield w
    # Let background jobs finish before the window is destroyed.
    w.pool.waitForDone(WAIT_MS)
    QThreadPool.globalInstance().waitForDone(WAIT_MS)


def type_text(window, text):
    window.english.setPlainText(text)


def wait_for_french(qtbot, window, expected):
    qtbot.waitUntil(lambda: window.french.toPlainText() == expected, timeout=WAIT_MS)


# --- Translating ---------------------------------------------------------------

def test_pausing_after_typing_shows_the_french(qtbot, window):
    type_text(window, "Hello")
    wait_for_french(qtbot, window, "FR-tu: Hello")
    assert window.status.text() == app.HINT


def test_fast_typing_sends_only_one_request(qtbot, window, fake):
    # Each keystroke restarts the debounce timer, so only the last text goes out.
    for partial in ["H", "He", "Hel", "Hell", "Hello"]:
        type_text(window, partial)
    wait_for_french(qtbot, window, "FR-tu: Hello")
    assert fake.calls == [("Hello", "tu")]


def test_switching_to_vous_retranslates_immediately(qtbot, window, fake):
    type_text(window, "Can you help me?")
    wait_for_french(qtbot, window, "FR-tu: Can you help me?")
    vous = next(b for b in window.register_group.buttons() if b.property("register") == "vous")
    vous.click()
    wait_for_french(qtbot, window, "FR-vous: Can you help me?")
    assert fake.calls[-1] == ("Can you help me?", "vous")


def test_clearing_the_text_clears_the_french(qtbot, window):
    type_text(window, "Hello")
    wait_for_french(qtbot, window, "FR-tu: Hello")
    type_text(window, "   ")
    wait_for_french(qtbot, window, "")


def test_stale_reply_is_ignored(window):
    # A reply for an older request must never overwrite newer French.
    window.french.setPlainText("current")
    window.show_translation(window.request_id - 1, "old reply")
    assert window.french.toPlainText() == "current"


# --- Errors ----------------------------------------------------------------------

def test_network_error_shows_a_plain_message(qtbot, window, fake):
    fake.error = deepl.ConnectionException("offline")
    type_text(window, "Hello")
    qtbot.waitUntil(lambda: "Can't reach DeepL" in window.status.text(), timeout=WAIT_MS)
    assert window.status.property("state") == "error"


# --- Keyboard ---------------------------------------------------------------------

def test_enter_copies_the_french(qtbot, window):
    type_text(window, "See you this weekend")
    wait_for_french(qtbot, window, "FR-tu: See you this weekend")
    qtbot.keyClick(window.english, Qt.Key.Key_Return)
    assert QApplication.clipboard().text() == "FR-tu: See you this weekend"
    assert window.status.text().startswith("Copied")


def test_enter_before_translation_arrives_copies_when_ready(qtbot, window):
    QApplication.clipboard().clear()
    type_text(window, "Good morning")
    qtbot.keyClick(window.english, Qt.Key.Key_Return)  # pressed during the debounce wait
    qtbot.waitUntil(lambda: QApplication.clipboard().text() == "FR-tu: Good morning",
                    timeout=WAIT_MS)


def test_shift_enter_adds_a_new_line_without_copying(qtbot, window):
    QApplication.clipboard().clear()
    window.english.setFocus()
    qtbot.keyClick(window.english, Qt.Key.Key_Return, Qt.KeyboardModifier.ShiftModifier)
    assert window.english.toPlainText() == "\n"
    assert QApplication.clipboard().text() == ""


def test_escape_clears_both_boxes(qtbot, window):
    type_text(window, "Hello")
    wait_for_french(qtbot, window, "FR-tu: Hello")
    qtbot.keyClick(window.english, Qt.Key.Key_Escape)
    assert window.english.toPlainText() == ""
    wait_for_french(qtbot, window, "")


# --- Quota -------------------------------------------------------------------------

def test_quota_label_shows_usage(qtbot, window):
    qtbot.waitUntil(lambda: window.usage_label.text() != "", timeout=WAIT_MS)
    assert window.usage_label.text() == "Under 1% of quota used"
    assert window.usage_label.toolTip() == "1,234 of 500,000 characters this month"
