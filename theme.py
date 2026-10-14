"""Look and feel: colour tokens plus a Qt stylesheet built from them.

Qt stylesheets (QSS) work like CSS for desktop widgets. Keeping every colour in
one dictionary per mode ("tokens") means light and dark mode share one stylesheet,
and a colour change happens in exactly one place.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QPalette

# Pick the accent here: "quebec", "fleuve", "verte", "sirop" or "aubergine".
ACCENT = "fleuve"

# "auto" follows the system's light/dark setting; "dark" or "light" forces one.
MODE = "auto"

# Neutral colours: the same whatever accent you pick.
BASE_LIGHT = {
    "bg": "#EEF1F5",          # window background: cool light grey
    "surface": "#FFFFFF",     # English field, buttons
    "border": "#CDD4DF",
    "text": "#1B2330",
    "muted": "#5E6878",       # labels, hints
    "on_panel": "#FFFFFF",    # text on the French panel
    "on_accent": "#FFFFFF",   # text on the selected tu/vous segment
    "danger": "#B42318",
}

BASE_DARK = {
    "bg": "#15191F",
    "surface": "#1E242D",
    "border": "#323B48",
    "text": "#E7EBF1",
    "muted": "#8F99A8",
    "on_panel": "#FFFFFF",
    "on_accent": "#11151B",   # dark text: the dark-mode accents are bright
    "danger": "#F97066",
}

# Each accent has a light and a dark version. The dark versions use a brighter
# accent (a deep colour is unreadable on a dark background) and a deeper panel.
#   accent       selected tu/vous, focus outline, "Keep on top" text
#   accent_soft  "Keep on top" background when active
#   panel        the French panel        panel_flash  its flash when you copy
#   panel_hint   placeholder text on the panel
ACCENTS = {
    "quebec": {  # the blue of the Québec flag
        "light": {"accent": "#003DA5", "accent_soft": "#DCE6F7", "panel": "#003DA5",
                  "panel_flash": "#2F63C4", "panel_hint": "#A9C0EA"},
        "dark": {"accent": "#5B8DEF", "accent_soft": "#18233A", "panel": "#123A86",
                 "panel_flash": "#2155B5", "panel_hint": "#8EA7D6"},
    },
    "fleuve": {  # the St. Lawrence: deep river teal
        "light": {"accent": "#0E6B73", "accent_soft": "#D5ECEC", "panel": "#0E5E66",
                  "panel_flash": "#2A7F87", "panel_hint": "#9CCACD"},
        "dark": {"accent": "#4FB3BA", "accent_soft": "#173A3D", "panel": "#0F4A50",
                 "panel_flash": "#1B6870", "panel_hint": "#86B9BC"},
    },
    "verte": {  # the métro's green line
        "light": {"accent": "#00733F", "accent_soft": "#D6EFE2", "panel": "#006B3E",
                  "panel_flash": "#177F50", "panel_hint": "#9DD3B8"},
        "dark": {"accent": "#3DBE82", "accent_soft": "#173829", "panel": "#0D4A2F",
                 "panel_flash": "#18663F", "panel_hint": "#8CC4A8"},
    },
    "sirop": {  # maple syrup amber
        "light": {"accent": "#9A520E", "accent_soft": "#F4E4CF", "panel": "#7A3F0A",
                  "panel_flash": "#9A5A1E", "panel_hint": "#E0B98C"},
        "dark": {"accent": "#E39A4B", "accent_soft": "#3A2816", "panel": "#5E3210",
                 "panel_flash": "#7C4618", "panel_hint": "#D2A777"},
    },
    "aubergine": {  # deep plum
        "light": {"accent": "#6B2E7F", "accent_soft": "#EDDDF2", "panel": "#55246A",
                  "panel_flash": "#73408A", "panel_hint": "#C9A7D6"},
        "dark": {"accent": "#B983D0", "accent_soft": "#34213D", "panel": "#43205A",
                 "panel_flash": "#5B3277", "panel_hint": "#B596C7"},
    },
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
QFrame#segmented QPushButton:checked {{ background: {accent}; color: {on_accent}; }}
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
    if MODE in ("dark", "light"):
        return MODE == "dark"
    return QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark


def tokens() -> dict:
    mode = "dark" if is_dark() else "light"
    base = BASE_DARK if mode == "dark" else BASE_LIGHT
    accent = ACCENTS.get(ACCENT, ACCENTS["quebec"])[mode]  # unknown name: fall back to blue
    return {**base, **accent}


def stylesheet() -> str:
    return QSS.format(**tokens())


def set_placeholder(widget, color: str):
    """Placeholder text colour isn't reachable from QSS, so set it on the palette."""
    palette = widget.palette()
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(color))
    widget.setPalette(palette)
