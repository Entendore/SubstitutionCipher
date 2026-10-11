#!/usr/bin/env python3
"""Main Entry Point: GUI Window and CLI Interface."""
import sys
import argparse
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QFileDialog, 
    QWidget, QTabWidget, QVBoxLayout
)
from PySide6.QtCore import QSettings, QSize
from PySide6.QtGui import QColor, QPalette

from ui_theme import DARK_STYLE, LIGHT_STYLE
from ui_views import (
    CipherTab, FileTab, TransliterationTab, 
    AnalysisTab, CrackTab, KeyTab
)
from core_ciphers import SubstitutionCipherConfig, SubstitutionCipher
from transliterator import Transliterator
from crypto_utils import process_file, batch_process, KeyManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔐 Substitution Cipher & Transliteration Tool")
        self.setMinimumSize(1100, 750)
        self.resize(1300, 850)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(6, 6, 6, 6)

        self.tabs = self._create_tabs()
        main_layout.addWidget(self.tabs)
        
        self._build_menu()
        self._build_toolbar()
        self.statusBar().showMessage("Ready")

    def _create_tabs(self):
        # Store tabs in a simple namespace object
        class Tabs:
            pass
            
        tabs = Tabs()
        tabs.tab_cipher = CipherTab()
        tabs.tab_file = FileTab()
        tabs.tab_trans = TransliterationTab()
        tabs.tab_analysis = AnalysisTab()
        tabs.tab_crack = CrackTab()
        tabs.tab_key = KeyTab()
        
        w = QTabWidget()
        w.addTab(tabs.tab_cipher, "🔐 Cipher")
        w.addTab(tabs.tab_file, "📁 Files")
        w.addTab(tabs.tab_trans, "🌐 Transliterate")
        w.addTab(tabs.tab_analysis, "📊 Analysis")
        w.addTab(tabs.tab_crack, "🔓 Crack")
        w.addTab(tabs.tab_key, "🔑 Keys")
        
        self._tabs_widget = w
        self._tabs_obj = tabs
        return w

    def _build_menu(self):
        mb = self.menuBar()
        
        file_m = mb.addMenu("&File")
        file_m.addAction("Open into Analysis...", self._menu_open)
        file_m.addSeparator()
        file_m.addAction("Exit", self.close)
        
        view_m = mb.addMenu("&View")
        self.dark_act = view_m.addAction("Dark Theme")
        self.dark_act.setCheckable(True)
        self.dark_act.setChecked(True)
        self.dark_act.triggered.connect(self._toggle_theme)
        
        help_m = mb.addMenu("&Help")
        help_m.addAction("About", lambda: QMessageBox.about(
            self, "About", 
            "<h2>Substitution Cipher Tool</h2><p>Advanced cryptographic and transliteration tool.</p>"
        ))
        help_m.addAction("Maps", lambda: QMessageBox.information(
            self, "Maps", 
            "\n".join(f"• {m}" for m in Transliterator.list_maps())
        ))

    def _build_toolbar(self):
        tb = self.addToolBar("Main")
        tb.setMovable(False)
        tb.addAction("🔑 Keys", lambda: self._tabs_widget.setCurrentIndex(5))
        tb.addSeparator()
        tb.addAction("📋 Copy Output", self._global_copy)

    def _toggle_theme(self, dark):
        QApplication.instance().setStyleSheet(DARK_STYLE if dark else LIGHT_STYLE)

    def _menu_open(self):
        f, _ = QFileDialog.getOpenFileName(self, "Open File")
        if f:
            try:
                with open(f, 'r', encoding='utf-8') as fh:
                    self._tabs_obj.tab_analysis.input_edit.setPlainText(fh.read())
                self._tabs_widget.setCurrentIndex(3)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _global_copy(self):
        idx = self._tabs_widget.currentIndex()
        txt = ""
        if idx == 0: 
            txt = self._tabs_obj.tab_cipher.output_edit.toPlainText()
        elif idx == 2: 
            txt = self._tabs_obj.tab_trans.output_edit.toPlainText()
        
        if txt: 
            QApplication.clipboard().setText(txt)
            self.statusBar().showMessage("Copied to clipboard!", 2000)

    def closeEvent(self, event):
        settings = QSettings("CipherTool", "SubstitutionCipher")
        settings.setValue("dark_theme", self.dark_act.isChecked())
        settings.sync()
        super().closeEvent(event)


def run_gui():
    app = QApplication(sys.argv)
    app.setApplicationName("CipherTool")
    
    app.setStyle("Fusion")
    
    # Set dark palette base
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#1e1e2e"))
    palette.setColor(QPalette.WindowText, QColor("#cdd6f4"))
    palette.setColor(QPalette.Base, QColor("#313244"))
    palette.setColor(QPalette.AlternateBase, QColor("#45475a"))
    palette.setColor(QPalette.Text, QColor("#cdd6f4"))
    palette.setColor(QPalette.Button, QColor("#45475a"))
    palette.setColor(QPalette.ButtonText, QColor("#cdd6f4"))
    palette.setColor(QPalette.Highlight, QColor("#89b4fa"))
    palette.setColor(QPalette.HighlightedText, QColor("#1e1e2e"))
    app.setPalette(palette)
    
    # Apply stylesheet
    settings = QSettings("CipherTool", "SubstitutionCipher")
    is_dark = settings.value("dark_theme", True, type=bool)
    app.setStyleSheet(DARK_STYLE if is_dark else LIGHT_STYLE)
    
    window = MainWindow()
    
    # Sync theme toggle checkbox with loaded setting
    window.dark_act.setChecked(is_dark)
    
    window.show()
    sys.exit(app.exec())


def run_cli():
    parser = argparse.ArgumentParser(description="Substitution Cipher CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-e", "--encrypt", metavar="INPUT")
    group.add_argument("-d", "--decrypt", metavar="INPUT")
    group.add_argument("--transliterate", metavar="INPUT")
    group.add_argument("--interactive", action="store_true")
    
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("-a", "--alphabet", default="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    parser.add_argument("-n", "--num-layers", type=int, default=1)
    parser.add_argument("--mode", default="simple", choices=["simple", "caesar", "atbash", "keyword"])
    parser.add_argument("--shift", type=int)
    parser.add_argument("--keyword", type=str)
    parser.add_argument("-s", "--seed", type=int, default=None)
    parser.add_argument("--ignore-case", action="store_true")
    parser.add_argument("--remove-spaces", action="store_true")
    parser.add_argument("--trans-map", type=str)
    parser.add_argument("--trans-reverse", action="store_true")
    parser.add_argument("--batch", action="store_true")
    parser.add_argument("--pattern", default="*.txt")
    parser.add_argument("--import-key", type=str)
    
    args = parser.parse_args()

    if args.interactive:
        run_gui()
        return

    if args.transliterate:
        if not args.trans_map:
            raise ValueError("--trans-map required")
        trans = Transliterator(args.trans_map)
        with open(args.transliterate, 'r', encoding='utf-8') as inf, \
             open(args.output, 'w', encoding='utf-8') as outf:
            for line in inf:
                outf.write(trans.transliterate(line.rstrip('\n'), args.trans_reverse) + '\n')
        print(f"Transliterated to {args.output}")
        return

    if args.import_key:
        config = KeyManager.import_key(args.import_key)
    else:
        config = SubstitutionCipherConfig(
            alphabet=args.alphabet, mode=args.mode, num_layers=args.num_layers,
            random_seed=args.shift if args.mode == "caesar" else args.seed,
            caesar_shift=args.shift, keyword=args.keyword,
            ignore_case=args.ignore_case, remove_spaces=args.remove_spaces
        )
        
    cipher = SubstitutionCipher(config)
    op = "encrypt" if args.encrypt else "decrypt"
    
    if args.batch:
        count = batch_process(cipher, args.encrypt or args.decrypt, args.output, op, pattern=args.pattern)
        print(f"Batch processed {count} files.")
    else:
        process_file(cipher, args.encrypt or args.decrypt, args.output, op)
        print(f"Output written to {args.output}")


if __name__ == "__main__":
    if "--interactive" in sys.argv or len(sys.argv) == 1:
        run_gui()
    else:
        run_cli()