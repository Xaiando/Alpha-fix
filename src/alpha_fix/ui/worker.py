import traceback
from threading import Event

from PySide6.QtCore import QThread, Signal

from ..service import Cancelled


class Worker(QThread):
    result = Signal(object)
    failed = Signal(str, str)
    progress = Signal(int, int, str)
    item_finished = Signal(object)

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.cancel = Event()

    def run(self):
        try:
            self.result.emit(self.task(self))
        except Cancelled as exc:
            self.failed.emit(str(exc), "")
        except Exception as exc:
            self.failed.emit(str(exc), traceback.format_exc())
