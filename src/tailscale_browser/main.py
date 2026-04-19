"""Application entry: Chromium env, optional profile wipe, then Qt UI."""

import os
import platform
import shutil
import sys


def _set_chromium_flags() -> None:
    from tailscale_browser.constants import CHROMIUM_FLAGS

    flags = list(CHROMIUM_FLAGS)
    if platform.system() == "Linux":
        flags.append("--enable-webrtc-pipewire-capturer")
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = " ".join(flags)


def _wipe_profile_disk_if_requested() -> None:
    """Remove on-disk profile before WebEngine starts (next-launch full wipe)."""
    from tailscale_browser.paths import data_dir

    marker = os.path.join(data_dir(), ".wipe_profile_next_launch")
    if not os.path.isfile(marker):
        return
    try:
        os.remove(marker)
    except OSError:
        pass
    root = os.path.join(os.path.expanduser("~"), ".tailscale_browser", "profile")
    shutil.rmtree(root, ignore_errors=True)


def main() -> None:
    _set_chromium_flags()
    _wipe_profile_disk_if_requested()

    from PyQt5 import QtCore, QtWidgets

    # Required ordering for Qt WebEngine (Chromium)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts, True)
    from PyQt5 import QtWebEngineWidgets  # noqa: F401 — register before QApplication

    from tailscale_browser.config import ensure_config_exists
    from tailscale_browser.ui.main_window import MainWindow

    ensure_config_exists()
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
