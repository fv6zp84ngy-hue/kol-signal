from __future__ import annotations

import importlib.metadata
import os
import platform
import sys
from pathlib import Path
from typing import Any

from . import __version__


def _skill_installed() -> bool:
    configured_root = os.environ.get("CODEX_HOME")
    roots = [Path(configured_root)] if configured_root else [Path.home() / ".codex"]
    return any(
        (root / "skills" / "creator-signal-intelligence" / "SKILL.md").is_file()
        for root in roots
    )


def doctor_report() -> dict[str, Any]:
    """Return environment facts without reading creator data or exposing paths."""

    python_supported = sys.version_info >= (3, 11)
    try:
        openpyxl_version = importlib.metadata.version("openpyxl")
        openpyxl_installed = True
    except importlib.metadata.PackageNotFoundError:
        openpyxl_version = None
        openpyxl_installed = False
    working_directory_writable = os.access(Path.cwd(), os.W_OK)
    core_ready = (
        python_supported
        and openpyxl_installed
        and working_directory_writable
    )
    return {
        "status": "ok" if core_ready else "error",
        "python": {
            "version": platform.python_version(),
            "supported": python_supported,
            "minimum": "3.11",
        },
        "package": {
            "name": "kol-signal",
            "version": __version__,
        },
        "dependencies": {
            "openpyxl": {
                "installed": openpyxl_installed,
                "version": openpyxl_version,
            }
        },
        "working_directory": {
            "writable": working_directory_writable,
            "path_disclosed": False,
        },
        "skill": {
            "installed": _skill_installed(),
            "required": False,
        },
        "privacy": {
            "user_data_accessed": False,
            "network_accessed": False,
            "paths_disclosed": False,
        },
    }
