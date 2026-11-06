"""浅色 / 深色主题样式表。"""

from __future__ import annotations

from string import Template

PALETTES = {
    "light": {
        "bg": "#F5F6FA", "card": "#FFFFFF", "border": "#E8EAF1",
        "text": "#23262E", "text2": "#8A90A0",
        "accent": "#FF4D26", "accent_soft": "#FFF0EA",
        "blue": "#4D7CFF",
        "primary_bg": "#23262E", "primary_bg_h": "#3B3F4B", "primary_text": "#FFFFFF",
        "ghost_bg": "#EEF0F6", "ghost_bg_h": "#E1E4EE", "ghost_text": "#23262E",
        "groove": "#ECEEF6", "input_bg": "#F5F6FA", "hover_bg": "#EDEFF6", "alt_bg": "#FAFBFE",
        "ok": "#16A866", "ok_soft": "rgba(22,168,102,0.12)",
        "warn": "#D97C0B", "warn_soft": "rgba(232,147,12,0.13)",
        "idle": "#98A0AE", "idle_soft": "rgba(152,160,174,0.15)",
    },
    "dark": {
        "bg": "#1A1B21", "card": "#232530", "border": "#2E3140",
        "text": "#EDEFF5", "text2": "#8B91A2",
        "accent": "#FF6B3D", "accent_soft": "rgba(255,107,61,0.16)",
        "blue": "#5B8CFF",
        "primary_bg": "#EDEFF5", "primary_bg_h": "#FFFFFF", "primary_text": "#1A1B21",
        "ghost_bg": "#2C2F3C", "ghost_bg_h": "#3A3E4E", "ghost_text": "#EDEFF5",
        "groove": "#2C2F3C", "input_bg": "#1F212B", "hover_bg": "rgba(255,255,255,0.07)", "alt_bg": "#262937",
        "ok": "#2BD97E", "ok_soft": "rgba(43,217,126,0.15)",
        "warn": "#FFB020", "warn_soft": "rgba(255,176,32,0.15)",
        "idle": "#7B8194", "idle_soft": "rgba(123,129,148,0.18)",
    },
}

QSS = Template("""
* { font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif; outline: none; }
QWidget { color: $text; font-size: 12px; }

#RootCard { background: $bg; border: 1px solid $border; border-radius: 18px; }

#titleLabel { color: $text; font-size: 13px; font-weight: 700; }
#dateLabel, #clockLabel { color: $text2; font-size: 11px; }

#statusPill { border-radius: 10px; padding: 3px 12px; font-size: 12px; font-weight: 600; }
#statusPill[st="working"] { color: $ok; background: $ok_soft; }
#statusPill[st="paused"]  { color: $warn; background: $warn_soft; }
#statusPill[st="off"]     { color: $idle; background: $idle_soft; }

#countdownLabel { color: $text; font-size: 14px; font-weight: 600; }
#captionLabel { color: $text2; font-size: 11px; }
#moneySymbol { color: $accent; font-size: 20px; font-weight: 700; }
#moneyNumber { color: $accent; font-size: 33px; font-weight: 800;
               font-family: "Bahnschrift", "Segoe UI", "Microsoft YaHei UI"; }
#rateLabel, #msgLabel, #smallLabel { color: $text2; font-size: 11px; }
#monthAmount { color: $accent; font-size: 16px; font-weight: 700;
               font-family: "Bahnschrift", "Segoe UI", "Microsoft YaHei UI"; }

#card { background: $card; border: 1px solid $border; border-radius: 12px; }

QToolButton[tb="1"] { background: transparent; color: $text2; border: none;
                      border-radius: 7px; font-size: 13px; min-width: 26px; min-height: 22px; }
QToolButton[tb="1"]:hover { background: $hover_bg; color: $text; }
QToolButton[tb="1"]:checked { background: $accent_soft; color: $accent; }

QPushButton { background: $ghost_bg; color: $ghost_text; border: none;
              border-radius: 8px; padding: 6px 16px; font-size: 12px; }
QPushButton:hover { background: $ghost_bg_h; }
QPushButton[cls="primary"] { background: $primary_bg; color: $primary_text;
                             border-radius: 16px; padding: 8px 14px; font-size: 13px; font-weight: 600; }
QPushButton[cls="primary"]:hover { background: $primary_bg_h; }
QPushButton[cls="ghost"] { background: $ghost_bg; color: $ghost_text;
                           border-radius: 16px; padding: 8px 14px; font-size: 13px; font-weight: 600; }
QPushButton[cls="ghost"]:hover { background: $ghost_bg_h; }
QPushButton[cls="link"] { background: transparent; color: $blue; padding: 0; font-size: 11px; }
QPushButton[cls="link"]:hover { background: transparent; text-decoration: underline; }
QPushButton:disabled { color: $idle; background: transparent; }

QProgressBar { background: $groove; border: none; border-radius: 4px; min-height: 8px; max-height: 8px; }
QProgressBar::chunk { background: $blue; border-radius: 4px; }

QMenu { background: $card; color: $text; border: 1px solid $border; border-radius: 10px; padding: 6px; }
QMenu::item { padding: 6px 24px 6px 12px; border-radius: 6px; }
QMenu::item:selected { background: $hover_bg; }
QMenu::separator { height: 1px; background: $border; margin: 4px 8px; }

QDialog { background: $card; }
QLabel { background: transparent; }
QLineEdit, QDoubleSpinBox, QTimeEdit, QComboBox {
    background: $input_bg; color: $text; border: 1px solid $border;
    border-radius: 8px; padding: 5px 8px; min-height: 18px; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView { background: $card; color: $text;
    border: 1px solid $border; selection-background-color: $hover_bg; }

QTableWidget { background: $card; color: $text; border: 1px solid $border;
               border-radius: 8px; gridline-color: transparent; alternate-background-color: $alt_bg;
               selection-background-color: $accent_soft; selection-color: $accent; }
QHeaderView::section { background: $input_bg; color: $text2; border: none;
                       border-bottom: 1px solid $border; padding: 6px; font-size: 11px; }

QCheckBox { spacing: 6px; }
QCheckBox::indicator { width: 16px; height: 16px; border-radius: 5px;
                       border: 1px solid $border; background: $input_bg; }
QCheckBox::indicator:checked { background: $blue; border-color: $blue; }

QScrollBar:vertical { background: transparent; width: 8px; margin: 2px; }
QScrollBar::handle:vertical { background: $groove; border-radius: 4px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
""")


def theme_qss(theme: str) -> str:
    palette = PALETTES.get(theme, PALETTES["light"])
    return QSS.substitute(palette)
