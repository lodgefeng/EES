# -*- coding: utf-8 -*-
"""Creolight entry point: activate menu patch, then run app.main."""

from __future__ import annotations

import runpy
import sys
import traceback

_LOG_PATH = None


def _log_path():
    global _LOG_PATH
    if _LOG_PATH is not None:
        return _LOG_PATH
    import os
    from pathlib import Path

    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        _LOG_PATH = Path(local) / "Creolight" / "AR_Camera_Ollama" / "launcher.log"
    else:
        _LOG_PATH = Path.home() / ".creolight" / "AR_Camera_Ollama" / "launcher.log"
    return _LOG_PATH


def _log(message: str) -> None:
    try:
        path = _log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(message + "\n")
    except OSError:
        pass


def main() -> None:
    _log("bootstrap_main: starting")
    try:
        from app.home_menu_patch import activate_menu_patch_runtime

        activate_menu_patch_runtime()
        _log("bootstrap_main: menu patch activated")
    except Exception:
        _log("bootstrap_main: menu patch failed")
        _log(traceback.format_exc())

    if not sys.argv or sys.argv[0] == "":
        sys.argv = ["app.main"]
    elif sys.argv[0].endswith("bootstrap_main.py"):
        sys.argv[0] = "app.main"

    _log("bootstrap_main: launching app.main")
    runpy.run_module("app.main", run_name="__main__")


if __name__ == "__main__":
    main()
