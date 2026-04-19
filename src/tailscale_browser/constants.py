"""Application constants and Chromium flags (no Qt imports)."""

APP_NAME = "Tailscale Browser"
APP_VERSION = "0.1.0"

# Chromium / Qt WebEngine — applied in main() before importing QtWebEngine
CHROMIUM_FLAGS = [
    "--ignore-certificate-errors",
    "--disable-features=TranslateUI",
    "--disable-web-security",
    # WebRTC / media (conservative; GPU left at Chromium defaults)
    "--autoplay-policy=no-user-gesture-required",
]

# Theme — dark chrome-like palette
PRIMARY_COLOR = "#7c3aed"
DARK_BG = "#202124"
DARK_TAB_BAR = "#323639"
DARK_TAB_ACTIVE = "#323639"
DARK_TAB_INACTIVE = "#202124"
DARK_TEXT = "#e8eaed"
DARK_BUTTON = "#3c4043"
DARK_BUTTON_HOVER = "#5f6368"

RECENT_MAX = 15
TAB_TITLE_MAX_LEN = 28
SESSION_SAVE_DEBOUNCE_MS = 450

WEBENGINE_PROFILE_NAME = "TailscaleBrowser"
