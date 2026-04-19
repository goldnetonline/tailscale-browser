"""
Chrome-like tab row: only page tabs live in QTabBar; New tab + Settings stay fixed at the end,
so tabs cannot be dragged past them (unlike QTabWidget corner widget on some platforms).
"""

import os
from typing import Optional

from PyQt5 import QtCore, QtGui, QtWidgets

from tailscale_browser.paths import resource_path


class TabStrip(QtWidgets.QWidget):
    """Horizontal [ tab bar (scrollable) | New tab | Settings ] + stacked pages below."""

    tabCloseRequested = QtCore.pyqtSignal(int)
    currentChanged = QtCore.pyqtSignal(int)
    tabMoved = QtCore.pyqtSignal(int, int)

    def __init__(
        self,
        new_tab_button: QtWidgets.QAbstractButton,
        settings_button: QtWidgets.QAbstractButton,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._tab_bar = QtWidgets.QTabBar()
        self._tab_bar.setMovable(True)
        # Custom close buttons (setTabButton); built-in closable × is unreliable with our QSS/theme.
        self._tab_bar.setTabsClosable(False)
        self._tab_bar.setUsesScrollButtons(True)
        self._tab_bar.setExpanding(False)
        self._tab_bar.setElideMode(QtCore.Qt.ElideRight)
        self._stack = QtWidgets.QStackedWidget()
        self._header = QtWidgets.QWidget()
        self._header.setObjectName("tabHeader")

        self._tab_bar.currentChanged.connect(self._on_bar_current_changed)
        self._tab_bar.tabMoved.connect(self._on_bar_tab_moved)

        for button in (new_tab_button, settings_button):
            button.setMinimumHeight(30)
            button.setMaximumHeight(30)
            button.setSizePolicy(
                QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
            )

        row = QtWidgets.QHBoxLayout(self._header)
        # Right padding so New tab / Settings sit clear of the window edge (like a corner widget).
        row.setContentsMargins(6, 4, 8, 4)
        row.setSpacing(6)
        row.addWidget(self._tab_bar, 1)
        row.addWidget(new_tab_button, 0, QtCore.Qt.AlignVCenter)
        row.addWidget(settings_button, 0, QtCore.Qt.AlignVCenter)

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._header)
        outer.addWidget(self._stack, 1)

    def tab_bar(self) -> QtWidgets.QTabBar:
        return self._tab_bar

    def count(self) -> int:
        return self._tab_bar.count()

    def widget(self, index: int) -> QtWidgets.QWidget:
        return self._stack.widget(index)

    def currentWidget(self) -> QtWidgets.QWidget:
        return self._stack.currentWidget()

    def currentIndex(self) -> int:
        return self._tab_bar.currentIndex()

    def setCurrentIndex(self, index: int) -> None:
        self._tab_bar.setCurrentIndex(index)

    def setCurrentWidget(self, w: QtWidgets.QWidget) -> None:
        i = self._stack.indexOf(w)
        if i >= 0:
            self._tab_bar.setCurrentIndex(i)

    def indexOf(self, w: QtWidgets.QWidget) -> int:
        return self._stack.indexOf(w)

    def tabText(self, index: int) -> str:
        return self._tab_bar.tabText(index)

    def setTabText(self, index: int, text: str) -> None:
        self._tab_bar.setTabText(index, text)

    def addTab(self, page: QtWidgets.QWidget, title: str) -> int:
        self._stack.addWidget(page)
        idx = self._tab_bar.addTab(title)
        self._install_close_button(idx)
        return idx

    def _install_close_button(self, index: int) -> None:
        btn = QtWidgets.QToolButton(self._tab_bar)
        btn.setAutoRaise(True)
        btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        btn.setToolTip("Close tab")
        p = resource_path("tab_close.png")
        if os.path.isfile(p):
            btn.setIcon(QtGui.QIcon(p))
        else:
            btn.setIcon(
                self.style().standardIcon(QtWidgets.QStyle.SP_DialogCloseButton)
            )
        btn.setIconSize(QtCore.QSize(16, 16))
        btn.setFixedSize(22, 22)
        btn.setStyleSheet(
            "QToolButton { background: transparent; border: none; padding: 2px; } "
            "QToolButton:hover { background: rgba(255,255,255,0.12); border-radius: 4px; } "
            "QToolButton:pressed { background: rgba(255,255,255,0.2); }"
        )
        btn.clicked.connect(self._on_close_clicked)
        self._tab_bar.setTabButton(index, QtWidgets.QTabBar.RightSide, btn)

    def _on_close_clicked(self) -> None:
        btn = self.sender()
        if not isinstance(btn, QtWidgets.QToolButton):
            return
        for i in range(self._tab_bar.count()):
            if self._tab_bar.tabButton(i, QtWidgets.QTabBar.RightSide) == btn:
                self.tabCloseRequested.emit(i)
                return

    def removeTab(self, index: int) -> None:
        w = self._stack.widget(index)
        self._stack.removeWidget(w)
        self._tab_bar.removeTab(index)

    def _on_bar_current_changed(self, index: int) -> None:
        if index >= 0:
            self._stack.setCurrentIndex(index)
        self.currentChanged.emit(index)

    def _on_bar_tab_moved(self, from_idx: int, to_idx: int) -> None:
        w = self._stack.widget(from_idx)
        self._stack.removeWidget(w)
        self._stack.insertWidget(to_idx, w)
        self.tabMoved.emit(from_idx, to_idx)
