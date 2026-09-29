from dataclasses import fields

from PySide6.QtWidgets import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QLabel, QMessageBox, QScrollArea, QSpinBox, QTabWidget, QVBoxLayout, QWidget


class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processing settings")
        self.resize(620, 670)
        self.settings = settings.clone()
        layout = QVBoxLayout(self)
        note = QLabel("All values belong to the selected file. Original algorithm defaults are preserved.")
        note.setWordWrap(True)
        layout.addWidget(note)
        tabs = QTabWidget()
        layout.addWidget(tabs)
        forms = {}
        self.controls = {}
        config = self.settings.config()
        for group in ("General", "Subject", "Holes", "Guidance", "Keying", "Research"):
            page = QWidget()
            form = QFormLayout(page)
            form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(page)
            tabs.addTab(scroll, group)
            forms[group] = form
        for field in fields(config):
            name = field.name
            if name in {"mode", "overlay_method", "sample_regions", "export_format"}:
                continue
            value = getattr(config, name)
            group = "General"
            for prefix, category in [("subject_", "Subject"), ("lipc_", "Subject"), ("sdr_", "Subject"), ("osa_", "Subject"), ("chhc_", "Holes"), ("hole_", "Holes"), ("srf_", "Guidance"), ("chroma_", "Keying"), ("checkerboard_", "Keying"), ("despill_", "Keying"), ("const_", "Research")]:
                if name.startswith(prefix):
                    group = category
                    break
            if type(value) is bool:
                widget = QCheckBox()
                widget.setChecked(value)
            elif type(value) is int:
                widget = QSpinBox()
                widget.setRange(-1 if name.startswith("checkerboard_offset_") else 0, 100000)
                widget.setValue(value)
            elif type(value) is float:
                widget = QDoubleSpinBox()
                widget.setDecimals(4)
                widget.setRange(0, 100000)
                widget.setSingleStep(0.05)
                widget.setValue(value)
            else:
                widget = QComboBox()
                widget.addItems(["HTP", "lite"] if name == "osa_mode" else ["auto", "green", "blue", "none"])
                widget.setCurrentText(value)
            widget.setToolTip(name)
            forms[group].addRow(name.replace("_", " ").capitalize(), widget)
            self.controls[name] = widget
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        candidate = self.settings.clone()
        for name, widget in self.controls.items():
            if isinstance(widget, QCheckBox):
                value = widget.isChecked()
            elif isinstance(widget, QComboBox):
                value = widget.currentText()
            else:
                value = widget.value()
            candidate.parameters[name] = value
        try:
            candidate.config()
        except ValueError as exc:
            QMessageBox.warning(self, "Check settings", str(exc))
            return
        self.settings = candidate
        super().accept()
