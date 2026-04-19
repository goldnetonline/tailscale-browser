"""Single tab: optional new-tab page, toolbar, webview."""

from typing import Callable, List, Optional

from PyQt5 import QtCore, QtGui, QtWebEngineWidgets, QtWidgets

from tailscale_browser.config import normalize_url
from tailscale_browser.constants import DARK_BG, PRIMARY_COLOR
from tailscale_browser.ui.new_tab_page import NewTabPage
from tailscale_browser.ui.styles import address_bar_style, toolbar_button_style
from tailscale_browser.web.engine_page import TailscaleWebEnginePage


class BrowserTab(QtWidgets.QWidget):
    """Toolbar + progress + stacked new-tab page / webview."""

    title_changed = QtCore.pyqtSignal(str)
    url_changed_for_session = QtCore.pyqtSignal()
    entered_web_mode = QtCore.pyqtSignal()
    add_recent_requested = QtCore.pyqtSignal(str, str)

    def __init__(
        self,
        profile: QtWebEngineWidgets.QWebEngineProfile,
        url: str = "",
        *,
        start_on_new_tab_page: bool = True,
        get_recent: Optional[Callable[[], List[dict]]] = None,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._profile = profile
        self._get_recent = get_recent or (lambda: [])
        self._start_new_tab = start_on_new_tab_page and not (url and url.strip())
        self._initial_url = normalize_url(url) if url else ""
        self._pending_name_for_recent: str = ""
        self._save_recent_after_load = False
        self._preferred_title: str = ""

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.toolbar = QtWidgets.QWidget()
        self.toolbar.setStyleSheet(
            "background-color: #24272b; "
            "border-top: 1px solid #14171a; "
            "border-bottom: 1px solid #3c4043;"
        )
        self.toolbar.setFixedHeight(40)
        tb = QtWidgets.QHBoxLayout(self.toolbar)
        tb.setContentsMargins(10, 4, 10, 4)
        tb.setSpacing(6)

        style = QtWidgets.QApplication.style()
        isize = QtCore.QSize(20, 20)

        self.back_btn = QtWidgets.QPushButton()
        self.back_btn.setIcon(style.standardIcon(QtWidgets.QStyle.SP_ArrowBack))
        self.back_btn.setIconSize(isize)
        self.back_btn.setToolTip("Back")
        self.back_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.back_btn.setStyleSheet(toolbar_button_style())

        self.forward_btn = QtWidgets.QPushButton()
        self.forward_btn.setIcon(style.standardIcon(QtWidgets.QStyle.SP_ArrowForward))
        self.forward_btn.setIconSize(isize)
        self.forward_btn.setToolTip("Forward")
        self.forward_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.forward_btn.setStyleSheet(toolbar_button_style())

        self.reload_btn = QtWidgets.QPushButton()
        self.reload_btn.setIcon(style.standardIcon(QtWidgets.QStyle.SP_BrowserReload))
        self.reload_btn.setIconSize(isize)
        self.reload_btn.setToolTip("Reload")
        self.reload_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.reload_btn.setStyleSheet(toolbar_button_style())

        self.stop_btn = QtWidgets.QPushButton()
        self.stop_btn.setIcon(style.standardIcon(QtWidgets.QStyle.SP_BrowserStop))
        self.stop_btn.setIconSize(isize)
        self.stop_btn.setToolTip("Stop")
        self.stop_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.stop_btn.setStyleSheet(toolbar_button_style())

        for b in (self.back_btn, self.forward_btn, self.reload_btn, self.stop_btn):
            tb.addWidget(b)

        div = QtWidgets.QFrame()
        div.setFrameShape(QtWidgets.QFrame.VLine)
        div.setStyleSheet("color: #5f6368; max-width: 1px;")
        tb.addWidget(div)

        self.address_bar = QtWidgets.QLineEdit()
        self.address_bar.setPlaceholderText("Search or enter address")
        self.address_bar.returnPressed.connect(self._on_address_enter)
        self.address_bar.setStyleSheet(address_bar_style())
        self.address_bar.setMinimumHeight(30)
        tb.addWidget(self.address_bar, 1)

        layout.addWidget(self.toolbar)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setMaximumHeight(3)
        self.progress.setTextVisible(False)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        self.progress.setStyleSheet(
            f"QProgressBar::chunk {{ background: {PRIMARY_COLOR}; }} "
            f"QProgressBar {{ border: none; background: transparent; }}"
        )
        layout.addWidget(self.progress)

        self._stack = QtWidgets.QStackedWidget()
        self._new_tab = NewTabPage(self._get_recent, self)
        self._new_tab.open_url.connect(self._on_new_tab_navigate)

        self.webview = QtWebEngineWidgets.QWebEngineView()
        self._page = TailscaleWebEnginePage(profile, self.webview)
        self.webview.setPage(self._page)
        self.webview.setStyleSheet(f"background-color: {DARK_BG};")

        self._stack.addWidget(self._new_tab)
        self._stack.addWidget(self.webview)
        layout.addWidget(self._stack, 1)

        self.webview.loadStarted.connect(self._on_load_started)
        self.webview.loadProgress.connect(self.progress.setValue)
        self.webview.loadFinished.connect(self._on_load_finished)
        self.webview.titleChanged.connect(self._on_title_changed)
        self.webview.urlChanged.connect(self._on_url_changed)
        self.webview.page().loadStarted.connect(self._maybe_hide_toolbar_on_load)

        self.back_btn.clicked.connect(self.webview.back)
        self.forward_btn.clicked.connect(self.webview.forward)
        self.reload_btn.clicked.connect(self.webview.reload)
        self.stop_btn.clicked.connect(self.webview.stop)

        self._update_nav_buttons()
        self.webview.urlChanged.connect(lambda _: self._update_nav_buttons())
        self.webview.loadFinished.connect(lambda _: self._update_nav_buttons())

        if self._start_new_tab:
            self._stack.setCurrentIndex(0)
            self.toolbar.setVisible(False)
            self.address_bar.setText("")
            QtCore.QTimer.singleShot(0, self._new_tab.focus_url)
        else:
            self._stack.setCurrentIndex(1)
            u = self._initial_url or "about:blank"
            self.address_bar.setText(u)
            if u == "about:blank":
                self._set_simple_blank()
            else:
                self.webview.setUrl(QtCore.QUrl(u))

    def web_engine_page(self) -> TailscaleWebEnginePage:
        return self._page

    def set_popup_handler(self, handler) -> None:
        self._page.set_create_popup_handler(handler)

    def refresh_saved_sites(self) -> None:
        self._new_tab.reload_list()

    def focus_new_tab_address(self) -> None:
        if self.is_showing_new_tab_page():
            self._new_tab.focus_url()

    def is_showing_new_tab_page(self) -> bool:
        return self._stack.currentIndex() == 0

    def _on_new_tab_navigate(self, name: str, url: str) -> None:
        url = normalize_url(url)
        if not url:
            return
        self._pending_name_for_recent = name
        if name.strip():
            self.set_preferred_title(name.strip())
        self._save_recent_after_load = True
        self.address_bar.setText(url)
        self._stack.setCurrentIndex(1)
        self.toolbar.setVisible(True)
        self.entered_web_mode.emit()
        self.webview.setUrl(QtCore.QUrl(url))

    def _on_address_enter(self) -> None:
        text = self.address_bar.text().strip()
        if not text:
            return
        url = normalize_url(text)
        self._save_recent_after_load = False
        self._pending_name_for_recent = ""
        self.webview.setUrl(QtCore.QUrl(url))
        if self._stack.currentIndex() == 0:
            self._stack.setCurrentIndex(1)
            self.toolbar.setVisible(True)
            self.entered_web_mode.emit()
        QtCore.QTimer.singleShot(120, self.hide_toolbar)

    def _maybe_hide_toolbar_on_load(self) -> None:
        if self._stack.currentIndex() == 1:
            QtCore.QTimer.singleShot(80, self.hide_toolbar)

    def _set_simple_blank(self) -> None:
        html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"/>
        <style>body{{background:{DARK_BG};color:#9aa0a6;font-family:system-ui;margin:0;
        display:flex;align-items:center;justify-content:center;height:100vh;}}</style>
        </head><body><p>Empty page</p></body></html>"""
        self.webview.setHtml(html)

    def _on_load_started(self) -> None:
        self.progress.setVisible(True)
        self.progress.setValue(0)

    def _on_load_finished(self, ok: bool) -> None:
        self.progress.setVisible(False)
        if not ok or not self._save_recent_after_load:
            return
        self._save_recent_after_load = False
        page_url = self.webview.url().toString()
        title = (self.webview.title() or "").strip()
        name = self._pending_name_for_recent.strip()
        if not name:
            name = title or QtCore.QUrl(page_url).host() or page_url
        self._pending_name_for_recent = ""
        self.add_recent_requested.emit(name, page_url)

    def _on_title_changed(self, title: str) -> None:
        if (
            self._stack.currentIndex() == 1
            and title.strip()
            and not self._preferred_title
        ):
            self.title_changed.emit(title.strip()[:80])

    def _on_url_changed(self, qurl: QtCore.QUrl) -> None:
        self.address_bar.setText(qurl.toString())
        self.url_changed_for_session.emit()

    def hide_toolbar(self) -> None:
        if self._stack.currentIndex() == 1:
            self.toolbar.setVisible(False)

    def show_toolbar(self) -> None:
        if self._stack.currentIndex() == 1:
            self.toolbar.setVisible(True)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._stack.currentIndex() == 1 and not self.toolbar.geometry().contains(
            event.pos()
        ):
            self.hide_toolbar()
        super().mousePressEvent(event)

    def _update_nav_buttons(self) -> None:
        try:
            self.back_btn.setEnabled(self.webview.history().canGoBack())
            self.forward_btn.setEnabled(self.webview.history().canGoForward())
        except Exception:
            pass

    def current_url(self) -> str:
        return self.webview.url().toString()

    def set_preferred_title(self, title: str) -> None:
        self._preferred_title = (title or "").strip()
        if self._preferred_title:
            self.title_changed.emit(self._preferred_title[:80])

    def preferred_title(self) -> str:
        return self._preferred_title

    def reload(self) -> None:
        self.webview.reload()

    def cleanup(self) -> None:
        try:
            self.webview.stop()
            self.webview.setUrl(QtCore.QUrl("about:blank"))
            pg = self.webview.page()
            if pg:
                pg.deleteLater()
        except Exception:
            pass
