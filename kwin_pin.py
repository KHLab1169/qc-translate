"""Keep-on-top for KDE Plasma on Wayland, using KWin's built-in scripting.

Wayland doesn't let an app pin itself, but KDE's window manager (KWin) accepts
small JavaScript snippets over D-Bus. We send one that finds our window by its
process ID and sets keepAbove. Nothing extra to install: Qt already speaks D-Bus.
"""
import os
import tempfile

from PySide6.QtCore import QTimer
from PySide6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage

SERVICE = "org.kde.KWin"
PLUGIN_NAME = f"qc-translate-pin-{os.getpid()}"
SCRIPT_PATH = os.path.join(tempfile.gettempdir(), f"{PLUGIN_NAME}.js")

# Plasma 6 calls it windowList(), Plasma 5 called it clientList().
SCRIPT = """
const windows = workspace.windowList ? workspace.windowList() : workspace.clientList();
for (const w of windows) {
    if (w.pid === %d) {
        w.keepAbove = %s;
    }
}
"""


def _scripting() -> QDBusInterface:
    return QDBusInterface(SERVICE, "/Scripting", "org.kde.kwin.Scripting",
                          QDBusConnection.sessionBus())


def available() -> bool:
    """True when we're on KDE Plasma and KWin's scripting interface answers."""
    return QDBusConnection.sessionBus().isConnected() and _scripting().isValid()


def _cleanup():
    _scripting().call("unloadScript", PLUGIN_NAME)
    try:
        os.remove(SCRIPT_PATH)
    except OSError:
        pass


def set_keep_above(keep: bool) -> bool:
    """Ask KWin to pin (or unpin) this app's window. Returns False on failure."""
    with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(SCRIPT % (os.getpid(), "true" if keep else "false"))

    scripting = _scripting()
    scripting.call("unloadScript", PLUGIN_NAME)  # clear any earlier run
    reply = scripting.call("loadScript", SCRIPT_PATH, PLUGIN_NAME)
    if reply.type() == QDBusMessage.MessageType.ErrorMessage or not reply.arguments():
        return False
    script_id = reply.arguments()[0]

    # Loading only registers the script; it has to be told to run.
    # The object path differs between Plasma versions, so try both.
    ran = False
    for path in (f"/Scripting/Script{script_id}", f"/{script_id}"):
        script = QDBusInterface(SERVICE, path, "org.kde.kwin.Script",
                                QDBusConnection.sessionBus())
        if script.isValid():
            ran = script.call("run").type() != QDBusMessage.MessageType.ErrorMessage
            break

    # KWin reads the file in the background, so tidy up a moment later.
    QTimer.singleShot(2000, _cleanup)
    return ran
