"""Qt Stylesheet Definitions (Catppuccin Inspired)."""

DARK_STYLE = """
QMainWindow { background-color: #1e1e2e; }
QWidget { background-color: #1e1e2e; color: #cdd6f4; font-family: 'Segoe UI', sans-serif; font-size: 13px; }
QGroupBox { border: 1px solid #45475a; border-radius: 8px; margin-top: 12px; padding-top: 16px; font-weight: bold; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #89b4fa; }
QTextEdit { background-color: #313244; border: 1px solid #45475a; border-radius: 6px; padding: 8px; color: #cdd6f4; }
QLineEdit { background-color: #313244; border: 1px solid #45475a; border-radius: 6px; padding: 6px 10px; color: #cdd6f4; }
QLineEdit:focus { border-color: #89b4fa; }
QComboBox { background-color: #313244; border: 1px solid #45475a; border-radius: 6px; padding: 5px 10px; color: #cdd6f4; }
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView { background-color: #313244; color: #cdd6f4; selection-background-color: #45475a; }
QSpinBox, QDoubleSpinBox { background-color: #313244; border: 1px solid #45475a; border-radius: 6px; padding: 5px; color: #cdd6f4; }
QPushButton { background-color: #89b4fa; color: #1e1e2e; border: none; border-radius: 6px; padding: 8px 18px; font-weight: bold; }
QPushButton:hover { background-color: #74c7ec; }
QPushButton:pressed { background-color: #585b70; }
QPushButton:disabled { background-color: #45475a; color: #6c7086; }
QPushButton#danger { background-color: #f38ba8; }
QPushButton#danger:hover { background-color: #eba0ac; }
QPushButton#success { background-color: #a6e3a1; }
QPushButton#success:hover { background-color: #94e2d5; }
QPushButton#secondary { background-color: #45475a; color: #cdd6f4; }
QPushButton#secondary:hover { background-color: #585b70; }
QTabWidget::pane { border: 1px solid #45475a; border-radius: 8px; background-color: #1e1e2e; }
QTabBar::tab { background-color: #313244; color: #a6adc8; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:selected { background-color: #1e1e2e; color: #89b4fa; border-bottom: 2px solid #89b4fa; }
QTabBar::tab:hover { color: #cdd6f4; }
QMenuBar { background-color: #181825; color: #cdd6f4; }
QMenuBar::item:selected { background-color: #313244; }
QMenu { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; }
QMenu::item:selected { background-color: #45475a; }
QStatusBar { background-color: #181825; color: #a6adc8; }
QToolBar { background-color: #181825; border-bottom: 1px solid #313244; spacing: 6px; padding: 4px; }
QScrollBar:vertical { background-color: #1e1e2e; width: 10px; border-radius: 5px; }
QScrollBar::handle:vertical { background-color: #45475a; border-radius: 5px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QListWidget { background-color: #313244; border: 1px solid #45475a; border-radius: 6px; }
QListWidget::item { padding: 6px; }
QListWidget::item:selected { background-color: #45475a; color: #89b4fa; }
QProgressBar { background-color: #313244; border: 1px solid #45475a; border-radius: 6px; text-align: center; color: #cdd6f4; height: 20px; }
QProgressBar::chunk { background-color: #89b4fa; border-radius: 5px; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 2px solid #45475a; background-color: #313244; }
QCheckBox::indicator:checked { background-color: #89b4fa; border-color: #89b4fa; }
QRadioButton::indicator { width: 18px; height: 18px; border-radius: 9px; border: 2px solid #45475a; background-color: #313244; }
QRadioButton::indicator:checked { background-color: #89b4fa; border-color: #89b4fa; }
QSplitter::handle { background-color: #45475a; }
QLabel#header { font-size: 22px; font-weight: bold; color: #89b4fa; }
QLabel#subheader { font-size: 14px; color: #a6adc8; }
QLabel#stat { font-size: 16px; font-weight: bold; color: #f9e2af; }
"""

LIGHT_STYLE = """
QMainWindow { background-color: #eff1f5; }
QWidget { background-color: #eff1f5; color: #4c4f69; font-family: 'Segoe UI', sans-serif; font-size: 13px; }
QGroupBox { border: 1px solid #ccd0da; border-radius: 8px; margin-top: 12px; padding-top: 16px; font-weight: bold; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #1e66f5; }
QTextEdit { background-color: #ffffff; border: 1px solid #ccd0da; border-radius: 6px; padding: 8px; color: #4c4f69; }
QLineEdit { background-color: #ffffff; border: 1px solid #ccd0da; border-radius: 6px; padding: 6px 10px; color: #4c4f69; }
QLineEdit:focus { border-color: #1e66f5; }
QComboBox { background-color: #ffffff; border: 1px solid #ccd0da; border-radius: 6px; padding: 5px 10px; color: #4c4f69; }
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView { background-color: #ffffff; color: #4c4f69; selection-background-color: #ccd0da; }
QSpinBox, QDoubleSpinBox { background-color: #ffffff; border: 1px solid #ccd0da; border-radius: 6px; padding: 5px; color: #4c4f69; }
QPushButton { background-color: #1e66f5; color: #ffffff; border: none; border-radius: 6px; padding: 8px 18px; font-weight: bold; }
QPushButton:hover { background-color: #2a6ef5; }
QPushButton:pressed { background-color: #ccd0da; }
QPushButton:disabled { background-color: #ccd0da; color: #9ca0b0; }
QPushButton#danger { background-color: #d20f39; color: white; }
QPushButton#danger:hover { background-color: #e32e57; }
QPushButton#success { background-color: #40a02b; color: white; }
QPushButton#success:hover { background-color: #50b03b; }
QPushButton#secondary { background-color: #ccd0da; color: #4c4f69; }
QPushButton#secondary:hover { background-color: #bcc0cc; }
QTabWidget::pane { border: 1px solid #ccd0da; border-radius: 8px; background-color: #eff1f5; }
QTabBar::tab { background-color: #e6e9ef; color: #6c6f85; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:selected { background-color: #eff1f5; color: #1e66f5; border-bottom: 2px solid #1e66f5; }
QTabBar::tab:hover { color: #4c4f69; }
QMenuBar { background-color: #dce0e8; color: #4c4f69; }
QMenuBar::item:selected { background-color: #ccd0da; }
QMenu { background-color: #ffffff; color: #4c4f69; border: 1px solid #ccd0da; border-radius: 6px; }
QMenu::item:selected { background-color: #ccd0da; }
QStatusBar { background-color: #dce0e8; color: #6c6f85; }
QToolBar { background-color: #dce0e8; border-bottom: 1px solid #ccd0da; spacing: 6px; padding: 4px; }
QScrollBar:vertical { background-color: #eff1f5; width: 10px; border-radius: 5px; }
QScrollBar::handle:vertical { background-color: #ccd0da; border-radius: 5px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QListWidget { background-color: #ffffff; border: 1px solid #ccd0da; border-radius: 6px; }
QListWidget::item { padding: 6px; }
QListWidget::item:selected { background-color: #ccd0da; color: #1e66f5; }
QProgressBar { background-color: #e6e9ef; border: 1px solid #ccd0da; border-radius: 6px; text-align: center; color: #4c4f69; height: 20px; }
QProgressBar::chunk { background-color: #1e66f5; border-radius: 5px; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 2px solid #ccd0da; background-color: #ffffff; }
QCheckBox::indicator:checked { background-color: #1e66f5; border-color: #1e66f5; }
QRadioButton::indicator { width: 18px; height: 18px; border-radius: 9px; border: 2px solid #ccd0da; background-color: #ffffff; }
QRadioButton::indicator:checked { background-color: #1e66f5; border-color: #1e66f5; }
QSplitter::handle { background-color: #ccd0da; }
QLabel#header { font-size: 22px; font-weight: bold; color: #1e66f5; }
QLabel#subheader { font-size: 14px; color: #6c6f85; }
QLabel#stat { font-size: 16px; font-weight: bold; color: #df8e1d; }
"""