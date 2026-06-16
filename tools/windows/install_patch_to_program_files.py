#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Copy patch modules into Program Files and wire start_app.bat."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def install_to_program_files(install_dir: Path, source_app: Path, repo_root: Path) -> tuple[bool, str]:
    target_app = install_dir / "app"
    main_py = target_app / "main.py"
    if not main_py.exists():
        return False, f"missing {main_py}"

    if not source_app.exists():
        return False, f"missing source app folder: {source_app}"

    target_app.mkdir(parents=True, exist_ok=True)
    copied = 0
    for file_path in sorted(source_app.glob("*.py")):
        shutil.copy2(file_path, target_app / file_path.name)
        copied += 1

    start_app_src = repo_root / "tools" / "windows" / "start_app.bat"
    if start_app_src.exists():
        shutil.copy2(start_app_src, install_dir / "start_app.bat")

    launch_src = repo_root / "tools" / "windows" / "launch_ar_camera_ollama.bat"
    if launch_src.exists():
        shutil.copy2(launch_src, install_dir / "launch_ar_camera_ollama.bat")

    return True, f"installed {copied} module(s) to {target_app}"


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: install_patch_to_program_files.py <install_dir> [source_app_dir]")
        return 1

    install_dir = Path(argv[1]).resolve()
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parents[1]

    if len(argv) >= 3:
        source_app = Path(argv[2]).resolve()
    else:
        source_app = repo_root / "feature" / "ai_experiment_judgement" / "app"

    ok, message = install_to_program_files(install_dir, source_app, repo_root)
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
