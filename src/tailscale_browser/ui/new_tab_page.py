"""Centered new-tab UI: optional name, URL, saved sites."""

from typing import Callable, Dict, List

from PyQt5 import QtCore, QtGui, QtWidgets

from tailscale_browser.constants import DARK_BG, DARK_TAB_BAR, DARK_TEXT, PRIMARY_COLOR
from tailscale_browser.paths import resource_path
from tailscale_browser.ui.styles import address_bar_style, corner_button_style


class NewTabPage(QtWidgets.QWidget):
    """Chrome-like speed dial + omnibox."""

    open_url = QtCore.pyqtSignal(str, str)  # name (may be empty), url

    def __init__(
        self,
        get_recent: Callable[[], List[Dict[str, str]]],
        parent: QtWidgets.QWidget = None,
    ) -> None:
        super().__init__(parent)
        self._get_recent = get_recent
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QtGui.QPalette.Window, QtGui.QColor(DARK_BG))
        self.setPalette(pal)

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(48, 32, 48, 48)
        outer.addStretch(1)

        center = QtWidgets.QFrame()
        center.setObjectName("newTabCard")
        center.setMaximumWidth(980)
        center.setMinimumWidth(560)
        center.setStyleSheet(
            "QFrame#newTabCard {"
            "background: #2a2d31;"
            "border: 1px solid #45494e;"
            "border-radius: 12px;"
            "}"
        )
        grid = QtWidgets.QVBoxLayout(center)
        grid.setContentsMargins(26, 22, 26, 22)
        grid.setSpacing(16)

        logo = QtWidgets.QLabel()
        logo.setAlignment(QtCore.Qt.AlignCenter)
        mark = QtGui.QIcon(resource_path("icon.svg")).pixmap(64, 64)
        if not mark.isNull():
            logo.setPixmap(mark)
            grid.addWidget(logo)

        title = QtWidgets.QLabel("Tailscale Browser")
        title.setAlignment(QtCore.Qt.AlignCenter)
        tf = title.font()
        tf.setPointSize(34)
        tf.setWeight(tf.DemiBold)
        title.setFont(tf)
        title.setStyleSheet(f"color: {DARK_TEXT}; background: transparent;")
        grid.addWidget(title)

        sub = QtWidgets.QLabel("Enter an address or pick a saved site")
        sub.setAlignment(QtCore.Qt.AlignCenter)
        sub.setStyleSheet("color: #9aa0a6; font-size: 18px; background: transparent;")
        grid.addWidget(sub)

        self._name = QtWidgets.QLineEdit()
        self._name.setPlaceholderText("Name (optional — uses page title if empty)")
        self._name.setClearButtonEnabled(True)
        self._name.setStyleSheet(address_bar_style())
        self._name.setMinimumHeight(40)
        self._name.setMaximumWidth(930)
        grid.addWidget(self._name)

        row = QtWidgets.QHBoxLayout()
        row.setSpacing(10)
        self._url = QtWidgets.QLineEdit()
        self._url.setPlaceholderText(
            "URL or IP (e.g. 100.x.x.x or https://device.tailnet)"
        )
        self._url.setClearButtonEnabled(True)
        self._url.setStyleSheet(address_bar_style())
        uf = self._url.font()
        uf.setPointSize(16)
        self._url.setFont(uf)
        self._url.setMinimumHeight(48)
        self._url.setMaximumWidth(930)
        self._url.returnPressed.connect(self._emit_navigate)
        row.addWidget(self._url, 1)

        go = QtWidgets.QPushButton("Go")
        go.setStyleSheet(corner_button_style())
        go.setMinimumWidth(88)
        go.setMinimumHeight(48)
        go.clicked.connect(self._emit_navigate)
        row.addWidget(go)
        grid.addLayout(row)

        sites_label = QtWidgets.QLabel("Saved sites")
        sites_label.setStyleSheet(
            "color: #9aa0a6; font-size: 12px; font-weight: 600; "
            "text-transform: uppercase; letter-spacing: 0.5px; background: transparent;"
        )
        grid.addWidget(sites_label)

        self._list = QtWidgets.QListWidget()
        self._list.setMinimumHeight(200)
        self._list.setMaximumHeight(280)
        self._list.setMaximumWidth(930)
        self._list.setAlternatingRowColors(False)
        self._list.setStyleSheet(
            f"QListWidget {{ background: {DARK_TAB_BAR}; border: 1px solid #5f6368; "
            f"border-radius: 8px; font-size: 14px; }}"
            f"QListWidget::item {{ padding: 12px 14px; border-radius: 4px; }}"
            f"QListWidget::item:selected {{ background: {PRIMARY_COLOR}; }}"
        )
        self._list.itemDoubleClicked.connect(self._on_double_click)
        grid.addWidget(self._list, 1)

        outer.addWidget(center, 0, QtCore.Qt.AlignHCenter)
        outer.addStretch(1)

        self.reload_list()

    def focus_url(self) -> None:
        self._url.setFocus(QtCore.Qt.OtherFocusReason)

    def reload_list(self) -> None:
        self._list.clear()
        for item in self._get_recent():
            name = item.get("name", "")
            url = item.get("url", "")
            self._list.addItem(f"{name}  ·  {url}")

    def _on_double_click(self, item: QtWidgets.QListWidgetItem) -> None:
        row = self._list.row(item)
        recent = self._get_recent()
        if 0 <= row < len(recent):
            r = recent[row]
            self.open_url.emit(r.get("name", ""), r.get("url", ""))

    def _emit_navigate(self) -> None:
        name = self._name.text().strip()
        url = self._url.text().strip()
        if url:
            self.open_url.emit(name, url)
