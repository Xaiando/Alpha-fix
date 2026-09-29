def apply_theme(app):
    """Use the platform font, with a fallback for Qt's headless render backend."""
    import os
    from pathlib import Path
    from PySide6.QtGui import QFontDatabase
    if "Segoe UI" not in QFontDatabase.families():
        font_dir = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        for name in ("segoeui.ttf", "segoeuib.ttf", "segoeuil.ttf"):
            path = font_dir / name
            if path.is_file():
                QFontDatabase.addApplicationFont(str(path))
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)


STYLE = """
QWidget { background: #13171d; color: #e3e8ee; font-family: 'Segoe UI'; font-size: 13px; }
QMainWindow { background: #101419; }
QWidget#header { background: #1a2028; border-bottom: 1px solid #2c3541; }
QLabel#brand { font-size: 24px; font-weight: 700; color: #f2f6fa; }
QWidget#header QLabel { background: transparent; }
QLabel#eyebrow { color: #8d9aa9; font-size: 11px; font-weight: 600; }
QLabel#muted { color: #8d9aa9; }
QLabel#section { font-size: 14px; font-weight: 600; padding-top: 10px; }
QLabel#badge { color: #70dcc1; background: #203b35; border-radius: 4px; padding: 5px 9px; }
QPushButton { background: #252d38; border: 1px solid #354150; border-radius: 5px; padding: 7px 12px; }
QPushButton:hover { background: #313e4c; border-color: #65788a; }
QPushButton:pressed, QPushButton:checked { background: #245547; border-color: #72d8b9; }
QPushButton#primary { color: #0d2820; background: #74dfbd; font-weight: 600; border: 1px solid #74dfbd; }
QPushButton#primary:hover { background: #97efd2; }
QPushButton:disabled { color: #637080; background: #1c232c; border-color: #293440; }
QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox { background: #1b222b; border: 1px solid #354150; padding: 6px; border-radius: 4px; min-height: 19px; }
QComboBox:focus, QLineEdit:focus { border-color: #74dfbd; }
QComboBox QAbstractItemView { background: #232c36; selection-background-color: #315549; }
QComboBox::drop-down { border: 0; width: 24px; }
QListWidget { background: #151a21; border: 1px solid #2b3542; border-radius: 5px; outline: none; }
QListWidget::item { padding: 10px 7px; border-bottom: 1px solid #242d38; }
QListWidget::item:selected { background: #264638; color: #c9f7e6; }
QListWidget::item:hover { background: #25313b; }
QScrollArea { border: 0; }
QScrollBar:vertical { background: #171d25; width: 9px; }
QScrollBar::handle:vertical { background: #3c4958; border-radius: 4px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QSplitter::handle { background: #2b3541; width: 1px; }
QProgressBar { background: #222c35; border: 0; border-radius: 3px; height: 7px; text-align: center; }
QProgressBar::chunk { background: #74dfbd; border-radius: 3px; }
QSlider::groove:horizontal { height: 4px; background: #35414d; border-radius: 2px; }
QSlider::handle:horizontal { background: #86e5c8; width: 12px; margin: -5px 0; border-radius: 6px; }
QTabWidget::pane { border: 1px solid #354150; }
QTabBar::tab { background: #242e39; padding: 8px 12px; }
QTabBar::tab:selected { background: #315549; }
QToolTip { background: #303c48; color: #f4f7fa; border: 1px solid #677e8d; padding: 5px; }
QStatusBar { background: #1a2028; color: #a1afbd; }
QCheckBox { spacing: 8px; }
"""
