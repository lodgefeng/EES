# -*- coding: utf-8 -*-
"""Launch app.main with automatic home-menu button 05 injection."""

from __future__ import annotations

import runpy
import sys


def main() -> None:
    from app.home_menu_patch import activate_menu_patch_runtime

    activate_menu_patch_runtime()
    sys.argv = ["app.main", *sys.argv[1:]]
    runpy.run_module("app.main", run_name="__main__")


if __name__ == "__main__":
    main()
