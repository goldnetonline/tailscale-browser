"""Filesystem paths and resource resolution (PyInstaller-safe)."""

import os
import sys


def data_dir() -> str:
    d = os.path.join(os.path.expanduser("~"), ".tailscale_browser")
    os.makedirs(d, exist_ok=True)
    return d


def config_path() -> str:
    return os.path.join(data_dir(), "config.json")


def session_path() -> str:
    return os.path.join(data_dir(), "session.json")


def profile_root() -> str:
    p = os.path.join(data_dir(), "profile")
    os.makedirs(p, exist_ok=True)
    return p


def profile_storage_path() -> str:
    p = os.path.join(profile_root(), "storage")
    os.makedirs(p, exist_ok=True)
    return p


def profile_cache_path() -> str:
    p = os.path.join(profile_root(), "cache")
    os.makedirs(p, exist_ok=True)
    return p


def package_dir() -> str:
    return os.path.abspath(os.path.dirname(__file__))


def resource_path(rel: str) -> str:
    """
    Resolve a path under repo `resources/` at dev time, or PyInstaller bundle.
    `rel` is e.g. "icon.svg" or "resources/icon.svg" — we join with resources/.
    """
    name = rel.replace("\\", "/").lstrip("/")
    if name.startswith("resources/"):
        name = name[10:]

    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
        for candidate in (
            os.path.join(base, "resources", name),
            os.path.join(base, name),
        ):
            if os.path.isfile(candidate):
                return candidate
        return os.path.join(base, "resources", name)

    repo_root = os.path.abspath(os.path.join(package_dir(), "..", ".."))
    return os.path.join(repo_root, "resources", name)
