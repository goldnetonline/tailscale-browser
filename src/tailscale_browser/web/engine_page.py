"""QWebEnginePage with certs, media permissions, and window.open handling."""

from typing import Any, Callable, Optional

from PyQt5 import QtGui, QtWebEngineWidgets, QtWidgets

from tailscale_browser.constants import DARK_BG


FeatureHandler = Callable[[Any], Optional[QtWebEngineWidgets.QWebEnginePage]]


class TailscaleWebEnginePage(QtWebEngineWidgets.QWebEnginePage):
    """SSL ignored; dark background; optional permission prompt; createWindow hook."""

    def __init__(
        self,
        profile: QtWebEngineWidgets.QWebEngineProfile,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(profile, parent)
        self.setBackgroundColor(QtGui.QColor(DARK_BG))
        self._create_popup: Optional[FeatureHandler] = None

    def set_create_popup_handler(self, handler: Optional[FeatureHandler]) -> None:
        self._create_popup = handler

    def certificateError(self, error):
        error.ignoreCertificateError()
        return True

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        pass

    def createWindow(self, window_type):
        if self._create_popup:
            return self._create_popup(window_type)
        return None

    def featurePermissionRequested(self, securityOrigin, feature):
        host = securityOrigin.host() or securityOrigin.toString()
        feat_name = self._feature_label(feature)
        parent = None
        if self.view() and self.view().window():
            parent = self.view().window()
        else:
            parent = QtWidgets.QApplication.activeWindow()
        btn = QtWidgets.QMessageBox.question(
            parent,
            "Site permission",
            f"Allow access for “{feat_name}” on {host}?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        granted = btn == QtWidgets.QMessageBox.Yes
        page = QtWebEngineWidgets.QWebEnginePage
        policy = (
            page.PermissionGrantedByUser if granted else page.PermissionDeniedByUser
        )
        self.setFeaturePermission(securityOrigin, feature, policy)

    @staticmethod
    def _feature_label(feature) -> str:
        try:
            page = QtWebEngineWidgets.QWebEnginePage
            mapping = {
                getattr(page, "Geolocation", None): "location",
                getattr(page, "MediaAudioCapture", None): "microphone",
                getattr(page, "MediaVideoCapture", None): "camera",
                getattr(page, "MediaAudioVideoCapture", None): "camera and microphone",
                getattr(page, "DesktopVideoCapture", None): "screen",
                getattr(page, "DesktopAudioVideoCapture", None): "screen and audio",
                getattr(page, "Notifications", None): "notifications",
            }
            for k, v in mapping.items():
                if k is not None and feature == k:
                    return v
        except Exception:
            pass
        return "this feature"
