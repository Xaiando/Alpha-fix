from __future__ import annotations

import copy
import json
import logging
import os
import sys
from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QCloseEvent, QDesktopServices, QIcon, QKeySequence
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QProgressBar, QPushButton, QScrollArea, QSlider, QSpinBox, QSplitter, QStatusBar, QVBoxLayout, QWidget

from .. import __version__
from ..media import MEDIA_SUFFIXES, discover_media
from ..project import FORMATS, METHODS, MediaItem, Project, Settings, atomic_json
from ..samples import load_sample_regions
from ..service import export_batch, preview
from .canvas import PreviewCanvas
from .settings_dialog import SettingsDialog
from .theme import apply_theme
from .worker import Worker


def label(text, style=None, wrap=False):
    widget = QLabel(text)
    if style:
        widget.setObjectName(style)
    widget.setWordWrap(wrap)
    return widget


def button(text, callback, primary=False):
    widget = QPushButton(text)
    widget.clicked.connect(callback)
    if primary:
        widget.setObjectName("primary")
    return widget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.project = Project()
        self.project_path = None
        self.dirty = False
        self.worker = None
        self.closing = False
        self.loading = False
        self.last_preview = None
        self.export_indices = []
        self.preferences = QSettings("AlphaFix", "AlphaFix3")
        self.resize(1440, 940)
        self.setWindowIcon(QIcon(str(Path(__file__).resolve().parents[1] / "assets" / "alpha-fix.svg")))
        self.setMinimumSize(1120, 720)
        self.setAcceptDrops(True)
        self.build_ui()
        self.sync_title()
        self.set_current_enabled(False)
        geometry = self.preferences.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.header = QWidget()
        self.header.setObjectName("header")
        head = QHBoxLayout(self.header)
        head.setContentsMargins(22, 16, 22, 16)
        head.addWidget(label("α  Alpha Fix", "brand"))
        head.addSpacing(12)
        head.addWidget(label("3.0  /  WORKSPACE", "eyebrow"))
        head.addStretch()
        head.addWidget(button("Open project", self.open_project))
        head.addWidget(button("Save project", self.save_project))
        head.addWidget(button("+ Add files", self.add_files, True))
        head.addWidget(button("Add folder", self.add_folder))
        layout.addWidget(self.header)

        splitter = QSplitter()
        layout.addWidget(splitter, 1)
        self.left = QWidget()
        self.left.setMinimumWidth(190)
        left = QVBoxLayout(self.left)
        left.setContentsMargins(16, 14, 16, 14)
        self.queue_count = label("MEDIA QUEUE  ·  0", "eyebrow")
        left.addWidget(self.queue_count)
        left.addWidget(label("Your working files", "section"))
        self.queue = QListWidget()
        self.queue.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.queue.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.queue.currentRowChanged.connect(self.select_item)
        left.addWidget(self.queue, 1)
        left.addWidget(button("Remove selected", self.remove_item))
        left.addWidget(button("Apply settings to all", self.apply_all))
        left.addSpacing(14)
        left.addWidget(label("KEEP YOUR DETAIL", "eyebrow"))
        left.addWidget(label("Mark background to remove and details to keep. Every file remembers its own samples.", "muted", True))
        left.addSpacing(10)
        left.addWidget(label("PNG · JPG · WEBP · TIFF\nMP4 · MOV · MKV · WEBM", "muted"))
        splitter.addWidget(self.left)

        center = QWidget()
        central = QVBoxLayout(center)
        central.setContentsMargins(18, 14, 18, 16)
        self.filename = label("Preview workspace", "section")
        central.addWidget(self.filename)
        self.metadata = label("Compare the source with the cleaned alpha result.", "muted")
        central.addWidget(self.metadata)
        views = QHBoxLayout()
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Compare", "Result", "Original", "Alpha matte"])
        self.view_combo.currentTextChanged.connect(self.change_view)
        views.addWidget(self.view_combo)
        self.background_combo = QComboBox()
        self.background_combo.addItems(["Checkerboard", "Black", "White", "Green"])
        self.background_combo.currentTextChanged.connect(self.change_background)
        views.addWidget(self.background_combo)
        views.addStretch()
        self.guides_toggle = QCheckBox("Guides")
        self.guides_toggle.setChecked(True)
        self.guides_toggle.toggled.connect(self.toggle_guides)
        views.addWidget(self.guides_toggle)
        self.fit_button = button("Fit", lambda: self.canvas.fit())
        views.addWidget(self.fit_button)
        central.addLayout(views)
        self.canvas = PreviewCanvas()
        self.canvas.sample_added.connect(self.add_sample)
        self.canvas.open_requested.connect(self.add_files)
        central.addWidget(self.canvas, 1)
        timeline = QHBoxLayout()
        timeline.addWidget(label("FRAME", "eyebrow"))
        self.scrubber = QSlider(Qt.Orientation.Horizontal)
        self.scrubber.setRange(0, 0)
        self.scrubber.valueChanged.connect(lambda value: self.frame_number.setValue(value + 1))
        self.scrubber.sliderReleased.connect(self.run_preview)
        timeline.addWidget(self.scrubber, 1)
        self.frame_number = QSpinBox()
        self.frame_number.setRange(1, 1)
        self.frame_number.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.frame_number.setFixedWidth(70)
        self.frame_number.valueChanged.connect(lambda value: self.scrubber.setValue(value - 1))
        self.frame_number.editingFinished.connect(self.run_preview)
        timeline.addWidget(self.frame_number)
        self.preview_button = button("Update preview", self.run_preview, True)
        timeline.addWidget(self.preview_button)
        central.addLayout(timeline)
        central.addWidget(label("Drag the divider to compare · Scroll to zoom · Middle-drag to pan · Double-click to fit", "muted", True))
        splitter.addWidget(center)

        self.right = QScrollArea()
        self.right.setWidgetResizable(True)
        self.right.setMinimumWidth(290)
        panel = QWidget()
        right = QVBoxLayout(panel)
        right.setContentsMargins(16, 14, 16, 16)
        right.addWidget(label("PROCESSING", "eyebrow"))
        self.engine_badge = label("OPERATOR  /  ORIGINAL V2", "badge")
        right.addWidget(self.engine_badge)
        form = QFormLayout()
        self.engine_combo = QComboBox()
        self.engine_combo.addItem("Operator", "operator")
        self.engine_combo.addItem("Research", "research")
        self.engine_combo.currentIndexChanged.connect(self.change_engine)
        form.addRow("Engine", self.engine_combo)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Overlay", "overlay")
        self.mode_combo.addItem("Subject", "subject")
        self.mode_combo.currentIndexChanged.connect(self.change_mode)
        form.addRow("Mode", self.mode_combo)
        self.method_combo = QComboBox()
        self.method_combo.currentIndexChanged.connect(self.change_method)
        form.addRow("Method", self.method_combo)
        right.addLayout(form)
        self.method_note = label("", "muted", True)
        right.addWidget(self.method_note)
        right.addWidget(button("Advanced settings…", self.advanced_settings))
        right.addWidget(button("Reset processing defaults", self.reset_settings))
        right.addWidget(label("Guided samples", "section"))
        tools = QHBoxLayout()
        self.tool_combo = QComboBox()
        for text, data in [("Inspect", "inspect"), ("Remove background", "background"), ("Keep detail", "keep"), ("Basin / allowed area", "basin")]:
            self.tool_combo.addItem(text, data)
        self.tool_combo.currentIndexChanged.connect(self.change_tool)
        tools.addWidget(self.tool_combo)
        self.shape_combo = QComboBox()
        self.shape_combo.addItems(["Rectangle", "Ellipse"])
        self.shape_combo.currentTextChanged.connect(lambda text: setattr(self.canvas, "shape", text.lower()))
        tools.addWidget(self.shape_combo)
        right.addLayout(tools)
        self.sample_list = QListWidget()
        self.sample_list.setMaximumHeight(118)
        right.addWidget(self.sample_list)
        sample_actions = QHBoxLayout()
        sample_actions.addWidget(button("Delete", self.delete_sample))
        sample_actions.addWidget(button("Clear", self.clear_samples))
        right.addLayout(sample_actions)
        presets = QHBoxLayout()
        presets.addWidget(button("Load preset", self.load_preset))
        presets.addWidget(button("Save preset", self.save_preset))
        right.addLayout(presets)
        right.addWidget(label("Export", "section"))
        self.format_combo = QComboBox()
        for value, text in FORMATS.items():
            self.format_combo.addItem(text, value)
        self.format_combo.currentIndexChanged.connect(self.export_options_changed)
        right.addWidget(self.format_combo)
        output = QHBoxLayout()
        self.output_edit = QLineEdit(str(self.project.output_dir))
        self.output_edit.setToolTip("Parent folder. Each export creates its own run folder.")
        self.output_edit.editingFinished.connect(self.export_options_changed)
        output.addWidget(self.output_edit)
        output.addWidget(button("…", self.choose_output))
        right.addLayout(output)
        right.addWidget(button("Export selected", lambda: self.run_export(False)))
        right.addWidget(button("Export queue", lambda: self.run_export(True), True))
        right.addWidget(button("Open output folder", self.open_output))
        right.addWidget(label("Each export gets a new folder. Original files stay in place.", "muted", True))
        right.addStretch()
        self.right.setWidget(panel)
        splitter.addWidget(self.right)
        splitter.setSizes([220, 860, 320])
        splitter.setStretchFactor(1, 1)
        footer = QWidget()
        foot = QHBoxLayout(footer)
        foot.setContentsMargins(20, 9, 20, 9)
        self.status = label("Ready · Add media to begin", "muted")
        foot.addWidget(self.status, 1)
        self.progress = QProgressBar()
        self.progress.setFixedWidth(160)
        self.progress.setTextVisible(False)
        foot.addWidget(self.progress)
        self.cancel_button = button("Cancel", self.cancel_work)
        self.cancel_button.setEnabled(False)
        foot.addWidget(self.cancel_button)
        layout.addWidget(footer)
        self.setStatusBar(QStatusBar())
        self.statusBar().hide()
        for key, callback in [("Ctrl+O", self.add_files), ("Ctrl+S", self.save_project), ("Ctrl+Shift+S", lambda: self.save_project(True)), ("Ctrl+Return", self.run_preview)]:
            action = QAction(self)
            action.setShortcut(QKeySequence(key))
            action.triggered.connect(callback)
            self.addAction(action)

    def current_item(self):
        index = self.queue.currentRow()
        return self.project.items[index] if 0 <= index < len(self.project.items) else None

    def sync_title(self):
        name = self.project_path.stem if self.project_path else "Untitled project"
        self.setWindowTitle(f"{'* ' if self.dirty else ''}{name} — Alpha Fix {__version__}")

    def mark_dirty(self):
        self.dirty = True
        self.sync_title()

    def set_current_enabled(self, enabled):
        self.right.setEnabled(enabled)
        self.preview_button.setEnabled(enabled)
        self.scrubber.setEnabled(enabled)
        self.frame_number.setEnabled(enabled)

    def refresh_queue(self):
        row = self.queue.currentRow()
        self.queue.blockSignals(True)
        self.queue.clear()
        for item in self.project.items:
            entry = QListWidgetItem(f"{item.path.name}\n{item.status}")
            entry.setToolTip(str(item.path))
            self.queue.addItem(entry)
        self.queue.setCurrentRow(min(row, len(self.project.items) - 1))
        self.queue.blockSignals(False)
        self.queue_count.setText(f"MEDIA QUEUE  ·  {len(self.project.items)}")

    def add_paths(self, paths):
        if self.worker:
            return
        existing = {item.path.resolve() for item in self.project.items}
        first_new = len(self.project.items)
        for path in paths:
            path = Path(path).resolve()
            if path not in existing and path.suffix.lower() in MEDIA_SUFFIXES:
                self.project.items.append(MediaItem(path))
                existing.add(path)
        self.refresh_queue()
        if first_new < len(self.project.items):
            self.mark_dirty()
            self.queue.setCurrentRow(first_new)
        else:
            self.status.setText("No new supported media files found.")

    def add_files(self):
        if self.worker:
            return
        paths, _ = QFileDialog.getOpenFileNames(self, "Add images or videos", "", "Media (" + " ".join('*' + s for s in sorted(MEDIA_SUFFIXES)) + ")")
        if paths:
            self.add_paths(paths)

    def add_folder(self):
        if self.worker:
            return
        directory = QFileDialog.getExistingDirectory(self, "Add media folder")
        if directory:
            try:
                self.add_paths(discover_media(Path(directory), self.project.output_dir))
            except Exception as exc:
                self.show_error(str(exc))

    def select_item(self, row):
        if self.worker:
            return
        item = self.current_item()
        self.set_current_enabled(item is not None)
        self.last_preview = None
        self.canvas.set_preview(None)
        if item is None:
            self.filename.setText("Preview workspace")
            self.metadata.setText("Add an image or video to begin.")
            return
        self.filename.setText(item.path.name)
        self.filename.setToolTip(str(item.path))
        self.scrubber.setRange(0, 0)
        self.frame_number.setRange(1, 1)
        self.load_controls()
        self.run_preview()

    def load_controls(self):
        item = self.current_item()
        if not item:
            return
        self.loading = True
        self.engine_combo.setCurrentIndex(self.engine_combo.findData(item.settings.engine))
        self.mode_combo.setCurrentIndex(self.mode_combo.findData(item.settings.mode))
        self.method_combo.clear()
        for value, title in METHODS[item.settings.engine].items():
            self.method_combo.addItem(title, value)
        self.method_combo.setCurrentIndex(self.method_combo.findData(item.settings.method))
        self.tool_combo.setCurrentIndex(0)
        self.canvas.tool = "inspect"
        self.tool_combo.model().item(3).setEnabled(item.settings.engine == "research")
        self.engine_badge.setText("OPERATOR  /  ORIGINAL V2" if item.settings.engine == "operator" else "RESEARCH  /  EXPERIMENTAL")
        self.method_combo.setEnabled(item.settings.mode == "overlay")
        self.update_method_note()
        self.refresh_samples()
        self.loading = False

    def update_method_note(self):
        settings = self.current_item().settings
        notes = {"auto_hole": "Find enclosed background openings automatically.", "radfield": "Draw background and keep samples to guide the matte.", "chroma": "Remove the configured key color inside the portal range.", "checkerboard": "Remove a baked checkerboard. Tune tile size in advanced settings.", "chhc": "Carve enclosed holes while preserving the frame.", "constellation": "Research: sampled color families seed a global geodesic flood.", "bounded_geodesic": "Research: draw a basin and a background sample. Removal stays inside the authored basin; keep samples protect detail."}
        self.method_note.setText("Separate a subject from its backdrop with temporal smoothing and halo suppression." if settings.mode == "subject" else notes[settings.method])

    def invalidate(self):
        self.mark_dirty()
        self.status.setText("Settings changed · Update preview to review the result.")

    def change_engine(self):
        if self.loading or not self.current_item():
            return
        item = self.current_item()
        engine = self.engine_combo.currentData()
        item.settings = Settings(engine=engine, mode=item.settings.mode, method="auto_hole" if engine == "operator" else "bounded_geodesic", samples=item.settings.samples.copy())
        self.load_controls()
        self.invalidate()

    def change_mode(self):
        if self.loading or not self.current_item():
            return
        self.current_item().settings.mode = self.mode_combo.currentData()
        self.load_controls()
        self.invalidate()

    def change_method(self):
        if self.loading or not self.current_item():
            return
        self.current_item().settings.method = self.method_combo.currentData()
        self.update_method_note()
        self.invalidate()

    def change_tool(self):
        self.canvas.tool = self.tool_combo.currentData()
        if self.canvas.tool != "inspect":
            self.guides_toggle.setChecked(True)
            self.view_combo.setCurrentText("Original")

    def toggle_guides(self, checked):
        self.canvas.show_samples = checked
        self.canvas.update()

    def change_view(self, text):
        self.canvas.view = text
        self.canvas.rebuild()

    def change_background(self, text):
        self.canvas.background = text
        self.canvas.rebuild()

    def refresh_samples(self):
        item = self.current_item()
        self.sample_list.clear()
        samples = item.settings.samples if item else []
        for index, sample in enumerate(samples, 1):
            self.sample_list.addItem(f"{index} · {sample.kind.capitalize()} · {sample.shape}")
        self.canvas.samples = list(samples)
        self.canvas.update()

    def add_sample(self, sample):
        if self.current_item() and not self.worker:
            self.current_item().settings.samples.append(sample)
            self.refresh_samples()
            self.invalidate()

    def delete_sample(self):
        row = self.sample_list.currentRow()
        if row >= 0:
            self.current_item().settings.samples.pop(row)
            self.refresh_samples()
            self.invalidate()

    def clear_samples(self):
        self.current_item().settings.samples.clear()
        self.refresh_samples()
        self.invalidate()

    def advanced_settings(self):
        dialog = SettingsDialog(self.current_item().settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.current_item().settings = dialog.settings
            self.invalidate()

    def reset_settings(self):
        old = self.current_item().settings
        self.current_item().settings = Settings(old.engine, old.mode, old.method, samples=old.samples.copy())
        self.load_controls()
        self.invalidate()

    def remove_item(self):
        row = self.queue.currentRow()
        if row < 0:
            return
        self.project.items.pop(row)
        self.refresh_queue()
        self.mark_dirty()
        self.select_item(self.queue.currentRow())

    def apply_all(self):
        item = self.current_item()
        if item:
            for other in self.project.items:
                other.settings = item.settings.clone()
            self.mark_dirty()
            self.status.setText(f"Settings and samples applied to {len(self.project.items)} files.")

    def load_preset(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load settings or legacy samples", "", "JSON presets (*.json)")
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
            if data.get("type") == "alpha-fix-preset":
                if data.get("version") != 1:
                    raise ValueError("Unsupported preset version.")
                self.current_item().settings = Settings.from_dict(data["settings"])
            else:
                self.current_item().settings.samples = load_sample_regions(path)
            self.load_controls()
            self.invalidate()
        except Exception as exc:
            self.show_error(str(exc))

    def save_preset(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save processing preset", "alpha-fix-preset.json", "JSON (*.json)")
        if path:
            try:
                atomic_json(Path(path), {"type": "alpha-fix-preset", "version": 1, "settings": self.current_item().settings.to_dict()})
            except Exception as exc:
                self.show_error(str(exc))

    def export_options_changed(self):
        if not self.loading:
            self.project.output_dir = Path(self.output_edit.text().strip() or str(Path.home() / "Videos" / "Alpha Fix Exports"))
            self.project.export_format = self.format_combo.currentData()
            self.mark_dirty()

    def choose_output(self):
        path = QFileDialog.getExistingDirectory(self, "Export destination", str(self.project.output_dir))
        if path:
            self.output_edit.setText(path)
            self.export_options_changed()

    def open_output(self):
        item = self.current_item()
        path = item.output if item and item.output else self.project.output_dir
        if path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        else:
            self.status.setText("The output folder will be created when you export.")

    def start_work(self, task, completed):
        if self.worker:
            return
        self.worker = Worker(task, self)
        self.worker.result.connect(completed)
        self.worker.failed.connect(self.work_failed)
        self.worker.progress.connect(self.work_progress)
        self.worker.item_finished.connect(self.item_exported)
        self.worker.finished.connect(self.work_finished)
        self.header.setEnabled(False)
        self.left.setEnabled(False)
        self.set_current_enabled(False)
        self.canvas.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress.setRange(0, 0)
        self.worker.start()

    def run_preview(self):
        item = self.current_item()
        if self.worker or item is None:
            return
        source, settings = item.path, item.settings.clone()
        index = self.scrubber.value()
        self.status.setText("Building preview…")
        self.start_work(lambda worker: preview(source, settings, index, worker.cancel, worker.progress.emit), self.preview_ready)

    def preview_ready(self, result):
        self.last_preview = result
        self.canvas.set_preview(result)
        self.canvas.samples = list(self.current_item().settings.samples)
        self.canvas.update()
        self.metadata.setText(f"{result.info.width} × {result.info.height}  ·  " + ("Still image" if result.info.is_image else f"{result.info.fps:.3f} fps  ·  {result.info.frames} frames") + "  ·  Full resolution")
        max_frame = max(result.info.frames, result.frame_index + 1, 1)
        self.scrubber.setRange(0, max_frame - 1)
        self.frame_number.setRange(1, max_frame)
        self.frame_number.setValue(result.frame_index + 1)
        selected = self.view_combo.currentText()
        self.view_combo.blockSignals(True)
        self.view_combo.clear()
        self.view_combo.addItems(["Compare", "Result", "Original", "Alpha matte"] + ["Debug: " + name for name in getattr(result.result, "debug_views", {})])
        self.view_combo.setCurrentText(selected if self.view_combo.findText(selected) >= 0 else "Compare")
        self.view_combo.blockSignals(False)
        self.change_view(self.view_combo.currentText())
        self.status.setText(f"Preview ready · Frame {result.frame_index + 1}")

    def run_export(self, all_items):
        if self.worker or not self.project.items:
            return
        self.export_options_changed()
        self.export_indices = list(range(len(self.project.items))) if all_items else [self.queue.currentRow()]
        if self.export_indices == [-1]:
            return
        items = copy.deepcopy([self.project.items[index] for index in self.export_indices])
        target, format = self.project.output_dir, self.project.export_format
        for index in self.export_indices:
            self.project.items[index].status = "Queued"
        self.refresh_queue()
        self.status.setText("Starting export…")
        self.start_work(lambda worker: export_batch(items, target, format, worker.cancel, worker.progress.emit, worker.item_finished.emit), self.export_ready)

    def item_exported(self, record):
        item = self.project.items[self.export_indices[record["index"]]]
        item.status = record["status"]
        if record.get("output"):
            item.output = record["output"]
        if record.get("error"):
            item.status = "Failed · " + record["error"][:80]
            logging.error("Export %s: %s", item.path, record["error"])
        self.refresh_queue()

    def export_ready(self, results):
        failed = [record for record in results if record["status"] == "Failed"]
        self.status.setText(f"Export complete · {len(results) - len(failed)} succeeded · {len(failed)} failed")
        if failed:
            self.show_error("\n\n".join(record["error"] for record in failed))

    def work_progress(self, done, total, message):
        self.progress.setRange(0, total if total > 0 else 0)
        self.progress.setValue(done)
        self.status.setText(f"{message} · {done}/{total or '?'}")

    def work_failed(self, message, detail):
        self.status.setText(message)
        if detail:
            logging.error(detail)
            self.show_error(message)

    def work_finished(self):
        finished = self.worker
        self.worker = None
        finished.deleteLater()
        self.header.setEnabled(True)
        self.left.setEnabled(True)
        self.set_current_enabled(self.current_item() is not None)
        self.canvas.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        for item in self.project.items:
            if item.status == "Queued":
                item.status = "Not exported"
        self.refresh_queue()
        if self.closing:
            self.closing = False
            self.close()

    def cancel_work(self):
        if self.worker:
            self.worker.cancel.set()
            self.cancel_button.setEnabled(False)
            self.status.setText("Cancelling after the current processing step…")

    def show_error(self, message):
        QMessageBox.warning(self, "Alpha Fix", message)

    def save_project(self, save_as=False):
        if self.worker:
            return False
        path = self.project_path
        if path is None or save_as:
            selected, _ = QFileDialog.getSaveFileName(self, "Save Alpha Fix project", str(path or "Untitled.afix"), "Alpha Fix project (*.afix)")
            if not selected:
                return False
            path = Path(selected).with_suffix(".afix")
        try:
            self.project.save(path)
            self.project_path = path
            self.dirty = False
            self.sync_title()
            self.status.setText(f"Saved {path.name}")
            return True
        except Exception as exc:
            self.show_error(str(exc))
            return False

    def confirm_discard(self):
        if not self.dirty:
            return True
        choice = QMessageBox.question(self, "Save project changes?", "Save the current files, processing settings and samples before continuing?", QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Save)
        if choice == QMessageBox.StandardButton.Cancel:
            return False
        return self.save_project() if choice == QMessageBox.StandardButton.Save else True

    def open_project(self, path=None):
        if self.worker:
            return
        if not path:
            selected, _ = QFileDialog.getOpenFileName(self, "Open Alpha Fix project", "", "Alpha Fix project (*.afix)")
            if not selected:
                return
            path = Path(selected)
        try:
            project = Project.load(Path(path))
            if not self.confirm_discard():
                return
            self.project = project
            self.project_path = Path(path)
            self.dirty = False
            self.sync_title()
            self.loading = True
            self.output_edit.setText(str(project.output_dir))
            self.format_combo.setCurrentIndex(self.format_combo.findData(project.export_format))
            self.loading = False
            self.queue.blockSignals(True)
            self.queue.setCurrentRow(-1)
            self.queue.blockSignals(False)
            self.refresh_queue()
            if project.items:
                self.queue.setCurrentRow(0)
            else:
                self.select_item(-1)
        except Exception as exc:
            self.show_error(str(exc))

    def dragEnterEvent(self, event):
        if not self.worker and event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                path = Path(url.toLocalFile())
                if path.suffix.lower() == ".afix":
                    self.open_project(path)
                    return
                try:
                    paths.extend(discover_media(path, self.project.output_dir))
                except Exception as exc:
                    self.show_error(str(exc))
        self.add_paths(paths)
        event.acceptProposedAction()

    def closeEvent(self, event: QCloseEvent):
        if self.worker:
            self.closing = True
            self.cancel_work()
            event.ignore()
            return
        if not self.confirm_discard():
            event.ignore()
            return
        self.preferences.setValue("geometry", self.saveGeometry())
        event.accept()


def launch(project_path=None, input_path=None):
    log_dir = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "AlphaFix" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=log_dir / "alpha-fix.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("Alpha Fix")
    app.setApplicationVersion(__version__)
    apply_theme(app)
    window = MainWindow()
    window.show()
    if project_path:
        QTimer.singleShot(0, lambda: window.open_project(project_path))
    elif input_path:
        QTimer.singleShot(0, lambda: window.add_paths(discover_media(input_path, window.project.output_dir)))
    return app.exec()
