import json
import os
import sys
from typing import Dict, List, Optional, Tuple

from PyQt5 import QtCore, QtGui, QtWebEngineWidgets, QtWidgets

# Load unsecure tailscale instances
chromium_flags = [
    "--ignore-certificate-errors",
    "--disable-features=TranslateUI",
    "--disable-web-security",
]
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = " ".join(chromium_flags)

APP_NAME = "Tailscale Browser"
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".tailscale_browser")
PRIMARY_COLOR = "#7c3aed"  # Nice shade of purple
# Dark mode colors similar to Chrome
DARK_BG = "#202124"
DARK_TAB_BAR = "#323639"
DARK_TAB_ACTIVE = "#323639"
DARK_TAB_INACTIVE = "#202124"
DARK_TEXT = "#e8eaed"
DARK_BUTTON = "#3c4043"
DARK_BUTTON_HOVER = "#5f6368"


def load_recent() -> List[Dict[str, str]]:
    """
    Return the list of recent addresses from the config file.
    """
    config = load_config()
    return config.get("recent", [])


def ensure_config_exists() -> None:
    """
    Ensure the config file exists and has the base structure.
    """
    if not os.path.exists(CONFIG_FILE):
        base = {"recent": []}
        with open(CONFIG_FILE, "w") as f:
            json.dump(base, f, indent=2)


def load_config() -> dict:
    """
    Load the config file as a dict. If missing or invalid, create/reset it.
    """
    ensure_config_exists()
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError
            if "recent" not in data:
                data["recent"] = []
            return data
    except Exception:
        base = {"recent": []}
        with open(CONFIG_FILE, "w") as f:
            json.dump(base, f, indent=2)
        return base


def save_config(config: dict) -> None:
    """
    Save the config dict to the config file.
    """
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


class InsecureWebEnginePage(QtWebEngineWidgets.QWebEnginePage):
    """Custom QWebEnginePage that accepts all SSL certificate errors and enables dark mode."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Set dark background color for the page
        self.setBackgroundColor(QtGui.QColor(DARK_BG))

    def certificateError(self, error):
        error.ignoreCertificateError()
        return True

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # Suppress console messages to reduce noise
        pass


class AddTabDialog(QtWidgets.QDialog):
    """
    Dialog for adding a new browser tab. Allows picking from recent or entering new address.
    """

    def __init__(
        self, recent: List[Dict[str, str]], parent: Optional[QtWidgets.QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add New Tab")
        self.setMinimumWidth(400)
        layout = QtWidgets.QVBoxLayout(self)

        self.recent = recent
        self.combo = QtWidgets.QComboBox()
        self.combo.setEditable(True)
        for item in recent:
            self.combo.addItem(f"{item['name']} ({item['url']})", item)
        layout.addWidget(QtWidgets.QLabel("Pick recent or enter new address:"))
        layout.addWidget(self.combo)

        self.name_edit = QtWidgets.QLineEdit()
        self.url_edit = QtWidgets.QLineEdit()
        layout.addWidget(QtWidgets.QLabel("Name:"))
        layout.addWidget(self.name_edit)
        layout.addWidget(QtWidgets.QLabel("URL or IP:"))
        layout.addWidget(self.url_edit)

        # Pre-fill fields if there is at least one recent item
        if recent:
            self.fill_fields(0)

        self.combo.currentIndexChanged.connect(self.fill_fields)
        self.combo.lineEdit().textChanged.connect(self.clear_fields)

        btns = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        self.buttonBox = QtWidgets.QDialogButtonBox(btns)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

    def fill_fields(self, idx: int) -> None:
        """Fill name and url fields from selected recent item."""
        if idx >= 0 and idx < len(self.recent):
            item = self.recent[idx]
            self.name_edit.setText(item["name"])
            self.url_edit.setText(item["url"])

    def clear_fields(self, _: str) -> None:
        """Clear name and url fields when editing combobox."""
        self.name_edit.clear()
        self.url_edit.clear()

    def get_data(self) -> Tuple[str, str]:
        """Return (name, url) from dialog fields."""
        name = self.name_edit.text().strip()
        url = self.url_edit.text().strip()
        if not url:
            url = self.combo.currentText().strip()
        return name, url


class BrowserTab(QtWidgets.QWidget):
    """
    A single browser tab containing a QWebEngineView with dark mode support and per-tab progress bar.
    """

    def __init__(self, url: str, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add per-tab progress bar at the top
        self.progress = QtWidgets.QProgressBar()
        self.progress.setMaximumHeight(3)
        self.progress.setTextVisible(False)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        # Dark progress bar styling
        progress_style = (
            f"QProgressBar::chunk {{ background: {PRIMARY_COLOR}; }} "
            f"QProgressBar {{ border: none; background: transparent; }}"
        )
        self.progress.setStyleSheet(progress_style)
        layout.addWidget(self.progress)

        self.webview = QtWebEngineWidgets.QWebEngineView()

        # Use the insecure page to allow self-signed/invalid certs
        self.webview.setPage(InsecureWebEnginePage(self.webview))

        # Set dark background for the webview itself
        self.webview.setStyleSheet(f"background-color: {DARK_BG};")

        # Connect progress signals to this tab's progress bar
        self.webview.loadStarted.connect(self._on_load_started)
        self.webview.loadProgress.connect(self.progress.setValue)
        self.webview.loadFinished.connect(self._on_load_finished)

        # Set a default home page if url is empty
        if not url or url.strip() == "":
            url = "about:blank"

        # Set initial dark page content for about:blank
        if url == "about:blank":
            self._set_dark_blank_page()
        else:
            self.webview.setUrl(QtCore.QUrl(url))

        layout.addWidget(self.webview)

    def _on_load_started(self):
        """Show progress bar when loading starts."""
        self.progress.setVisible(True)
        self.progress.setValue(0)

    def _on_load_finished(self, ok):
        """Hide progress bar when loading finishes."""
        self.progress.setVisible(False)

    def _set_dark_blank_page(self):
        """Set a dark-themed blank page."""
        dark_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    background-color: {DARK_BG};
                    color: {DARK_TEXT};
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 40px;
                    text-align: center;
                }}
                .message {{
                    margin-top: 100px;
                    opacity: 0.7;
                }}
            </style>
        </head>
        <body>
            <div class="message">
                <h2>Tailscale Browser</h2>
                <p>Add a new tab to get started</p>
            </div>
        </body>
        </html>
        """
        self.webview.setHtml(dark_html)


class MainWindow(QtWidgets.QMainWindow):
    """
    Main application window for Tailscale Browser.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QtGui.QIcon(self.resource_path("icon.svg")))
        self.resize(1200, 800)
        self.showMaximized()
        # Chrome-like dark mode styling
        self.setStyleSheet(
            f"""
            QMainWindow {{
                background: {DARK_BG};
                color: {DARK_TEXT};
            }}
            QTabWidget::pane {{
                border: none;
                background: {DARK_BG};
            }}
            QTabBar {{
                background: {DARK_TAB_BAR};
            }}
            QTabBar::tab:selected {{
                background: {DARK_TAB_ACTIVE};
                color: {DARK_TEXT};
                border: none;
                padding: 8px 16px;
                margin-right: 2px;
            }}
            QTabBar::tab:!selected {{
                background: {DARK_TAB_INACTIVE};
                color: #9aa0a6;
                border: none;
                padding: 8px 16px;
                margin-right: 2px;
            }}
            QTabBar::tab:hover:!selected {{
                background: #3c4043;
                color: {DARK_TEXT};
            }}
            QPushButton {{
                background: {DARK_BUTTON};
                color: {DARK_TEXT};
                border: 1px solid #5f6368;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {DARK_BUTTON_HOVER};
                border-color: #8ab4f8;
            }}
            QDialog {{
                background: {DARK_BG};
                color: {DARK_TEXT};
            }}
            QLabel {{
                color: {DARK_TEXT};
            }}
            QLineEdit {{
                background: #3c4043;
                color: {DARK_TEXT};
                border: 1px solid #5f6368;
                border-radius: 4px;
                padding: 8px;
            }}
            QLineEdit:focus {{
                border-color: #8ab4f8;
            }}
            QComboBox {{
                background: #3c4043;
                color: {DARK_TEXT};
                border: 1px solid #5f6368;
                border-radius: 4px;
                padding: 8px;
            }}
            QComboBox:focus {{
                border-color: #8ab4f8;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {DARK_TEXT};
                margin-right: 10px;
            }}
        """
        )
        self.config: dict = load_config()
        # Create the main tab widget
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        # Create a custom top bar with the tab bar and buttons
        top_bar = QtWidgets.QWidget()
        top_layout = QtWidgets.QHBoxLayout(top_bar)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(12)

        # Add the tab bar only (not the whole tab widget)
        top_layout.addWidget(self.tabs.tabBar(), 1)
        top_layout.addStretch(1)

        add_btn = QtWidgets.QPushButton("+ New Tab")
        add_btn.clicked.connect(self.add_tab)
        top_layout.addWidget(add_btn, 0)

        open_recent_btn = QtWidgets.QPushButton("Open Recent")
        open_recent_btn.clicked.connect(self.open_recent)
        top_layout.addWidget(open_recent_btn, 0)

        # Main layout: top bar + tab widget (with content)
        container = QtWidgets.QWidget()
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        container_layout.addWidget(top_bar)
        container_layout.addWidget(self.tabs)
        self.setCentralWidget(container)

        self.add_tab()  # Start with one tab

    @property
    def recent(self) -> List[Dict[str, str]]:
        return self.config.get("recent", [])

    def add_tab(self) -> None:
        """Show dialog to add a new tab, and add it if accepted."""
        dialog = AddTabDialog(self.recent, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            name, url = dialog.get_data()
            if not url:
                return
            if not url.startswith("http"):
                url = "http://" + url
            self.tabs.addTab(BrowserTab(url), name or url)
            # Save to recent
            if name and url and not any(r["url"] == url for r in self.recent):
                self.config["recent"].insert(0, {"name": name, "url": url})
                self.config["recent"] = self.config["recent"][:10]
                save_config(self.config)

    def close_tab(self, idx: int) -> None:
        """Close a tab if more than one is open."""
        if self.tabs.count() > 1:
            self.tabs.removeTab(idx)

    def open_recent(self) -> None:
        """Open a recent address in a new tab."""
        items = [f"{r['name']} ({r['url']})" for r in self.config.get("recent", [])]
        item, ok = QtWidgets.QInputDialog.getItem(
            self, "Open Recent", "Select:", items, 0, False
        )
        if ok and item:
            idx = items.index(item)
            r = self.recent[idx]
            self.tabs.addTab(BrowserTab(r["url"]), r["name"])

    def resource_path(self, rel: str) -> str:
        """Get resource path for icon, compatible with PyInstaller."""
        if hasattr(sys, "_MEIPASS"):
            return os.path.join(sys._MEIPASS, rel)
        return os.path.join(os.path.abspath(os.path.dirname(__file__)), rel)


def main() -> None:
    """Main entry point for the application."""
    ensure_config_exists()
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
