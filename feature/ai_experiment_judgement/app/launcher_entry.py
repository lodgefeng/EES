# -*- coding: utf-8 -*-
"""Launch app.main with automatic home-menu button 05/06 injection."""

from __future__ import annotations

import os
import runpy
import sys
import traceback
import urllib.error
import urllib.request
from pathlib import Path

_LOG_PATH = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "Creolight",
    "AR_Camera_Ollama",
    "launcher.log",
)
_GITHUB_BRANCH = "cursor/fix-python-venv-launch-e627"
_GITHUB_RAW_BASE = (
    f"https://raw.githubusercontent.com/lodgefeng/EES/{_GITHUB_BRANCH}"
    "/feature/ai_experiment_judgement/app"
)
_PATCH_FILES = (
    "patch_sync.py",
    "run_patched_app.py",
    "home_menu_patch.py",
    "ar_imaging_adjustment.py",
    "ai_experiment_llm_judgement.py",
    "experiment_shared.py",
    "ollama_vision_client.py",
    "jbd4020_cast_support.py",
    "ai_experiment_judgement.py",
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


def _patch_runtime_root() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if not local_app_data:
        return Path.home() / ".creolight" / "AR_Camera_Ollama" / "patch_runtime"
    return Path(local_app_data) / "Creolight" / "AR_Camera_Ollama" / "patch_runtime"


def _download_raw_module(destination: Path, url: str) -> bool:
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Creolight-AR-Camera-Ollama-Launcher"},
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            destination.write_bytes(response.read())
        return True
    except (OSError, urllib.error.URLError) as exc:
        _log(f"launcher_entry: skip download {destination.name} ({exc})")
        return False


def _bootstrap_patch_modules() -> None:
    patch_runtime = _patch_runtime_root()
    patch_app = patch_runtime / "app"
    patch_app.mkdir(parents=True, exist_ok=True)

    patch_runtime_text = str(patch_runtime)
    if patch_runtime_text not in sys.path:
        sys.path.insert(0, patch_runtime_text)

    updated = 0
    for filename in _PATCH_FILES:
        destination = patch_app / filename
        url = f"{_GITHUB_RAW_BASE}/{filename}"
        if _download_raw_module(destination, url):
            updated += 1
            _log(f"launcher_entry: updated patch module {filename}")
    _log(f"launcher_entry: synced {updated}/{len(_PATCH_FILES)} patch module(s) to LOCALAPPDATA")


def main() -> None:
    _bootstrap_patch_modules()

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
