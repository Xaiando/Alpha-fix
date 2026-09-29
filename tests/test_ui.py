import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import cv2
import numpy as np
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from alpha_fix.media import write_png
from alpha_fix.project import MediaItem, Project
from alpha_fix.ui.app import MainWindow
from alpha_fix.ui.settings_dialog import SettingsDialog
from alpha_fix.ui.theme import apply_theme


def wait_idle(app, window):
    deadline = time.monotonic() + 15
    while window.worker is not None and time.monotonic() < deadline:
        app.processEvents()
        QTest.qWait(10)
    assert window.worker is None, "Worker did not finish"
    app.processEvents()


def test_desktop_workflow_preview_samples_settings_export_and_project(tmp_path):
    app = QApplication.instance() or QApplication([])
    apply_theme(app)
    window = MainWindow()
    errors = []
    window.show_error = errors.append
    frame = np.full((160, 240, 3), 150, np.uint8)
    cv2.rectangle(frame, (20, 20), (220, 140), (40, 60, 190), 16)
    frame[40:120, 40:200] = 15
    source = tmp_path / "sample.png"
    write_png(source, frame)
    window.show()
    try:
        window.add_paths([source])
        wait_idle(app, window)
        assert window.last_preview is not None
        assert window.last_preview.info.width == 240
        assert window.right.isEnabled()
        window.tool_combo.setCurrentIndex(1)
        rect = window.canvas.image_rect()
        start = QPoint(int(rect.left() + rect.width() * .3), int(rect.top() + rect.height() * .3))
        end = QPoint(int(rect.left() + rect.width() * .5), int(rect.top() + rect.height() * .6))
        QTest.mousePress(window.canvas, Qt.MouseButton.LeftButton, pos=start)
        QTest.mouseMove(window.canvas, end)
        QTest.mouseRelease(window.canvas, Qt.MouseButton.LeftButton, pos=end)
        assert len(window.current_item().settings.samples) == 1
        assert window.current_item().settings.samples[0].kind == "background"
        window.engine_combo.setCurrentIndex(1)
        assert window.current_item().settings.engine == "research"
        assert window.current_item().settings.method == "bounded_geodesic"
        dialog = SettingsDialog(window.current_item().settings, window)
        dialog.controls["const_color_gate"].setValue(6.5)
        dialog.accept()
        assert dialog.settings.parameters["const_color_gate"] == 6.5
        window.current_item().settings = dialog.settings
        window.run_preview()
        wait_idle(app, window)
        assert window.last_preview is not None
        window.output_edit.setText(str(tmp_path / "exports"))
        window.run_export(True)
        wait_idle(app, window)
        assert window.project.items[0].status == "Exported"
        assert window.project.items[0].output.is_dir()
        window.project_path = tmp_path / "test.afix"
        assert window.save_project()
        window.open_project(window.project_path)
        wait_idle(app, window)
        assert window.current_item().settings.parameters["const_color_gate"] == 6.5
        assert len(window.current_item().settings.samples) == 1
        assert not errors
    finally:
        if window.worker:
            window.cancel_work()
            wait_idle(app, window)
        window.dirty = False
        window.close()


def test_opening_empty_project_clears_preview(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    path = tmp_path / "empty.afix"
    Project().save(path)
    window.open_project(path)
    app.processEvents()
    assert window.current_item() is None
    assert not window.right.isEnabled()
    window.close()
