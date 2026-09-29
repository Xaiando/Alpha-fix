"""Render the app's own widgets to PNG for visual review (no screen capture)."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
import time
import cv2
import numpy as np
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from alpha_fix.media import write_png
from alpha_fix.project import MediaItem, Settings
from alpha_fix.service import preview
from alpha_fix.ui.app import MainWindow
from alpha_fix.ui.theme import apply_theme

root = Path(__file__).resolve().parents[1]
output = root / "docs/screenshots"
output.mkdir(parents=True, exist_ok=True)
app = QApplication([])
apply_theme(app)
window = MainWindow()
window.resize(1440, 940)
window.show()
app.processEvents()
window.grab().save(str(output / "workspace-empty.png"))

# A generated geometric fixture, independent of the user's private benchmark artwork.
h, w = 540, 900
frame = np.full((h, w, 3), (34, 29, 24), np.uint8)
cv2.rectangle(frame, (26, 24), (w-27, h-25), (92, 185, 165), 3)
cv2.rectangle(frame, (44, 72), (w-45, h-56), (16, 15, 14), -1)
cv2.rectangle(frame, (44, 72), (w-45, h-56), (119, 214, 189), 7)
cv2.putText(frame, "ALPHA FIX", (52, 53), cv2.FONT_HERSHEY_SIMPLEX, .72, (182, 224, 213), 2, cv2.LINE_AA)
cv2.putText(frame, "STREAM OVERLAY", (620, 53), cv2.FONT_HERSHEY_SIMPLEX, .45, (171, 186, 181), 1, cv2.LINE_AA)
cv2.putText(frame, "YOUR NEXT SCENE", (310, h-27), cv2.FONT_HERSHEY_SIMPLEX, .46, (142, 180, 168), 1, cv2.LINE_AA)
cv2.rectangle(frame, (650, 360), (828, 449), (56, 112, 100), -1)
cv2.putText(frame, "LIVE", (700, 411), cv2.FONT_HERSHEY_SIMPLEX, .7, (196, 239, 227), 2, cv2.LINE_AA)
asset = root / "examples/stream-frame.png"
asset.parent.mkdir(exist_ok=True)
write_png(asset, frame)
settings = Settings(parameters={"border_clusters": 1, "hole_dark_max": .2, "hole_flat_max": .08})
window.project.items = [MediaItem(asset, settings)]
window.refresh_queue()
window.queue.setCurrentRow(0)
deadline = time.monotonic() + 20
while window.worker and time.monotonic() < deadline:
    app.processEvents()
    QTest.qWait(15)
assert not window.worker
app.processEvents()
window.grab().save(str(output / "workspace-preview.png"))
window.project.output_dir = root / "exports"
window.project.save(root / "examples/Demo.afix")
window.dirty = False
window.close()
print(output)
