"""Look and feel: colour tokens plus a Qt stylesheet built from them.

Qt stylesheets (QSS) work like CSS for desktop widgets. Keeping every colour in
one dictionary per mode ("tokens") means light and dark mode share one stylesheet,
and a colour change happens in exactly one place.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QPalette

QUEBEC_BLUE = "#003DA5"  # the blue of the Québec flag

LIGHT = {
    "bg": "#EEF1F5",          # window background: cool light grey
    "surface": "#FFFFFF",     # English field, buttons
    "border": "#CDD4DF",
    "text": "#1B2330",
    "muted": "#5E6878",       # labels, hints
    "accent": QUEBEC_BLUE,
    "accent_soft": "#DCE6F7", # "Keep on top" when active
    "panel": QUEBEC_BLUE,     # the French panel
    "panel_flash": "#2F63C4", # the panel's flash when you copy
    "on_panel": "#FFFFFF",
    "panel_hint": "#A9C0EA",  # placeholder text on the blue panel
    "danger": "#B42318",
}

DARK = {
    "bg": "#15191F",
    "surface": "#1E242D",
    "border": "#323B48",
    "text": "#E7EBF1",
    "muted": "#8F99A8",
    "accent": "#5B8DEF",      # lighter blue: the flag blue is too dark to read on black
    "accent_soft": "#1F2F4D",
    "panel": "#123A86",
    "panel_flash": "#2155B5",
    "on_panel": "#FFFFFF",
    "panel_hint": "#8EA7D6",
    "danger": "#F97066",
}

QSS = """
QWidget#root {{ background: {bg}; color: {text}; }}
QLabel {{ color: {text}; background: transparent; }}
QToolTip {{ background: {surface}; color: {text}; border: 1px solid {border}; padding: 4px 6px; }}

/* Small grey labels: "English", "Français (Québec)" */
QLabel[role="caption"] {{ color: {muted}; font-size: 9pt; font-weight: 600; }}

/* English input */
QPlainTextEdit#english {{
    background: {surface}; color: {text};
    border: 1px solid {border}; border-radius: 10px;
    padding: 8px 10px; font-size: 11pt;
    selection-background-color: {accent}; selection-color: #FFFFFF;
}}
QPlainTextEdit#english:focus {{ border: 1px solid {accent}; }}

/* French output: the one bold element */
QPlainTextEdit#french {{
    background: {panel}; color: {on_panel};
    border: none; border-radius: 10px;
    padding: 10px 12px; font-size: 13pt;
    selection-background-color: {on_panel}; selection-color: {panel};
}}
QPlainTextEdit#french[copied="true"] {{ background: {panel_flash}; }}

/* tu | vous segmented toggle */
QFrame#segmented {{ background: {surface}; border: 1px solid {border}; border-radius: 8px; }}
QFrame#segmented QPushButton {{
    background: transparent; color: {muted};
    border: none; border-radius: 6px; padding: 4px 14px; font-weight: 600;
}}
QFrame#segmented QPushButton:checked {{ background: {accent}; color: #FFFFFF; }}
QFrame#segmented QPushButton:hover:!checked {{ color: {text}; }}

/* Keep on top */
QPushButton#pin {{
    background: {surface}; color: {muted};
    border: 1px solid {border}; border-radius: 8px; padding: 4px 12px;
}}
QPushButton#pin:checked {{ background: {accent_soft}; color: {accent}; border-color: {accent}; }}
QPushButton#pin:disabled {{ color: {border}; }}

/* Status line and quota */
QLabel#status, QLabel#usage {{ color: {muted}; font-size: 9pt; }}
QLabel#status[state="error"] {{ color: {danger}; }}

/* Thin, quiet scrollbars */
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 4px 2px; }}
QScrollBar::handle:vertical {{ background: {border}; border-radius: 3px; min-height: 24px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
"""


def is_dark() -> bool:
    return QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark


def tokens() -> dict:
    return DARK if is_dark() else LIGHT


def stylesheet() -> str:
    return QSS.format(**tokens())


def set_placeholder(widget, color: str):
    """Placeholder text colour isn't reachable from QSS, so set it on the palette."""
    palette = widget.palette()
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(color))
    widget.setPalette(palette)
