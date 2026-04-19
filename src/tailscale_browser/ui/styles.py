"""Application-wide Qt stylesheets."""

from tailscale_browser.constants import (
    DARK_BG,
    DARK_BUTTON,
    DARK_BUTTON_HOVER,
    DARK_TEXT,
    PRIMARY_COLOR,
)


def main_window_stylesheet() -> str:
    # Note: close controls are custom tab buttons in TabStrip.
    return f"""
        QMainWindow {{
            background: {DARK_BG};
            color: {DARK_TEXT};
        }}
        QWidget#tabHeader {{
            background: #2f3337;
            border-bottom: 1px solid #1f2226;
            min-height: 40px;
            max-height: 40px;
        }}
        QTabBar {{
            background: transparent;
            border: none;
            min-height: 38px;
        }}
        QTabBar::tab:selected {{
            background: #3a3f44;
            color: {DARK_TEXT};
            border: 1px solid #5a5f64;
            border-bottom: 2px solid {PRIMARY_COLOR};
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            padding: 7px 16px;
            margin: 5px 3px 0 0;
            font-weight: 600;
            font-size: 13px;
            min-height: 28px;
        }}
        QTabBar::tab:!selected {{
            background: #262a2f;
            color: #9aa0a6;
            border: 1px solid #454a4f;
            border-bottom: 1px solid #454a4f;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            padding: 7px 16px;
            margin: 7px 3px 0 0;
            font-size: 13px;
            min-height: 26px;
        }}
        QTabBar::tab:hover:!selected {{
            background: #32373c;
            color: {DARK_TEXT};
            border-color: #5a5f64;
        }}
        QPushButton {{
            background: {DARK_BUTTON};
            color: {DARK_TEXT};
            border: 1px solid #5f6368;
            border-radius: 4px;
            padding: 8px 14px;
            font-weight: 500;
            font-size: 13px;
            min-height: 28px;
        }}
        QPushButton:hover {{
            background: {DARK_BUTTON_HOVER};
            border-color: #8ab4f8;
        }}
        QPushButton:pressed {{
            background: #5f6368;
        }}
        QDialog {{
            background: {DARK_BG};
            color: {DARK_TEXT};
        }}
        QLabel {{
            color: {DARK_TEXT};
            font-size: 12px;
        }}
        QLineEdit {{
            background: #3c4043;
            color: {DARK_TEXT};
            border: 1px solid #5f6368;
            border-radius: 4px;
            padding: 8px 10px;
            font-size: 13px;
            selection-background-color: {PRIMARY_COLOR};
        }}
        QLineEdit:focus {{
            border: 1px solid #8ab4f8;
        }}
        QComboBox {{
            background: #3c4043;
            color: {DARK_TEXT};
            border: 1px solid #5f6368;
            border-radius: 4px;
            padding: 8px;
            font-size: 13px;
        }}
        QComboBox:focus {{
            border: 1px solid #8ab4f8;
        }}
        QComboBox::drop-down {{
            border: none;
        }}
        QListWidget {{
            background: #3c4043;
            color: {DARK_TEXT};
            border: 1px solid #5f6368;
            border-radius: 4px;
            outline: none;
            font-size: 13px;
        }}
        QListWidget::item {{
            padding: 10px 12px;
            min-height: 28px;
        }}
        QListWidget::item:selected {{
            background: {PRIMARY_COLOR};
            color: {DARK_TEXT};
            font-weight: 500;
        }}
        QListWidget::item:hover {{
            background: #4a4d50;
        }}
        QProgressBar {{
            background: transparent;
            border: none;
        }}
        QProgressBar::chunk {{
            background: {PRIMARY_COLOR};
        }}
        QMenu {{
            background: #3c4043;
            color: {DARK_TEXT};
            border: 1px solid #5f6368;
            padding: 4px;
        }}
        QMenu::item {{
            padding: 8px 24px;
        }}
        QMenu::item:selected {{
            background: {PRIMARY_COLOR};
        }}
    """


def toolbar_button_style() -> str:
    return (
        f"QPushButton {{ "
        f"  background: {DARK_BUTTON}; color: {DARK_TEXT}; "
        f"  border: 1px solid #5f6368; border-radius: 4px; "
        f"  padding: 4px; min-width: 30px; min-height: 28px; max-height: 30px; "
        f"}} "
        f"QPushButton:hover {{ background: {DARK_BUTTON_HOVER}; border-color: #8ab4f8; }} "
        f"QPushButton:pressed {{ background: #5f6368; }} "
        f"QPushButton:disabled {{ opacity: 0.45; }}"
    )


def address_bar_style() -> str:
    return (
        f"QLineEdit {{ "
        f"  background: #3c4043; color: {DARK_TEXT}; "
        f"  border: 1px solid #5f6368; border-radius: 4px; "
        f"  padding: 6px 10px; font-size: 13px; "
        f"  selection-background-color: {PRIMARY_COLOR}; "
        f"}} "
        f"QLineEdit:focus {{ border: 1px solid #8ab4f8; }}"
    )


def corner_button_style() -> str:
    return (
        f"QPushButton {{ "
        f"  background: {DARK_BUTTON}; color: {DARK_TEXT}; "
        f"  border: 1px solid #5f6368; border-radius: 6px; "
        f"  padding: 4px 12px; font-weight: 500; font-size: 12px; "
        f"  min-height: 30px; max-height: 30px; "
        f"}} "
        f"QPushButton:hover {{ background: {DARK_BUTTON_HOVER}; border-color: #8ab4f8; }} "
        f"QPushButton:pressed {{ background: #5f6368; }}"
    )
