from __future__ import annotations

import ctypes
import traceback
from pathlib import Path


def report_gui_exception(app_name: str, exc: BaseException, tb: object | None = None) -> None:
    trace = "".join(traceback.format_exception(type(exc), exc, tb or exc.__traceback__))
    log_name = app_name.lower().replace(" ", "_") + "_startup.log"
    log_path = Path.cwd() / log_name
    log_path.write_text(trace, encoding="utf-8")
    ctypes.windll.user32.MessageBoxW(
        0,
        f"{app_name} failed to start.\n\nDetails were written to:\n{log_path}",
        app_name,
        0x10,
    )
