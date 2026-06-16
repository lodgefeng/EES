# -*- coding: utf-8 -*-
"""Start Creolight with LOCALAPPDATA patch modules overriding Program Files."""

from __future__ import annotations

import os
import runpy
import sys
import traceback
from pathlib import Path


def _default_app_dir() -> Path:
    return Path(
        os.environ.get(
            "CREOLIGHT_APP_DIR",
            r"C:\Program Files\Creolight\AR_Camera_Ollama",
        )
    )


def _patch_runtime_root() -> Path:
    override = os.environ.get("CREOLIGHT_PATCH_RUNTIME")
    if override:
        return Path(override)
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if not local_app_data:
        return Path.home() / ".creolight" / "AR_Camera_Ollama" / "patch_runtime"
    return Path(local_app_data) / "Creolight" / "AR_Camera_Ollama" / "patch_runtime"


def _log_path() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if not local_app_data:
        return Path.home() / ".creolight" / "AR_Camera_Ollama" / "launcher.log"
    return Path(local_app_data) / "Creolight" / "AR_Camera_Ollama" / "launcher.log"


def _log(message: str) -> None:
    try:
        path = _log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(message + "\n")
    except OSError:
        pass


def _install_paths(app_dir: Path, patch_runtime: Path) -> None:
    app_dir_text = str(app_dir)
    patch_runtime_text = str(patch_runtime)
    for entry in (app_dir_text, patch_runtime_text):
        while entry in sys.path:
            sys.path.remove(entry)
    sys.path.insert(0, app_dir_text)
    sys.path.insert(0, patch_runtime_text)


def main() -> None:
    app_dir = _default_app_dir()
    patch_runtime = _patch_runtime_root()
    patch_app = patch_runtime / "app"
    patch_app.mkdir(parents=True, exist_ok=True)

    _install_paths(app_dir, patch_runtime)
    os.chdir(app_dir)

    _log("run_patched_app: starting")
    _log(f"run_patched_app: patch_runtime={patch_runtime}")
    _log(f"run_patched_app: app_dir={app_dir}")
    _log(f"run_patched_app: sys.path[:4]={sys.path[:4]}")

    try:
        from app.launcher_entry import _bootstrap_patch_modules

        _bootstrap_patch_modules()
    except Exception:
        _log("run_patched_app: bootstrap failed")
        _log(traceback.format_exc())

    _install_paths(app_dir, patch_runtime)

    try:
        import app.home_menu_patch as home_menu_patch

        _log(f"run_patched_app: home_menu_patch={home_menu_patch.__file__}")
        home_menu_patch.activate_menu_patch_runtime()
        _log("run_patched_app: menu patch activated")
    except Exception:
        _log("run_patched_app: menu patch failed")
        _log(traceback.format_exc())

    sys.argv = ["app.main", *sys.argv[1:]]
    runpy.run_module("app.main", run_name="__main__")


if __name__ == "__main__":
    main()
