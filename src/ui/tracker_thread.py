from PySide6.QtCore import QThread, Signal
from config import Config # type:ignore
from aimbot import Tracker # type:ignore

class TrackerThread(QThread):
    started_successfully = Signal()
    stopped = Signal()

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.tracker = None
        self._running = False

    def run(self):
        self._running = True
        self.tracker = Tracker(self.config)
        self.started_successfully.emit()
        self.tracker.run()
        self._running = False
        self.stopped.emit()

    def stop(self):
        if self.tracker:
            self.tracker.exit.clear()

    def sync_config(self) -> bool:
        if self.tracker:
            return self.tracker.update()
        return False
