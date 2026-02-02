import json
import os
import platform
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


def normalize_url(url: str) -> str:
    """Normalize a URL by adding http:// if missing."""
    url = url.strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    return url


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
        self.setMinimumWidth(450)
        layout = QtWidgets.QVBoxLayout(self)

        self.recent = recent

        # Quick select from recent
        if recent:
            layout.addWidget(QtWidgets.QLabel("Quick select from recent:"))
            self.recent_list = QtWidgets.QListWidget()
            for item in recent:
                display = f"{item['name']} ({item['url']})"
                self.recent_list.addItem(display)
            self.recent_list.itemClicked.connect(self.on_recent_selected)
            self.recent_list.itemDoubleClicked.connect(self.on_recent_double_clicked)
            layout.addWidget(self.recent_list)
            layout.addWidget(QtWidgets.QLabel("—— Or enter new ——"))

        # Manual entry
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText("Name (e.g., 'Pi-KVM')")
        self.url_edit = QtWidgets.QLineEdit()
        self.url_edit.setPlaceholderText("URL or IP (e.g., '192.168.1.100' or 'https://example.com')")

        layout.addWidget(QtWidgets.QLabel("Name:"))
        layout.addWidget(self.name_edit)
        layout.addWidget(QtWidgets.QLabel("URL or IP:"))
        layout.addWidget(self.url_edit)

        btns = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        self.buttonBox = QtWidgets.QDialogButtonBox(btns)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

    def on_recent_selected(self, item):
        """Fill fields when a recent item is selected."""
        idx = self.recent_list.row(item)
        if idx >= 0 and idx < len(self.recent):
            rec = self.recent[idx]
            self.name_edit.setText(rec["name"])
            self.url_edit.setText(rec["url"])

    def on_recent_double_clicked(self, item):
        """Accept dialog immediately when double-clicking a recent item."""
        self.on_recent_selected(item)
        self.accept()

    def get_data(self) -> Tuple[str, str]:
        """Return (name, url) from dialog fields."""
        name = self.name_edit.text().strip()
        url = self.url_edit.text().strip()
        url = normalize_url(url)
        return name, url


class BrowserTab(QtWidgets.QWidget):
    """
    A single browser tab with per-tab controls, address bar, reload/stop, and per-tab progress.
    """

    def __init__(self, url: str, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.url = normalize_url(url) if url else "about:blank"
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # === Top toolbar ===
        self.toolbar = QtWidgets.QWidget()
        self.toolbar.setStyleSheet(f"background-color: {DARK_TAB_BAR};")
        self.toolbar.setMaximumHeight(36)
        toolbar_layout = QtWidgets.QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(10, 4, 10, 4)
        toolbar_layout.setSpacing(8)

        # Navigation buttons (Back / Forward / Reload / Stop)
        btn_style = (
            f"QPushButton {{ "
            f"  background: {DARK_BUTTON}; color: {DARK_TEXT}; "
            f"  border: 1px solid #5f6368; border-radius: 3px; "
            f"  padding: 4px 8px; font-size: 13px; font-weight: 500; "
            f"  min-width: 28px; min-height: 24px; max-height: 24px; "
            f"}} "
            f"QPushButton:hover {{ background: {DARK_BUTTON_HOVER}; border-color: #8ab4f8; }} "
            f"QPushButton:pressed {{ background: #5f6368; }}"
        )

        self.back_btn = QtWidgets.QPushButton("←")
        self.back_btn.setToolTip("Back")
        self.back_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.back_btn.setStyleSheet(btn_style)

        self.forward_btn = QtWidgets.QPushButton("→")
        self.forward_btn.setToolTip("Forward")
        self.forward_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.forward_btn.setStyleSheet(btn_style)

        self.reload_btn = QtWidgets.QPushButton("↻")
        self.reload_btn.setToolTip("Reload")
        self.reload_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.reload_btn.setStyleSheet(btn_style)

        self.stop_btn = QtWidgets.QPushButton("⊗")
        self.stop_btn.setToolTip("Stop")
        self.stop_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.stop_btn.setStyleSheet(btn_style)

        toolbar_layout.addWidget(self.back_btn)
        toolbar_layout.addWidget(self.forward_btn)
        toolbar_layout.addWidget(self.reload_btn)
        toolbar_layout.addWidget(self.stop_btn)

        # Divider line
        divider = QtWidgets.QFrame()
        divider.setFrameShape(QtWidgets.QFrame.VLine)
        divider.setStyleSheet("color: #5f6368;")
        toolbar_layout.addWidget(divider)

        # Address bar
        self.address_bar = QtWidgets.QLineEdit()
        self.address_bar.setText(self.url)
        self.address_bar.setPlaceholderText("Enter URL or IP...")
        self.address_bar.returnPressed.connect(self.on_address_enter)
        address_style = (
            f"QLineEdit {{ "
            f"  background: #3c4043; color: {DARK_TEXT}; "
            f"  border: 1px solid #5f6368; border-radius: 3px; "
            f"  padding: 4px 8px; font-size: 12px; "
            f"  selection-background-color: {PRIMARY_COLOR}; "
            f"}} "
            f"QLineEdit:focus {{ border: 1px solid #8ab4f8; }}"
        )
        self.address_bar.setStyleSheet(address_style)
        self.address_bar.setMinimumHeight(24)
        self.address_bar.setMaximumHeight(24)
        toolbar_layout.addWidget(self.address_bar, 1)

        layout.addWidget(self.toolbar)

        # === Per-tab progress bar ===
        self.progress = QtWidgets.QProgressBar()
        self.progress.setMaximumHeight(3)
        self.progress.setTextVisible(False)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        progress_style = (
            f"QProgressBar::chunk {{ background: {PRIMARY_COLOR}; }} "
            f"QProgressBar {{ border: none; background: transparent; }}"
        )
        self.progress.setStyleSheet(progress_style)
        layout.addWidget(self.progress)

        # === WebView ===
        self.webview = QtWebEngineWidgets.QWebEngineView()
        self.webview.setPage(InsecureWebEnginePage(self.webview))
        self.webview.setStyleSheet(f"background-color: {DARK_BG};")

        # Connect signals (each tab has its own loader)
        self.webview.loadStarted.connect(self._on_load_started)
        self.webview.loadProgress.connect(self.progress.setValue)
        self.webview.loadFinished.connect(self._on_load_finished)
        self.webview.titleChanged.connect(self._on_title_changed)
        self.webview.urlChanged.connect(self._on_url_changed)
        self.webview.page().loadStarted.connect(self.hide_toolbar)

        # Connect toolbar buttons
        self.back_btn.clicked.connect(self.webview.back)
        self.forward_btn.clicked.connect(self.webview.forward)
        self.reload_btn.clicked.connect(self.webview.reload)
        self.stop_btn.clicked.connect(self.webview.stop)

        layout.addWidget(self.webview)

        # Load initial URL
        if self.url == "about:blank":
            self._set_dark_blank_page()
        else:
            self.webview.setUrl(QtCore.QUrl(self.url))

    def _on_load_started(self):
        """Show progress bar when loading starts."""
        self.progress.setVisible(True)
        self.progress.setValue(0)

    def _on_load_finished(self, ok):
        """Hide progress bar when loading finishes."""
        self.progress.setVisible(False)

    def _on_title_changed(self, title: str):
        """Update address bar if page title changes (optional)."""
        pass

    def _on_url_changed(self, url: QtCore.QUrl):
        """Update address bar when URL changes."""
        self.address_bar.setText(url.toString())

    def on_address_enter(self):
        """Navigate to URL entered in address bar."""
        url_text = self.address_bar.text().strip()
        if url_text:
            url = normalize_url(url_text)
            self.webview.setUrl(QtCore.QUrl(url))
            # Hide toolbar after navigating
            QtCore.QTimer.singleShot(100, self.hide_toolbar)

    def hide_toolbar(self):
        """Hide the address bar toolbar."""
        self.toolbar.setVisible(False)

    def show_toolbar(self):
        """Show the address bar toolbar."""
        self.toolbar.setVisible(True)

    def mousePressEvent(self, event):
        """Hide toolbar when clicking anywhere in the tab (except toolbar itself)."""
        if not self.toolbar.geometry().contains(event.pos()):
            self.hide_toolbar()
        super().mousePressEvent(event)

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
                <p>Enter a URL in the address bar to get started</p>
            </div>
        </body>
        </html>
        """
        self.webview.setHtml(dark_html)

    def cleanup(self):
        """Properly clean up resources for this tab."""
        try:
            self.webview.stop()
            self.webview.setUrl(QtCore.QUrl("about:blank"))
            # Explicitly delete the page to release resources
            if hasattr(self, 'webview') and self.webview:
                old_page = self.webview.page()
                if old_page:
                    old_page.deleteLater()
        except Exception:
            pass


class MainWindow(QtWidgets.QMainWindow):
    """
    Main application window for Tailscale Browser with recent URLs management.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QtGui.QIcon(self.resource_path("icon.svg")))
        self.resize(1200, 800)
        self.showMaximized()

        # Use native platform style when available (Windows/macOS), fallback to Fusion
        app = QtWidgets.QApplication.instance()
        if app:
            # Detect platform and use appropriate style
            available_styles = QtWidgets.QStyleFactory.keys()
            system = platform.system()

            # Log available styles and current platform for debugging
            print(f"Platform: {system}")
            print(f"Available Qt styles: {available_styles}")

            if system == "Windows":
                # Try Windows 11, then Windows, then Fusion
                for style in ["Windows11", "windowsvista", "Windows", "Fusion"]:
                    if style in available_styles:
                        print(f"Setting style to: {style}")
                        app.setStyle(style)
                        break
            elif system == "Darwin":
                # Try macOS styles
                for style in ["macOS", "Macintosh", "Fusion"]:
                    if style in available_styles:
                        print(f"Setting style to: {style}")
                        app.setStyle(style)
                        break
            else:
                # Linux/other - use Fusion
                print(f"Setting style to: Fusion (Linux/other)")
                app.setStyle("Fusion")

        # Apply stylesheet
        self.apply_stylesheet()

        self.config: dict = load_config()

        # Create the main tab widget
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)

        # Install event filter on tab bar to detect interactions
        self.tabs.tabBar().installEventFilter(self)

        # Create a custom widget to hold buttons in the tab bar corner
        corner_widget = QtWidgets.QWidget()
        corner_layout = QtWidgets.QHBoxLayout(corner_widget)
        corner_layout.setContentsMargins(4, 2, 8, 2)
        corner_layout.setSpacing(6)

        add_btn = QtWidgets.QPushButton("+ New Tab")
        add_btn.setMaximumWidth(100)
        add_btn.setMinimumHeight(24)
        add_btn.setMaximumHeight(24)
        add_btn.clicked.connect(self.add_tab)
        btn_style = (
            f"QPushButton {{ "
            f"  background: {DARK_BUTTON}; color: {DARK_TEXT}; "
            f"  border: 1px solid #5f6368; border-radius: 3px; "
            f"  padding: 4px 12px; font-weight: 500; font-size: 12px; "
            f"}} "
            f"QPushButton:hover {{ background: {DARK_BUTTON_HOVER}; border-color: #8ab4f8; }} "
            f"QPushButton:pressed {{ background: #5f6368; }}"
        )
        add_btn.setStyleSheet(btn_style)

        manage_recent_btn = QtWidgets.QPushButton("📋 Manage Recent")
        manage_recent_btn.setMaximumWidth(140)
        manage_recent_btn.setMinimumHeight(24)
        manage_recent_btn.setMaximumHeight(24)
        manage_recent_btn.clicked.connect(self.manage_recent)
        manage_recent_btn.setStyleSheet(btn_style)

        corner_layout.addWidget(add_btn)
        corner_layout.addWidget(manage_recent_btn)

        # Set corner widget to appear on the right side of tabs
        self.tabs.setCornerWidget(corner_widget, QtCore.Qt.TopRightCorner)

        # Main layout
        container = QtWidgets.QWidget()
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        container_layout.addWidget(self.tabs)
        self.setCentralWidget(container)

        # Track if this is the initial add_tab call
        self.initial_tab_attempt = True
        self.add_tab()  # Start with one tab

    def apply_stylesheet(self):
        """Apply the dark mode stylesheet."""
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
                border-bottom: 1px solid #3c4043;
            }}
            QTabBar::tab:selected {{
                background: {DARK_TAB_ACTIVE};
                color: {DARK_TEXT};
                border: none;
                border-bottom: 3px solid {PRIMARY_COLOR};
                padding: 12px 20px;
                margin-right: 2px;
                font-weight: 600;
                font-size: 13px;
            }}
            QTabBar::tab:!selected {{
                background: {DARK_TAB_INACTIVE};
                color: #9aa0a6;
                border: none;
                padding: 12px 20px;
                margin-right: 2px;
                font-size: 13px;
            }}
            QTabBar::tab:hover:!selected {{
                background: #3c4043;
                color: {DARK_TEXT};
            }}
            QTabBar::close-button {{
                image: url(:/image/transparent.png);
                margin: 0px;
            }}
            QPushButton {{
                background: {DARK_BUTTON};
                color: {DARK_TEXT};
                border: 1px solid #5f6368;
                border-radius: 4px;
                padding: 8px 16px;
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
                padding: 8px;
                height: 28px;
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
        """
        )

    @property
    def recent(self) -> List[Dict[str, str]]:
        return self.config.get("recent", [])

    def eventFilter(self, obj, event):
        """Filter events to show toolbar when interacting with tab bar."""
        if obj == self.tabs.tabBar():
            if event.type() in (QtCore.QEvent.MouseButtonPress, QtCore.QEvent.Enter):
                # Show toolbar on current tab when interacting with tab bar
                current_tab = self.tabs.currentWidget()
                if isinstance(current_tab, BrowserTab):
                    current_tab.show_toolbar()
        return super().eventFilter(obj, event)

    def on_tab_changed(self, index):
        """Show toolbar when switching tabs."""
        if index >= 0:
            tab_widget = self.tabs.widget(index)
            if isinstance(tab_widget, BrowserTab):
                tab_widget.show_toolbar()

    def add_tab(self) -> None:
        """Show dialog to add a new tab, and add it if accepted."""
        dialog = AddTabDialog(self.recent, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            name, url = dialog.get_data()
            if not url:
                return

            self.tabs.addTab(BrowserTab(url), name or url)

            # Save to recent
            if name and url:
                # Remove existing entry with same URL if present
                self.config["recent"] = [r for r in self.recent if r["url"] != url]
                # Add to front
                self.config["recent"].insert(0, {"name": name, "url": url})
                # Keep only 15 recent items
                self.config["recent"] = self.config["recent"][:15]
                save_config(self.config)
            # Reset the flag after first attempt
            if hasattr(self, 'initial_tab_attempt'):
                self.initial_tab_attempt = False
        else:
            # Dialog was cancelled
            if hasattr(self, 'initial_tab_attempt') and self.initial_tab_attempt:
                # On initial startup, close the app if user cancels
                QtCore.QTimer.singleShot(0, self.close)
            # If there are no tabs after cancelling, close the app
            elif self.tabs.count() == 0:
                QtCore.QTimer.singleShot(0, self.close)

    def close_tab(self, idx: int) -> None:
        """Close a tab and clean up resources. Close app if last tab is closed."""
        tab_widget = self.tabs.widget(idx)
        if isinstance(tab_widget, BrowserTab):
            tab_widget.cleanup()
        self.tabs.removeTab(idx)

        # If no tabs remain, close the application
        if self.tabs.count() == 0:
            self.close()

    def manage_recent(self) -> None:
        """Show dialog to manage recent URLs (edit/delete)."""
        if not self.recent:
            QtWidgets.QMessageBox.information(
                self, "Manage Recent", "No recent URLs yet."
            )
            return

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Manage Recent URLs")
        dialog.setMinimumWidth(500)
        layout = QtWidgets.QVBoxLayout(dialog)

        # List of recent items
        list_widget = QtWidgets.QListWidget()
        for item in self.recent:
            display = f"{item['name']} ({item['url']})"
            list_widget.addItem(display)
        layout.addWidget(list_widget)

        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()

        delete_btn = QtWidgets.QPushButton("🗑️ Delete")
        delete_btn.clicked.connect(lambda: self.delete_recent(list_widget))
        btn_layout.addWidget(delete_btn)

        edit_btn = QtWidgets.QPushButton("✏️ Edit")
        edit_btn.clicked.connect(lambda: self.edit_recent(list_widget))
        btn_layout.addWidget(edit_btn)

        open_btn = QtWidgets.QPushButton("✓ Open in Tab")
        open_btn.clicked.connect(lambda: self.open_recent_from_list(list_widget))
        btn_layout.addWidget(open_btn)

        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
        dialog.exec_()

    def delete_recent(self, list_widget: QtWidgets.QListWidget) -> None:
        """Delete selected recent item."""
        current_row = list_widget.currentRow()
        if current_row >= 0:
            self.config["recent"].pop(current_row)
            save_config(self.config)
            list_widget.takeItem(current_row)

    def edit_recent(self, list_widget: QtWidgets.QListWidget) -> None:
        """Edit selected recent item."""
        current_row = list_widget.currentRow()
        if current_row < 0:
            return

        item = self.recent[current_row]
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Edit Recent URL")
        layout = QtWidgets.QVBoxLayout(dialog)

        name_edit = QtWidgets.QLineEdit()
        name_edit.setText(item["name"])
        layout.addWidget(QtWidgets.QLabel("Name:"))
        layout.addWidget(name_edit)

        url_edit = QtWidgets.QLineEdit()
        url_edit.setText(item["url"])
        layout.addWidget(QtWidgets.QLabel("URL:"))
        layout.addWidget(url_edit)

        btns = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        button_box = QtWidgets.QDialogButtonBox(btns)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            new_name = name_edit.text().strip()
            new_url = normalize_url(url_edit.text().strip())
            if new_name and new_url:
                self.config["recent"][current_row] = {"name": new_name, "url": new_url}
                save_config(self.config)
                # Update list display
                list_widget.item(current_row).setText(f"{new_name} ({new_url})")

    def open_recent_from_list(self, list_widget: QtWidgets.QListWidget) -> None:
        """Open selected recent item in a new tab."""
        current_row = list_widget.currentRow()
        if current_row >= 0:
            item = self.recent[current_row]
            self.tabs.addTab(BrowserTab(item["url"]), item["name"])

    def closeEvent(self, event):
        """Clean up all tabs on application close."""
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if isinstance(tab, BrowserTab):
                tab.cleanup()
        event.accept()

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
