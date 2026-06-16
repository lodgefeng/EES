# -*- coding: utf-8 -*-
"""Download latest menu/feature patch modules into LOCALAPPDATA."""

from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

GITHUB_BRANCH = "cursor/fix-python-venv-launch-e627"
GITHUB_RAW_BASE = (
    f"https://raw.githubusercontent.com/lodgefeng/EES/{GITHUB_BRANCH}"
    "/feature/ai_experiment_judgement/app"
)
PATCH_FILES = (
    "home_menu_patch.py",
    "patch_sync.py",
    "run_patched_app.py",
    "ar_imaging_adjustment.py",
    "ai_experiment_llm_judgement.py",
    "experiment_shared.py",
    "ollama_vision_client.py",
    "jbd4020_cast_support.py",
    "ai_experiment_judgement.py",
)


def patch_runtime_root() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if not local_app_data:
        return Path.home() / ".creolight" / "AR_Camera_Ollama" / "patch_runtime"
    return Path(local_app_data) / "Creolight" / "AR_Camera_Ollama" / "patch_runtime"


def patch_app_dir() -> Path:
    return patch_runtime_root() / "app"


def install_patch_path() -> Path:
    root = patch_runtime_root()
    root.mkdir(parents=True, exist_ok=True)
    patch_app_dir().mkdir(parents=True, exist_ok=True)
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    return root


def sync_patch_modules(log_fn=None) -> int:
    target_dir = patch_app_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    updated = 0
    for filename in PATCH_FILES:
        destination = target_dir / filename
        url = f"{GITHUB_RAW_BASE}/{filename}"
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "Creolight-AR-Camera-Ollama-PatchSync"},
            )
            with urllib.request.urlopen(request, timeout=20) as response:
                destination.write_bytes(response.read())
            updated += 1
            if log_fn is not None:
                log_fn(f"patch_sync: updated {filename}")
        except (OSError, urllib.error.URLError) as exc:
            if log_fn is not None:
                log_fn(f"patch_sync: skip {filename} ({exc})")
    return updated
