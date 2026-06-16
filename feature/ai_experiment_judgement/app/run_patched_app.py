# -*- coding: utf-8 -*-
"""Legacy LOCALAPPDATA launcher; prefer app.bootstrap_main in Program Files."""

from __future__ import annotations

import importlib.util
import os
import runpy
import sys
import traceback
from pathlib import Path
from types import ModuleType


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


def _log(message: str) -> None:
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if not local_app_data:
        path = Path.home() / ".creolight" / "AR_Camera_Ollama" / "launcher.log"
    else:
        path = Path(local_app_data) / "Creolight" / "AR_Camera_Ollama" / "launcher.log"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(message + "\n")
    except OSError:
        pass


def _install_app_path(app_dir: Path) -> None:
    app_dir_text = str(app_dir)
    while app_dir_text in sys.path:
        sys.path.remove(app_dir_text)
    sys.path.insert(0, app_dir_text)


def _load_module_from_file(module_name: str, file_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module from {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _preload_patch_modules(patch_app: Path) -> None:
    preload_order = (
        "experiment_shared.py",
        "ollama_vision_client.py",
        "jbd4020_cast_support.py",
        "ar_imaging_adjustment.py",
        "ai_experiment_llm_judgement.py",
        "home_menu_patch.py",
        "bootstrap_main.py",
    )
    for filename in preload_order:
        file_path = patch_app / filename
        if not file_path.exists():
            continue
        module_name = f"app.{file_path.stem}"
        if module_name in sys.modules:
            continue
        _load_module_from_file(module_name, file_path)
        _log(f"run_patched_app: loaded {module_name}")


def main() -> None:
    app_dir = _default_app_dir()
    patch_runtime = _patch_runtime_root()
    patch_app = patch_runtime / "app"
    installed_bootstrap = app_dir / "app" / "bootstrap_main.py"

    if not (app_dir / "app" / "main.py").exists():
        raise SystemExit(f"Missing {app_dir / 'app' / 'main.py'}")

    _install_app_path(app_dir)
    os.chdir(app_dir)
    _log("run_patched_app: starting")

    if installed_bootstrap.exists() and (app_dir / "app" / "home_menu_patch.py").exists():
        _log("run_patched_app: delegating to installed app.bootstrap_main")
        runpy.run_module("app.bootstrap_main", run_name="__main__")
        return

    try:
        if patch_app.exists():
            _preload_patch_modules(patch_app)
        bootstrap = sys.modules.get("app.bootstrap_main")
        if bootstrap is not None:
            bootstrap.main()
            return
        home_menu_patch = sys.modules.get("app.home_menu_patch")
        if home_menu_patch is not None:
            home_menu_patch.activate_menu_patch_runtime()
            _log("run_patched_app: menu patch activated")
    except Exception:
        _log("run_patched_app: menu patch failed")
        _log(traceback.format_exc())

    sys.argv = ["app.main", *sys.argv[1:]]
    runpy.run_module("app.main", run_name="__main__")


if __name__ == "__main__":
    main()
