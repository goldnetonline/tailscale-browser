"""User config (saved sites / recents)."""

import json
import os
from typing import Any, Dict

from tailscale_browser.paths import config_path, data_dir


def _migrate_legacy_file_if_present() -> None:
    """Older releases used ~/.tailscale_browser as a single JSON file."""
    home = os.path.expanduser("~")
    legacy = os.path.join(home, ".tailscale_browser")
    if not os.path.isfile(legacy):
        return
    try:
        with open(legacy, "r") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            data = {"recent": []}
    except Exception:
        data = {"recent": []}
    os.remove(legacy)
    os.makedirs(data_dir(), exist_ok=True)
    with open(config_path(), "w") as f:
        json.dump(data, f, indent=2)


def ensure_config_exists() -> None:
    _migrate_legacy_file_if_present()
    if not os.path.exists(config_path()):
        save_config({"recent": []})


def load_config() -> dict:
    ensure_config_exists()
    try:
        with open(config_path(), "r") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError
            if "recent" not in data:
                data["recent"] = []
            return data
    except Exception:
        base = {"recent": []}
        save_config(base)
        return base


def save_config(config: Dict[str, Any]) -> None:
    with open(config_path(), "w") as f:
        json.dump(config, f, indent=2)


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    return url
