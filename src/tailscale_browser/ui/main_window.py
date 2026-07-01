"""Main window: tabs, session, settings, recents."""

import os
import platform
from typing import Any, Dict, List

from PyQt5 import QtCore, QtGui, QtWebEngineWidgets, QtWidgets

from tailscale_browser.config import load_config, normalize_url, save_config
from tailscale_browser.constants import (
    APP_NAME,
    APP_VERSION,
    RECENT_MAX,
    SESSION_SAVE_DEBOUNCE_MS,
    TAB_TITLE_MAX_LEN,
    WEBENGINE_PROFILE_NAME,
)
from tailscale_browser.paths import data_dir, resource_path
from tailscale_browser.session import (
    default_session,
    load_session,
    save_session,
    tab_entry_new,
    tab_entry_url,
)
from tailscale_browser.ui.browser_tab import BrowserTab
from tailscale_browser.ui.styles import corner_button_style, main_window_stylesheet
from tailscale_browser.ui.tab_strip import TabStrip


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QtGui.QIcon(resource_path("icon.svg")))
        self.resize(1200, 800)

        self._apply_platform_style()
        self.setStyleSheet(main_window_stylesheet())

        self.config: Dict[str, Any] = load_config()

        storage = self._profile_paths()
        self._profile = QtWebEngineWidgets.QWebEngineProfile(WEBENGINE_PROFILE_NAME)
        self._profile.setPersistentStoragePath(storage["persistent"])
        self._profile.setCachePath(storage["cache"])
        self._profile.setPersistentCookiesPolicy(
            QtWebEngineWidgets.QWebEngineProfile.ForcePersistentCookies
        )

        self._suppress_last_tab_close = False

        self._session_timer = QtCore.QTimer(self)
        self._session_timer.setSingleShot(True)
        self._session_timer.timeout.connect(self._flush_session_save)

        style = self.style()

        add_btn = QtWidgets.QPushButton(" New tab")
        add_btn.setIcon(style.standardIcon(QtWidgets.QStyle.SP_FileDialogNewFolder))
        add_btn.setIconSize(QtCore.QSize(16, 16))
        add_btn.setMinimumWidth(98)
        add_btn.setMinimumHeight(30)
        add_btn.setMaximumHeight(30)
        add_btn.clicked.connect(self.add_empty_tab)
        add_btn.setStyleSheet(corner_button_style())

        settings_btn = QtWidgets.QPushButton()
        settings_btn.setIcon(self._settings_icon(style))
        settings_btn.setIconSize(QtCore.QSize(18, 18))
        settings_btn.setMinimumWidth(34)
        settings_btn.setMaximumWidth(34)
        settings_btn.setMinimumHeight(30)
        settings_btn.setMaximumHeight(30)
        settings_btn.setToolTip("Settings")
        settings_btn.setStyleSheet(corner_button_style())
        settings_btn.clicked.connect(self._show_settings_menu)

        self.tab_strip = TabStrip(add_btn, settings_btn)
        self.tab_strip.tabCloseRequested.connect(self.close_tab)
        self.tab_strip.currentChanged.connect(self.on_tab_changed)
        self.tab_strip.tab_bar().installEventFilter(self)
        self.tab_strip.tab_bar().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tab_strip.tab_bar().customContextMenuRequested.connect(
            self._on_tab_bar_context_menu
        )
        self.tab_strip.tabMoved.connect(lambda *_: self._schedule_session_save())

        container = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.tab_strip)
        self.setCentralWidget(container)

        self._restore_or_initial_tabs()
        self._apply_window_geometry()
        sess = load_session()
        if (sess.get("window") or {}).get("maximized", True):
            self.showMaximized()
        else:
            self.showNormal()

    def _profile_paths(self) -> Dict[str, str]:
        from tailscale_browser.paths import profile_cache_path, profile_storage_path

        return {"persistent": profile_storage_path(), "cache": profile_cache_path()}

    @staticmethod
    def _settings_icon(style: QtWidgets.QStyle) -> QtGui.QIcon:
        for name in ("preferences-system", "emblem-system", "applications-system"):
            ico = QtGui.QIcon.fromTheme(name)
            if not ico.isNull():
                return ico
        return style.standardIcon(QtWidgets.QStyle.SP_FileDialogDetailedView)

    def _apply_platform_style(self) -> None:
        app = QtWidgets.QApplication.instance()
        if not app:
            return
        keys = QtWidgets.QStyleFactory.keys()
        system = platform.system()
        if system == "Windows":
            for s in ("Windows11", "windowsvista", "Windows", "Fusion"):
                if s in keys:
                    app.setStyle(s)
                    break
        elif system == "Darwin":
            for s in ("macOS", "Macintosh", "Fusion"):
                if s in keys:
                    app.setStyle(s)
                    break
        else:
            app.setStyle("Fusion")

    def _get_recent_list(self) -> List[Dict[str, str]]:
        return list(self.config.get("recent", []))

    def _saved_name_for_url(self, url: str) -> str:
        normalized = normalize_url(url)
        for item in self._get_recent_list():
            if normalize_url(item.get("url", "")) == normalized:
                return (item.get("name") or "").strip()
        return ""

    def _restore_or_initial_tabs(self) -> None:
        sess = load_session()
        tabs = sess.get("tabs") or [tab_entry_new()]
        for entry in tabs:
            if entry.get("kind") == "new_tab":
                tab = BrowserTab(
                    self._profile,
                    "",
                    start_on_new_tab_page=True,
                    get_recent=self._get_recent_list,
                )
                title = "New tab"
            else:
                url = entry.get("url") or ""
                tab = BrowserTab(
                    self._profile,
                    url,
                    start_on_new_tab_page=False,
                    get_recent=self._get_recent_list,
                )
                preferred_name = entry.get(
                    "preferred_title"
                ) or self._saved_name_for_url(url)
                if preferred_name:
                    tab.set_preferred_title(preferred_name)
                title = self._short_title(
                    preferred_name or entry.get("title") or url or "Tab"
                )
            self.tab_strip.addTab(tab, title)
            self._wire_tab(tab)
        cur = int(sess.get("current_tab", 0))
        if 0 <= cur < self.tab_strip.count():
            self.tab_strip.setCurrentIndex(cur)

    def _apply_window_geometry(self) -> None:
        sess = load_session()
        w = sess.get("window") or {}
        if w.get("maximized"):
            return
        x, y = w.get("x"), w.get("y")
        width, height = w.get("w", 1200), w.get("h", 800)
        if x is not None and y is not None and width and height:
            self.setGeometry(int(x), int(y), int(width), int(height))

    def _wire_tab(self, tab: BrowserTab) -> None:
        tab.set_popup_handler(self._create_popup)
        tab.title_changed.connect(lambda t, tb=tab: self._on_tab_title(tb, t))
        tab.url_changed_for_session.connect(self._schedule_session_save)
        tab.add_recent_requested.connect(self.add_to_recent)
        tab.entered_web_mode.connect(self._schedule_session_save)

    def _on_tab_title(self, tab: BrowserTab, title: str) -> None:
        i = self.tab_strip.indexOf(tab)
        if i < 0:
            return
        preferred = tab.preferred_title()
        self.tab_strip.setTabText(i, self._short_title(preferred or title))

    @staticmethod
    def _short_title(title: str) -> str:
        t = (title or "Tab").strip() or "Tab"
        if len(t) > TAB_TITLE_MAX_LEN:
            return t[: TAB_TITLE_MAX_LEN - 1] + "…"
        return t

    def _create_popup(self, window_type):
        tab = BrowserTab(
            self._profile,
            "",
            start_on_new_tab_page=False,
            get_recent=self._get_recent_list,
        )
        self._wire_tab(tab)
        idx = self.tab_strip.addTab(tab, "New tab")
        self.tab_strip.setCurrentIndex(idx)
        self._schedule_session_save()
        return tab.web_engine_page()

    def add_empty_tab(self) -> None:
        tab = BrowserTab(
            self._profile,
            "",
            start_on_new_tab_page=True,
            get_recent=self._get_recent_list,
        )
        self._wire_tab(tab)
        self.tab_strip.addTab(tab, "New tab")
        self.tab_strip.setCurrentWidget(tab)
        self._schedule_session_save()
        QtCore.QTimer.singleShot(0, tab.focus_new_tab_address)

    def add_tab_with_url(self, url: str, title: str = "") -> None:
        u = normalize_url(url)
        if not u:
            return
        tab = BrowserTab(
            self._profile,
            u,
            start_on_new_tab_page=False,
            get_recent=self._get_recent_list,
        )
        preferred = (title or self._saved_name_for_url(u)).strip()
        if preferred:
            tab.set_preferred_title(preferred)
        self._wire_tab(tab)
        self.tab_strip.addTab(tab, self._short_title(preferred or u))
        self.tab_strip.setCurrentWidget(tab)
        self._schedule_session_save()

    def add_to_recent(self, name: str, url: str) -> None:
        if not name or not url:
            return
        url = normalize_url(url)
        self.config["recent"] = [
            r for r in self._get_recent_list() if r.get("url") != url
        ]
        self.config["recent"].insert(0, {"name": name, "url": url})
        self.config["recent"] = self.config["recent"][:RECENT_MAX]
        save_config(self.config)
        for i in range(self.tab_strip.count()):
            w = self.tab_strip.widget(i)
            if isinstance(w, BrowserTab):
                w.refresh_saved_sites()

    def _on_tab_bar_context_menu(self, pos: QtCore.QPoint) -> None:
        bar = self.tab_strip.tab_bar()
        idx = bar.tabAt(pos)
        if idx < 0:
            return
        menu = QtWidgets.QMenu(self)
        act_reload = menu.addAction("Reload")
        act_dup = menu.addAction("Duplicate tab")
        act_close = menu.addAction("Close tab")
        act_close_others = menu.addAction("Close other tabs")
        act_close_right = menu.addAction("Close tabs to the right")
        act_copy = menu.addAction("Copy URL")
        chosen = menu.exec_(bar.mapToGlobal(pos))
        if chosen == act_reload:
            w = self.tab_strip.widget(idx)
            if isinstance(w, BrowserTab):
                w.reload()
        elif chosen == act_dup:
            w = self.tab_strip.widget(idx)
            if isinstance(w, BrowserTab):
                self.add_tab_with_url(w.current_url(), self.tab_strip.tabText(idx))
        elif chosen == act_close:
            self.close_tab(idx)
        elif chosen == act_close_others:
            for i in reversed(range(self.tab_strip.count())):
                if i != idx:
                    self.close_tab(i)
        elif chosen == act_close_right:
            for i in reversed(range(idx + 1, self.tab_strip.count())):
                self.close_tab(i)
        elif chosen == act_copy:
            w = self.tab_strip.widget(idx)
            if isinstance(w, BrowserTab):
                QtWidgets.QApplication.clipboard().setText(w.current_url())

    def eventFilter(self, obj: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if obj == self.tab_strip.tab_bar():
            if event.type() in (QtCore.QEvent.MouseButtonPress, QtCore.QEvent.Enter):
                cur = self.tab_strip.currentWidget()
                if isinstance(cur, BrowserTab):
                    cur.show_toolbar()
        return super().eventFilter(obj, event)

    def on_tab_changed(self, index: int) -> None:
        if index >= 0:
            w = self.tab_strip.widget(index)
            if isinstance(w, BrowserTab):
                w.show_toolbar()
        self._schedule_session_save()

    def close_tab(self, idx: int) -> None:
        tab = self.tab_strip.widget(idx)
        if isinstance(tab, BrowserTab):
            tab.cleanup()
        self.tab_strip.removeTab(idx)
        if self.tab_strip.count() == 0 and not self._suppress_last_tab_close:
            self.close()
        else:
            self._schedule_session_save()

    def _collect_session(self) -> Dict[str, Any]:
        entries = []
        for i in range(self.tab_strip.count()):
            tab = self.tab_strip.widget(i)
            if not isinstance(tab, BrowserTab):
                continue
            if tab.is_showing_new_tab_page():
                entries.append(tab_entry_new())
            else:
                u = tab.current_url()
                entries.append(
                    tab_entry_url(
                        u,
                        self.tab_strip.tabText(i).replace("…", ""),
                        tab.preferred_title(),
                    )
                )
        geo = self.geometry()
        sess = {
            "version": 1,
            "window": {
                "x": geo.x(),
                "y": geo.y(),
                "w": geo.width(),
                "h": geo.height(),
                "maximized": self.isMaximized(),
            },
            "current_tab": self.tab_strip.currentIndex(),
            "tabs": entries,
        }
        return sess

    def _schedule_session_save(self) -> None:
        self._session_timer.stop()
        self._session_timer.start(SESSION_SAVE_DEBOUNCE_MS)

    def _flush_session_save(self) -> None:
        try:
            save_session(self._collect_session())
        except Exception:
            pass

    def _show_settings_menu(self) -> None:
        menu = QtWidgets.QMenu(self)
        menu.addAction("Manage saved sites…", self.manage_recent)
        menu.addSeparator()
        menu.addAction("Clear browsing data…", self._clear_browsing_data)
        menu.addSeparator()
        menu.addAction(f"About {APP_NAME}", self._about)
        menu.exec_(QtGui.QCursor.pos())

    def _about(self) -> None:
        QtWidgets.QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<b>{APP_NAME}</b> {APP_VERSION}<br/><br/>"
            "A small Qt WebEngine browser for Tailscale addresses.",
        )

    def _clear_browsing_data(self) -> None:
        r = QtWidgets.QMessageBox.question(
            self,
            "Clear browsing data",
            "This will remove all open tabs except a fresh tab, clear cookies and cache, "
            "and delete saved window session data. Site logins may be lost.<br/><br/>"
            "A full disk wipe of profile data runs on the <b>next</b> launch.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if r != QtWidgets.QMessageBox.Yes:
            return

        marker = os.path.join(data_dir(), ".wipe_profile_next_launch")
        try:
            with open(marker, "w") as f:
                f.write("1")
        except OSError:
            pass

        self._profile.cookieStore().deleteAllCookies()
        try:
            self._profile.clearHttpCache()
        except Exception:
            pass

        self._suppress_last_tab_close = True
        try:
            while self.tab_strip.count():
                self.close_tab(self.tab_strip.count() - 1)
        finally:
            self._suppress_last_tab_close = False
        save_session(default_session())
        self.add_empty_tab()

    def manage_recent(self) -> None:
        if not self._get_recent_list():
            QtWidgets.QMessageBox.information(
                self,
                "Saved sites",
                "No saved sites yet. Open pages from the new tab screen.",
            )
            return

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Saved sites")
        dialog.setMinimumWidth(520)
        layout = QtWidgets.QVBoxLayout(dialog)
        lw = QtWidgets.QListWidget()
        for item in self._get_recent_list():
            lw.addItem(f"{item['name']}  ·  {item['url']}")
        layout.addWidget(lw)
        row = QtWidgets.QHBoxLayout()
        del_btn = QtWidgets.QPushButton("Delete")
        del_btn.clicked.connect(lambda: self._mr_delete(lw))
        row.addWidget(del_btn)
        ed_btn = QtWidgets.QPushButton("Edit…")
        ed_btn.clicked.connect(lambda: self._mr_edit(lw))
        row.addWidget(ed_btn)
        op_btn = QtWidgets.QPushButton("Open in tab")
        op_btn.clicked.connect(lambda: self._mr_open(lw, dialog))
        row.addWidget(op_btn)
        row.addStretch(1)
        cl_btn = QtWidgets.QPushButton("Close")
        cl_btn.clicked.connect(dialog.accept)
        row.addWidget(cl_btn)
        layout.addLayout(row)
        dialog.exec_()

    def _mr_delete(self, lw: QtWidgets.QListWidget) -> None:
        row = lw.currentRow()
        if row >= 0:
            self.config["recent"].pop(row)
            save_config(self.config)
            lw.takeItem(row)
            self._refresh_all_saved_sites()

    def _mr_edit(self, lw: QtWidgets.QListWidget) -> None:
        row = lw.currentRow()
        if row < 0:
            return
        item = self._get_recent_list()[row]
        d = QtWidgets.QDialog(self)
        d.setWindowTitle("Edit saved site")
        lo = QtWidgets.QVBoxLayout(d)
        ne = QtWidgets.QLineEdit(item["name"])
        ue = QtWidgets.QLineEdit(item["url"])
        lo.addWidget(QtWidgets.QLabel("Name:"))
        lo.addWidget(ne)
        lo.addWidget(QtWidgets.QLabel("URL:"))
        lo.addWidget(ue)
        bb = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        bb.accepted.connect(d.accept)
        bb.rejected.connect(d.reject)
        lo.addWidget(bb)
        if d.exec_() == QtWidgets.QDialog.Accepted:
            nn, nu = ne.text().strip(), normalize_url(ue.text().strip())
            if nn and nu:
                self.config["recent"][row] = {"name": nn, "url": nu}
                save_config(self.config)
                lw.item(row).setText(f"{nn}  ·  {nu}")
                self._refresh_all_saved_sites()

    def _mr_open(self, lw: QtWidgets.QListWidget, dialog: QtWidgets.QDialog) -> None:
        row = lw.currentRow()
        if row >= 0:
            it = self._get_recent_list()[row]
            self.add_tab_with_url(it["url"], it["name"])
            dialog.accept()

    def _refresh_all_saved_sites(self) -> None:
        for i in range(self.tab_strip.count()):
            w = self.tab_strip.widget(i)
            if isinstance(w, BrowserTab):
                w.refresh_saved_sites()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        try:
            save_session(self._collect_session())
        except Exception:
            pass
        for i in range(self.tab_strip.count()):
            t = self.tab_strip.widget(i)
            if isinstance(t, BrowserTab):
                t.cleanup()
        event.accept()
