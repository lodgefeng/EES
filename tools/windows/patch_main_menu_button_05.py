#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch app/main.py so the home page shows button 05 | AI实验判断."""

from __future__ import annotations

import re
import sys
from pathlib import Path

MARKER = "AI_EXPERIMENT_JUDGEMENT_MENU_PATCH"
IMPORT_BLOCK = (
    "try:\n"
    "    from app.home_menu_patch import schedule_ai_experiment_menu_button\n"
    "except Exception:\n"
    "    schedule_ai_experiment_menu_button = None\n"
)
CALL_LINE = (
    "    if schedule_ai_experiment_menu_button is not None:\n"
    "        schedule_ai_experiment_menu_button(self)\n"
)


def patch_main_py(main_py: Path) -> tuple[bool, str]:
    text = main_py.read_text(encoding="utf-8")
    if MARKER in text:
        return True, "already patched"

    backup = main_py.with_suffix(main_py.suffix + ".bak_button05")
    if not backup.exists():
        backup.write_text(text, encoding="utf-8")

    updated = _insert_imports(text)
    updated, inserted = _insert_schedule_call(updated)
    if not inserted:
        return False, "skipped unsafe main.py patch; use launcher_entry runtime hook instead"

    try:
        import ast

        ast.parse(updated)
    except SyntaxError as exc:
        if backup.exists():
            main_py.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
        return False, f"patch rejected due to syntax error: {exc}"

    main_py.write_text(updated, encoding="utf-8")
    return True, "patched"


def _insert_imports(text: str) -> str:
    if "from app.home_menu_patch import schedule_ai_experiment_menu_button" in text:
        return text

    lines = text.splitlines()
    insert_at = 0
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            insert_at = index + 1
        elif stripped and not stripped.startswith("#") and insert_at > 0:
            break

    block = [f"# {MARKER}"] + IMPORT_BLOCK.splitlines()
    lines[insert_at:insert_at] = block + [""]
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _insert_schedule_call(text: str) -> tuple[str, bool]:
    patterns = [
        r"(^\s*self\.show\(\)\s*$)",
        r"(^\s*window\.show\(\)\s*$)",
        r"(^\s*main_window\.show\(\)\s*$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.MULTILINE)
        if not match:
            continue
        indent = re.match(r"^(\s*)", match.group(1)).group(1)
        call = "\n".join(_indent_line(indent, line) for line in CALL_LINE.splitlines())
        replacement = match.group(1) + "\n" + call
        return text[: match.start(1)] + replacement + text[match.end(1) :], True

    return text, False


def _indent_line(base_indent: str, line: str) -> str:
    if not line.strip():
        return ""
    body = line.lstrip()
    return f"{base_indent}{body}"


def _insert_before_main(text: str) -> str:
    marker = 'if __name__ == "__main__":'
    if marker not in text:
        return text
    helper = (
        f"\n\n# {MARKER}\n"
        "def _schedule_ai_experiment_menu_button(window):\n"
        "    try:\n"
        "        from app.home_menu_patch import schedule_ai_experiment_menu_button\n"
        "        schedule_ai_experiment_menu_button(window)\n"
        "    except Exception:\n"
        "        pass\n"
    )
    return text.replace(marker, helper + "\n" + marker, 1)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: patch_main_menu_button_05.py <project_dir>")
        return 1

    project_dir = Path(argv[1]).resolve()
    main_py = project_dir / "app" / "main.py"
    if not main_py.exists():
        print(f"ERROR: missing {main_py}")
        return 1

    ok, message = patch_main_py(main_py)
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
