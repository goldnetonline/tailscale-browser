"""Session persistence (window geometry + tab URLs)."""

import json
import os
from typing import Any, Dict

from tailscale_browser.paths import session_path


SESSION_VERSION = 1


def default_session() -> Dict[str, Any]:
    return {
        "version": SESSION_VERSION,
        "window": {
            "x": None,
            "y": None,
            "w": 1200,
            "h": 800,
            "maximized": True,
        },
        "current_tab": 0,
        "tabs": [{"kind": "new_tab"}],
    }


def load_session() -> Dict[str, Any]:
    path = session_path()
    if not os.path.isfile(path):
        return default_session()
    try:
        with open(path, "r") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError
        if data.get("version") != SESSION_VERSION:
            return default_session()
        if "tabs" not in data or not data["tabs"]:
            data["tabs"] = [{"kind": "new_tab"}]
        data.setdefault("window", default_session()["window"])
        data.setdefault("current_tab", 0)
        return data
    except Exception:
        return default_session()


def save_session(data: Dict[str, Any]) -> None:
    data = dict(data)
    data["version"] = SESSION_VERSION
    path = session_path()
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def tab_entry_new() -> Dict[str, str]:
    return {"kind": "new_tab"}


def tab_entry_url(url: str, title: str = "") -> Dict[str, str]:
    return {"kind": "url", "url": url, "title": title or ""}
