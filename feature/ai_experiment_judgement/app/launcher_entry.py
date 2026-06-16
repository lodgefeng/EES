# -*- coding: utf-8 -*-
"""Launch app.main with automatic home-menu button 05/06 injection."""

from __future__ import annotations

import os
import runpy
import sys
import traceback

_LOG_PATH = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "Creolight",
    "AR_Camera_Ollama",
    "launcher.log",
)


def _log(message: str) -> None:
    if not _LOG_PATH:
        return
    try:
        log_dir = os.path.dirname(_LOG_PATH)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        with open(_LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(message + "\n")
    except OSError:
        pass


def main() -> None:
    try:
        from app.home_menu_patch import activate_menu_patch_runtime

        activate_menu_patch_runtime()
        _log("launcher_entry: home-menu patch runtime activated")
    except Exception:
        _log("launcher_entry: failed to activate home-menu patch")
        _log(traceback.format_exc())

    sys.argv = ["app.main", *sys.argv[1:]]
    runpy.run_module("app.main", run_name="__main__")


if __name__ == "__main__":
    main()
