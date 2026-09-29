from __future__ import annotations

import cv2
import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ..samples import SampleRegion


def qimage(array: np.ndarray) -> QImage:
    data = np.ascontiguousarray(array, dtype=np.uint8)
    fmt = QImage.Format.Format_RGBA8888 if data.shape[2] == 4 else QImage.Format.Format_RGB888
    return QImage(data.data, data.shape[1], data.shape[0], data.strides[0], fmt).copy()


class PreviewCanvas(QWidget):
    sample_added = Signal(object)
    zoom_changed = Signal(str)
    open_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setMinimumSize(360, 280)
        self.preview = None
        self.source_image = self.result_image = None
        self.samples = []
        self.show_samples = True
        self.tool = "inspect"
        self.shape = "rectangle"
        self.view = "Compare"
        self.background = "Checkerboard"
        self.zoom = 1.0
        self.pan = QPointF()
        self.start = self.end = None
        self.pan_start = None
        self.split = 0.5
        self.setMouseTracking(True)

    def set_preview(self, preview):
        self.preview = preview
        self.zoom = 1.0
        self.pan = QPointF()
        self.rebuild()

    def fit(self):
        self.zoom = 1.0
        self.pan = QPointF()
        self.update()

    def rebuild(self):
        if self.preview is None:
            self.source_image = self.result_image = None
            self.update()
            return
        frame = self.preview.frame
        rgba = self.preview.result.rgba
        h, w = rgba.shape[:2]
        if self.background == "Checkerboard":
            yy, xx = np.indices((h, w))
            tiles = (((xx // 16 + yy // 16) % 2) * 12 + 37).astype(np.uint8)
            bg = np.repeat(tiles[:, :, None], 3, axis=2)
        else:
            color = {"Black": (0, 0, 0), "White": (255, 255, 255), "Green": (0, 255, 0)}[self.background]
            bg = np.full((h, w, 3), color, dtype=np.uint8)
        alpha = rgba[:, :, 3:4].astype(np.float32) / 255
        composite = np.clip(rgba[:, :, :3] * alpha + bg * (1 - alpha), 0, 255).astype(np.uint8)
        source = cv2.cvtColor(frame[:, :, :3], cv2.COLOR_BGR2RGB)
        if frame.shape[2] == 4:
            original_alpha = frame[:, :, 3:4].astype(np.float32) / 255
            source = (source * original_alpha + bg * (1 - original_alpha)).astype(np.uint8)
        self.source_image = qimage(source)
        if self.view == "Alpha matte":
            matte = np.clip(self.preview.result.alpha * 255, 0, 255).astype(np.uint8)
            composite = np.repeat(matte[:, :, None], 3, axis=2)
        elif self.view.startswith("Debug: "):
            name = self.view.removeprefix("Debug: ")
            debug = getattr(self.preview.result, "debug_views", {}).get(name)
            if debug is not None:
                debug = np.nan_to_num(debug.astype(np.float32))
                if debug.ndim == 2:
                    if debug.min() < 0 or debug.max() > 1:
                        debug = cv2.normalize(debug, None, 0, 1, cv2.NORM_MINMAX)
                    composite = np.repeat(np.clip(debug * 255, 0, 255).astype(np.uint8)[:, :, None], 3, axis=2)
                else:
                    composite = np.clip(debug * (255 if debug.max() <= 1 else 1), 0, 255).astype(np.uint8)[:, :, :3]
        self.result_image = qimage(composite)
        self.update()

    def image_rect(self):
        if self.source_image is None:
            return QRectF()
        width, height = self.source_image.width(), self.source_image.height()
        scale = min((self.width() - 32) / width, (self.height() - 52) / height) * self.zoom
        w, h = width * scale, height * scale
        return QRectF((self.width() - w) / 2 + self.pan.x(), (self.height() - h) / 2 + self.pan.y(), w, h)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#0e1217"))
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if self.source_image is None:
            painter.setPen(QColor("#75ddbd"))
            painter.setFont(QFont("Segoe UI", 45, QFont.Weight.Light))
            painter.drawText(self.rect().adjusted(0, -110, 0, 0), Qt.AlignmentFlag.AlignCenter, "α")
            painter.setFont(QFont("Segoe UI", 19, QFont.Weight.DemiBold))
            painter.setPen(QColor("#e0e8ee"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Make room for transparency")
            painter.setFont(QFont("Segoe UI", 11))
            painter.setPen(QColor("#8d9ba9"))
            painter.drawText(self.rect().adjusted(0, 72, 0, 0), Qt.AlignmentFlag.AlignCenter, "Drop an image or video here, or add files to get started.")
            return
        rect = self.image_rect()
        painter.drawImage(rect, self.source_image if self.view == "Original" else self.result_image)
        if self.view == "Compare":
            painter.save()
            painter.setClipRect(QRectF(rect.left(), rect.top(), rect.width() * self.split, rect.height()))
            painter.drawImage(rect, self.source_image)
            painter.restore()
            x = rect.left() + rect.width() * self.split
            painter.setPen(QPen(QColor("#95f0d3"), 2))
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            painter.setBrush(QColor("#95f0d3"))
            painter.drawEllipse(QPointF(x, rect.center().y()), 5, 12)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        regions = list(self.samples) if self.show_samples else []
        if self.start is not None and self.end is not None:
            regions.append(SampleRegion(self.tool, self.shape, *self.start, *self.end).normalized())
        for number, region in enumerate(regions, 1):
            color = QColor({"background": "#f37d78", "keep": "#78e6b1", "basin": "#e9c763"}[region.kind])
            box = QRectF(rect.x() + region.x0 * rect.width(), rect.y() + region.y0 * rect.height(), (region.x1 - region.x0) * rect.width(), (region.y1 - region.y0) * rect.height())
            painter.setPen(QPen(color, 2))
            fill = QColor(color)
            fill.setAlpha(25)
            painter.setBrush(fill)
            if region.shape == "ellipse":
                painter.drawEllipse(box)
            else:
                painter.drawRect(box)
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
            painter.drawText(box.topLeft() + QPointF(4, 14), f"{number} · {region.kind}")
        painter.setPen(QColor("#a6b2bf"))
        painter.setFont(QFont("Segoe UI", 9))
        left = "ORIGINAL" if self.view == "Compare" else self.view.upper()
        painter.drawText(16, 21, left)
        if self.view == "Compare":
            painter.drawText(self.width() - 115, 21, "ALPHA RESULT")

    def normalized(self, point):
        rect = self.image_rect()
        if rect.isEmpty():
            return None
        return (float(np.clip((point.x() - rect.x()) / rect.width(), 0, 1)), float(np.clip((point.y() - rect.y()) / rect.height(), 0, 1)))

    def mousePressEvent(self, event):
        if not self.preview or not self.image_rect().contains(event.position()):
            return
        if event.button() == Qt.MouseButton.MiddleButton:
            self.pan_start = event.position()
        elif event.button() == Qt.MouseButton.LeftButton:
            if self.tool != "inspect":
                self.start = self.end = self.normalized(event.position())
            elif self.view == "Compare":
                self.split = self.normalized(event.position())[0]
        self.update()

    def mouseMoveEvent(self, event):
        if self.pan_start is not None:
            self.pan += event.position() - self.pan_start
            self.pan_start = event.position()
        elif self.start is not None:
            self.end = self.normalized(event.position())
        elif event.buttons() & Qt.MouseButton.LeftButton and self.tool == "inspect" and self.view == "Compare" and self.preview:
            self.split = self.normalized(event.position())[0]
        self.update()

    def mouseReleaseEvent(self, event):
        self.pan_start = None
        if self.start is not None:
            sample = SampleRegion(self.tool, self.shape, *self.start, *self.end).normalized()
            self.start = self.end = None
            if sample.x1 - sample.x0 > 0.002 and sample.y1 - sample.y0 > 0.002:
                self.sample_added.emit(sample)
        self.update()

    def wheelEvent(self, event):
        if self.preview:
            self.zoom = float(np.clip(self.zoom * (1.15 if event.angleDelta().y() > 0 else 1 / 1.15), 0.25, 8))
            self.zoom_changed.emit(f"{self.zoom:.0%} of fit")
            self.update()

    def mouseDoubleClickEvent(self, event):
        if self.preview is None:
            self.open_requested.emit()
        else:
            self.fit()
