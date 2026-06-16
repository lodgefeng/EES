#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remove broken button-05 patches from app/main.py and validate syntax."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

MARKER = "AI_EXPERIMENT_JUDGEMENT_MENU_PATCH"
BACKUP_SUFFIX = ".bak_button05"


def repair_main_py(main_py: Path) -> tuple[bool, str]:
    original = main_py.read_text(encoding="utf-8")
    backup = main_py.with_suffix(main_py.suffix + BACKUP_SUFFIX)

    syntax_ok, syntax_error = _syntax_ok(original)
    has_patch = MARKER in original or "schedule_ai_experiment_menu_button" in original

    if not has_patch:
        if syntax_ok:
            return True, "main.py syntax OK, no button-05 patch found"
        restored, message = _restore_backup(main_py, backup)
        if restored:
            return True, message
        return False, f"main.py syntax broken and no backup to restore: {syntax_error}"

    if not backup.exists():
        backup.write_text(original, encoding="utf-8")

    repaired = original
    repaired = _remove_import_block(repaired)
    repaired = _remove_schedule_call(repaired)
    repaired = _remove_helper_functions(repaired)
    repaired = _cleanup_blank_lines(repaired)

    ok, error = _syntax_ok(repaired)
    if ok:
        main_py.write_text(repaired, encoding="utf-8")
        return True, "repaired main.py (removed button-05 source patch)"

    restored, message = _restore_backup(main_py, backup)
    if restored:
        return True, message
    return False, f"repair still invalid: {error}"


def _restore_backup(main_py: Path, backup: Path) -> tuple[bool, str]:
    if not backup.exists():
        return False, "no backup file"
    restored = backup.read_text(encoding="utf-8")
    ok, error = _syntax_ok(restored)
    if not ok:
        return False, f"backup also invalid: {error}"
    main_py.write_text(restored, encoding="utf-8")
    return True, "restored main.py from backup"


def _syntax_ok(text: str) -> tuple[bool, str | None]:
    try:
        ast.parse(text)
        return True, None
    except SyntaxError as exc:
        return False, str(exc)


def _remove_import_block(text: str) -> str:
    patterns = [
        (
            rf"(?m)^# {re.escape(MARKER)}\s*\n"
            r"try:\n"
            r"    from app\.home_menu_patch import schedule_ai_experiment_menu_button\n"
            r"except Exception:\n"
            r"    schedule_ai_experiment_menu_button = None\n"
            r"\n?"
        ),
        (
            r"(?m)^try:\n"
            r"    from app\.home_menu_patch import schedule_ai_experiment_menu_button\n"
            r"except Exception:\n"
            r"    schedule_ai_experiment_menu_button = None\n"
            r"\n?"
        ),
    ]
    for pattern in patterns:
        text = re.sub(pattern, "", text)
    return text


def _remove_schedule_call(text: str) -> str:
    pattern = (
        r"(?m)^[ \t]*if schedule_ai_experiment_menu_button is not None:\n"
        r"[ \t]*schedule_ai_experiment_menu_button\(self\)\n"
    )
    return re.sub(pattern, "", text)


def _remove_helper_functions(text: str) -> str:
    patterns = [
        (
            rf"(?ms)^# {re.escape(MARKER)}\n"
            r"def _ai_experiment_menu_patch_fallback\(window\):\n"
            r"    try:\n"
            r"        from app\.home_menu_patch import schedule_ai_experiment_menu_button\n"
            r"        schedule_ai_experiment_menu_button\(window\)\n"
            r"    except Exception:\n"
            r"        pass\n"
            r"\n?"
        ),
        (
            rf"(?ms)^# {re.escape(MARKER)}\n"
            r"def _schedule_ai_experiment_menu_button\(window\):\n"
            r"    try:\n"
            r"        from app\.home_menu_patch import schedule_ai_experiment_menu_button\n"
            r"        schedule_ai_experiment_menu_button\(window\)\n"
            r"    except Exception:\n"
            r"        pass\n"
            r"\n?"
        ),
    ]
    for pattern in patterns:
        text = re.sub(pattern, "", text)
    return text


def _cleanup_blank_lines(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    if not text.endswith("\n"):
        text += "\n"
    return text


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: repair_main_py_menu_patch.py <project_dir>")
        return 1

    project_dir = Path(argv[1]).resolve()
    main_py = project_dir / "app" / "main.py"
    if not main_py.exists():
        print(f"ERROR: missing {main_py}")
        return 1

    ok, message = repair_main_py(main_py)
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
