# -*- coding: utf-8 -*-
"""Python startup hook: load Creolight patches before app.main runs."""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path


def _log(message: str) -> None:
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if not local_app_data:
        return
    log_path = Path(local_app_data) / "Creolight" / "AR_Camera_Ollama" / "launcher.log"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write(message + "\n")
    except OSError:
        pass


def _install_paths() -> None:
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    app_dir = Path(
        os.environ.get(
            "CREOLIGHT_APP_DIR",
            r"C:\Program Files\Creolight\AR_Camera_Ollama",
        )
    )
    patch_runtime = Path(
        os.environ.get(
            "CREOLIGHT_PATCH_RUNTIME",
            Path(local_app_data) / "Creolight" / "AR_Camera_Ollama" / "patch_runtime"
            if local_app_data
            else Path.home() / ".creolight" / "AR_Camera_Ollama" / "patch_runtime",
        )
    )
    for entry in (str(app_dir), str(patch_runtime)):
        while entry in sys.path:
            sys.path.remove(entry)
    sys.path.insert(0, str(app_dir))
    sys.path.insert(0, str(patch_runtime))
    _log(f"creolight_startup: patch_runtime={patch_runtime}")
    _log(f"creolight_startup: app_dir={app_dir}")
    _log(f"creolight_startup: sys.path[:3]={sys.path[:3]}")


def _activate_menu_patch() -> None:
    try:
        import app.home_menu_patch as home_menu_patch

        _log(f"creolight_startup: home_menu_patch={home_menu_patch.__file__}")
        home_menu_patch.activate_menu_patch_runtime()
        _log("creolight_startup: menu patch activated")
    except Exception:
        _log("creolight_startup: menu patch failed")
        _log(traceback.format_exc())


_install_paths()
_activate_menu_patch()
