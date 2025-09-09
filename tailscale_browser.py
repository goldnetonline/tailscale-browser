
import json
import os
import sys
from typing import Dict, List, Optional, Tuple

from PyQt5 import QtCore, QtGui, QtWebEngineWidgets, QtWidgets

APP_NAME = "Tailscale Browser"
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".tailscale_browser")
PRIMARY_COLOR = "#7c3aed"  # Nice shade of purple


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


class AddTabDialog(QtWidgets.QDialog):
    """
    Dialog for adding a new browser tab. Allows picking from recent or entering new address.
    """
    def __init__(self, recent: List[Dict[str, str]], parent: Optional[QtWidgets.QWidget] = None) -> None:
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
            self.name_edit.setText(item['name'])
            self.url_edit.setText(item['url'])

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
    A single browser tab containing a QWebEngineView.
    """
    def __init__(self, url: str, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        self.webview = QtWebEngineWidgets.QWebEngineView()
        self.webview.setUrl(QtCore.QUrl(url))
        layout.addWidget(self.webview)
        layout.setContentsMargins(0, 0, 0, 0)


class MainWindow(QtWidgets.QMainWindow):
    """
    Main application window for Tailscale Browser.
    """
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QtGui.QIcon(self.resource_path("icon.svg")))
        self.resize(1200, 800)
        self.setStyleSheet(f"""
            QMainWindow {{ background: #f5f3ff; }}
            QTabWidget::pane {{ border: 2px solid {PRIMARY_COLOR}; }}
            QTabBar::tab:selected {{ background: {PRIMARY_COLOR}; color: white; }}
            QPushButton {{ background: {PRIMARY_COLOR}; color: white; border-radius: 6px; padding: 6px; }}
            QPushButton:hover {{ background: #a78bfa; }}
        """)
        self.config: dict = load_config()
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        toolbar = QtWidgets.QToolBar()
        self.addToolBar(toolbar)
        add_btn = QtWidgets.QPushButton("+ New Tab")
        add_btn.clicked.connect(self.add_tab)
        toolbar.addWidget(add_btn)
        open_recent_btn = QtWidgets.QPushButton("Open Recent")
        open_recent_btn.clicked.connect(self.open_recent)
        toolbar.addWidget(open_recent_btn)
        toolbar.setMovable(False)

        self.add_tab()  # Start with one tab

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
            if name and url and not any(r['url'] == url for r in self.recent):
                self.recent.insert(0, {'name': name, 'url': url})
                self.recent = self.recent[:10]
                save_config(self.config)

    def close_tab(self, idx: int) -> None:
        """Close a tab if more than one is open."""
        if self.tabs.count() > 1:
            self.tabs.removeTab(idx)

    def open_recent(self) -> None:
        """Open a recent address in a new tab."""
        items = [f"{r['name']} ({r['url']})" for r in self.config.get("recent", [])]
        item, ok = QtWidgets.QInputDialog.getItem(self, "Open Recent", "Select:", items, 0, False)
        if ok and item:
            idx = items.index(item)
            r = self.recent[idx]
            self.tabs.addTab(BrowserTab(r['url']), r['name'])

    def resource_path(self, rel: str) -> str:
        """Get resource path for icon, compatible with PyInstaller."""
        if hasattr(sys, '_MEIPASS'):
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
