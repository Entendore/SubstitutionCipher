"""PySide6 Widgets, Tabs, and Custom Charts."""
import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout, QGroupBox, QLabel, 
    QLineEdit, QTextEdit, QPushButton, QComboBox, QSpinBox, QCheckBox, 
    QRadioButton, QFileDialog, QMessageBox, QSplitter, QProgressBar, 
    QListWidget, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread
from PySide6.QtGui import QFont, QColor, QPainter, QBrush, QPalette

try:
    import matplotlib
    matplotlib.use('QtAgg')
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from constants import LANGUAGE_FREQUENCIES
from models import AnalysisResult
from core_ciphers import SubstitutionCipher, SubstitutionCipherConfig
from transliterator import Transliterator
from crypto_utils import FrequencyAnalyzer, CipherCracker, KeyManager, process_file, batch_process

class WorkerThread(QThread):
    finished_ok = Signal(str)
    finished_err = Signal(str)
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn, self.args, self.kwargs = fn, args, kwargs
    def run(self):
        try:
            self.finished_ok.emit(self.fn(*self.args, **self.kwargs))
        except Exception as e:
            self.finished_err.emit(str(e))

class FrequencyBarChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data, self.ref_data = {}, {}
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    def set_data(self, observed, reference=None):
        self.data, self.ref_data = observed, reference or {}
        self.update()
    def paintEvent(self, event):
        if not self.data: return
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        ml, mr, mt, mb = 50, 20, 20, 40
        cw, ch = w - ml - mr, h - mt - mb
        items = sorted(self.data.items(), key=lambda x: x[1], reverse=True)
        if not items: return
        n = len(items); max_val = max(max(v for _, v in items), 1)
        gap = cw / n; bar_w = max(2, gap - 2)
        if self.ref_data:
            for i, (char, _) in enumerate(items):
                bh = (self.ref_data.get(char, 0) / max_val) * ch
                x, y = ml + i * gap, mt + ch - bh
                p.setBrush(QBrush(QColor(100, 100, 140, 60))); p.setPen(Qt.NoPen)
                p.drawRoundedRect(int(x), int(y), int(bar_w), int(bh), 2, 2)
        for i, (char, val) in enumerate(items):
            bh = (val / max_val) * ch; x, y = ml + i * gap, mt + ch - bh
            color = QColor("#a6e3a1") if self.ref_data else QColor("#89b4fa")
            p.setBrush(QBrush(color)); p.setPen(Qt.NoPen)
            p.drawRoundedRect(int(x), int(y), int(bar_w), int(bh), 2, 2)
            p.setPen(QColor("#cdd6f4")); p.setFont(QFont("Segoe UI", max(6, min(9, int(bar_w)))))
            p.drawText(int(x), int(mt + ch + 14), int(bar_w), 16, Qt.AlignCenter, char)
        p.setPen(QColor("#a6adc8")); p.setFont(QFont("Segoe UI", 8))
        for i in range(5):
            val = (max_val * i) / 4; y = mt + ch - (val / max_val) * ch
            p.drawText(0, int(y) - 6, ml - 6, 14, Qt.AlignRight | Qt.AlignVCenter, f"{val:.1f}%")
            p.setPen(QPen(QColor("#45475a"), 1, Qt.DotLine))
            p.drawLine(ml, int(y), w - mr, int(y)); p.setPen(QColor("#a6adc8"))
        p.end()

class MatplotlibChart(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(8, 3), dpi=100); self.fig.patch.set_facecolor('#1e1e2e')
        super().__init__(self.fig); self.ax = self.fig.add_subplot(111); self.setMinimumHeight(200)
    def set_data(self, observed, reference=None):
        self.ax.clear()
        items = sorted(observed.items(), key=lambda x: x[1], reverse=True)
        if not items: self.draw(); return
        chars, vals = zip(*items); x = range(len(chars))
        if reference:
            ref_vals = [reference.get(c, 0) for c in chars]
            self.ax.bar(x, ref_vals, color='#585b70', alpha=0.6, label='Reference', width=0.8)
            self.ax.bar(x, vals, color='#a6e3a1', alpha=0.9, label='Observed', width=0.6)
        else:
            self.ax.bar(x, vals, color='#89b4fa', alpha=0.9, width=0.8)
        self.ax.set_xticks(x); self.ax.set_xticklabels(chars, fontsize=8)
        self.ax.set_ylabel('Frequency %', color='#cdd6f4', fontsize=9)
        self.ax.set_facecolor('#313244'); self.ax.tick_params(colors='#a6adc8')
        for spine in self.ax.spines.values(): spine.set_color('#45475a')
        if reference: self.ax.legend(fontsize=8, facecolor='#313244', edgecolor='#45475a', labelcolor='#cdd6f4')
        self.fig.tight_layout(); self.draw()

class ConfigPanel(QGroupBox):
    config_changed = Signal()
    def __init__(self, parent=None):
        super().__init__("Cipher Configuration", parent)
        layout = QFormLayout(self); layout.setSpacing(8)
        self.mode_combo = QComboBox(); self.mode_combo.addItems(["simple", "caesar", "atbash", "keyword", "homophonic"])
        self.mode_combo.currentTextChanged.connect(self._on_mode_change); layout.addRow("Mode:", self.mode_combo)
        self.alphabet_edit = QLineEdit("ABCDEFGHIJKLMNOPQRSTUVWXYZ"); layout.addRow("Alphabet:", self.alphabet_edit)
        self.layers_spin = QSpinBox(); self.layers_spin.setRange(1, 100); self.layers_spin.setValue(1); layout.addRow("Layers:", self.layers_spin)
        self.seed_spin = QSpinBox(); self.seed_spin.setRange(-1, 999999); self.seed_spin.setValue(-1); self.seed_spin.setSpecialValueText("Random"); layout.addRow("Seed:", self.seed_spin)
        self.shift_spin = QSpinBox(); self.shift_spin.setRange(1, 100); self.shift_spin.setValue(3); layout.addRow("Caesar Shift:", self.shift_spin)
        self.keyword_edit = QLineEdit(); layout.addRow("Keyword:", self.keyword_edit)
        self.random_choice_cb = QCheckBox("Random layer selection"); layout.addRow(self.random_choice_cb)
        self.ignore_case_cb = QCheckBox("Ignore case"); self.ignore_case_cb.setChecked(True); layout.addRow(self.ignore_case_cb)
        self.remove_spaces_cb = QCheckBox("Remove spaces"); layout.addRow(self.remove_spaces_cb)
        self.force_case_combo = QComboBox(); self.force_case_combo.addItems(["None", "upper", "lower"]); layout.addRow("Force case:", self.force_case_combo)
        self._on_mode_change("simple")
        for w in [self.alphabet_edit, self.layers_spin, self.seed_spin, self.shift_spin, self.keyword_edit, 
                  self.random_choice_cb, self.ignore_case_cb, self.remove_spaces_cb, self.force_case_combo]:
            attr = ('textChanged' if isinstance(w, QLineEdit) else 'valueChanged' if isinstance(w, QSpinBox) 
                    else 'stateChanged' if isinstance(w, QCheckBox) else 'currentTextChanged')
            if hasattr(w, attr): getattr(w, attr).connect(self.config_changed)

    def _on_mode_change(self, mode):
        self.shift_spin.setEnabled(mode == "caesar")
        self.keyword_edit.setEnabled(mode == "keyword")
        self.keyword_edit.setStyleSheet("" if mode == "keyword" else "background-color: #252536; color: #6c7086;")
        self.shift_spin.setStyleSheet("" if mode == "caesar" else "background-color: #252536; color: #6c7086;")

    def get_config(self) -> SubstitutionCipherConfig:
        seed = None if self.seed_spin.value() == -1 else self.seed_spin.value()
        fc = self.force_case_combo.currentText(); fc = None if fc == "None" else fc
        return SubstitutionCipherConfig(
            alphabet=self.alphabet_edit.text(), mode=self.mode_combo.currentText(),
            num_layers=self.layers_spin.value(), random_seed=seed,
            caesar_shift=self.shift_spin.value() if self.mode_combo.currentText() == "caesar" else None,
            keyword=self.keyword_edit.text() if self.mode_combo.currentText() == "keyword" else None,
            random_choice=self.random_choice_cb.isChecked(), ignore_case=self.ignore_case_cb.isChecked(),
            force_case=fc, remove_spaces=self.remove_spaces_cb.isChecked(),
        )
    def build_cipher(self, verbose=False) -> SubstitutionCipher:
        return SubstitutionCipher(self.get_config(), verbose=verbose)

class CipherTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        left = QVBoxLayout(); self.config = ConfigPanel(); left.addWidget(self.config)
        btn_row = QHBoxLayout()
        self.btn_encrypt = QPushButton("↓ Encrypt"); self.btn_encrypt.setObjectName("success")
        self.btn_decrypt = QPushButton("↑ Decrypt"); self.btn_decrypt.setObjectName("danger")
        self.btn_swap = QPushButton("⇄ Swap"); self.btn_swap.setObjectName("secondary")
        self.btn_copy = QPushButton("📋 Copy"); self.btn_copy.setObjectName("secondary")
        for b in [self.btn_encrypt, self.btn_decrypt, self.btn_swap, self.btn_copy]: btn_row.addWidget(b)
        left.addLayout(btn_row); left.addStretch()
        left_widget = QWidget(); left_widget.setLayout(left); left_widget.setFixedWidth(320)
        
        right = QVBoxLayout()
        self.input_edit = QTextEdit(); self.input_edit.setPlaceholderText("Enter plaintext here..."); self.input_edit.setFont(QFont("Consolas", 12))
        self.output_edit = QTextEdit(); self.output_edit.setPlaceholderText("Result appears here..."); self.output_edit.setReadOnly(True); self.output_edit.setFont(QFont("Consolas", 12))
        splitter = QSplitter(Qt.Vertical); splitter.addWidget(self.input_edit); splitter.addWidget(self.output_edit)
        splitter.setStretchFactor(0, 1); splitter.setStretchFactor(1, 1); right.addWidget(splitter)
        
        layout.addWidget(left_widget); layout.addLayout(right, 1)
        self.btn_encrypt.clicked.connect(self._encrypt); self.btn_decrypt.clicked.connect(self._decrypt)
        self.btn_swap.clicked.connect(self._swap); self.btn_copy.clicked.connect(self._copy)
        self.input_edit.textChanged.connect(self._auto_encrypt)
        self._debounce = QTimer(); self._debounce.setSingleShot(True); self._debounce.setInterval(300); self._debounce.timeout.connect(self._do_auto)

    def _auto_encrypt(self): self._debounce.start()
    def _do_auto(self):
        try:
            if self.input_edit.toPlainText(): self.output_edit.setPlainText(self.config.build_cipher().encrypt(self.input_edit.toPlainText()))
            else: self.output_edit.clear()
        except: pass
    def _encrypt(self):
        try: self.output_edit.setPlainText(self.config.build_cipher().encrypt(self.input_edit.toPlainText()))
        except Exception as e: self.output_edit.setPlainText(f"Error: {e}")
    def _decrypt(self):
        try: self.output_edit.setPlainText(self.config.build_cipher().decrypt(self.input_edit.toPlainText()))
        except Exception as e: self.output_edit.setPlainText(f"Error: {e}")
    def _swap(self):
        tmp = self.input_edit.toPlainText(); self.input_edit.setPlainText(self.output_edit.toPlainText()); self.output_edit.setPlainText(tmp)
    def _copy(self): QApplication.clipboard().setText(self.output_edit.toPlainText())

class FileTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.config = ConfigPanel(); self.config.setFixedHeight(300); layout.addWidget(self.config)
        io = QHBoxLayout()
        self.input_path = QLineEdit(); self.input_path.setPlaceholderText("Input file path...")
        b1 = QPushButton("Browse..."); b1.setObjectName("secondary"); b1.clicked.connect(lambda: self._browse(self.input_path, False))
        io.addWidget(QLabel("Input:")); io.addWidget(self.input_path, 1); io.addWidget(b1)
        self.output_path = QLineEdit(); self.output_path.setPlaceholderText("Output file path...")
        b2 = QPushButton("Browse..."); b2.setObjectName("secondary"); b2.clicked.connect(lambda: self._browse(self.output_path, True))
        io.addWidget(QLabel("Output:")); io.addWidget(self.output_path, 1); io.addWidget(b2)
        layout.addLayout(io)
        row = QHBoxLayout(); self.batch_cb = QCheckBox("Batch mode"); self.pattern_edit = QLineEdit("*.txt"); self.pattern_edit.setEnabled(False)
        self.batch_cb.stateChanged.connect(lambda s: self.pattern_edit.setEnabled(s == Qt.Checked))
        row.addWidget(self.batch_cb); row.addWidget(QLabel("Pattern:")); row.addWidget(self.pattern_edit); layout.addLayout(row)
        btn_row = QHBoxLayout()
        self.btn_enc = QPushButton("🔒 Encrypt File(s)"); self.btn_enc.setObjectName("success")
        self.btn_dec = QPushButton("🔓 Decrypt File(s)"); self.btn_dec.setObjectName("danger")
        btn_row.addWidget(self.btn_enc); btn_row.addWidget(self.btn_dec); btn_row.addStretch(); layout.addLayout(btn_row)
        self.progress = QProgressBar(); self.progress.setVisible(False); layout.addWidget(self.progress)
        self.log = QTextEdit(); self.log.setReadOnly(True); self.log.setMaximumHeight(150); layout.addWidget(self.log)
        self.btn_enc.clicked.connect(lambda: self._process("encrypt")); self.btn_dec.clicked.connect(lambda: self._process("decrypt"))

    def _browse(self, line_edit, save):
        if self.batch_cb.isChecked():
            d = QFileDialog.getExistingDirectory(self, "Select Directory"); 
            if d: line_edit.setText(d)
        else:
            f, _ = QFileDialog.getSaveFileName(self, "Select File") if save else QFileDialog.getOpenFileName(self, "Select File")
            if f: line_edit.setText(f)

    def _process(self, op):
        inp, out = self.input_path.text(), self.output_path.text()
        if not inp or not out: return QMessageBox.warning(self, "Error", "Specify paths.")
        try:
            cipher = self.config.build_cipher()
            if self.batch_cb.isChecked():
                out_path = Path(out); out_path.mkdir(parents=True, exist_ok=True)
                files = list(Path(inp).glob(self.pattern_edit.text()))
                if not files: return QMessageBox.warning(self, "Error", "No files found.")
                self.progress.setVisible(True); self.progress.setRange(0, len(files))
                for i, fp in enumerate(files):
                    try: process_file(cipher, str(fp), str(out_path / fp.name), op)
                    except Exception as e: self.log.append(f"[ERR] {fp.name}: {e}")
                    self.progress.setValue(i + 1)
                self.progress.setVisible(False); QMessageBox.information(self, "Done", f"Processed {len(files)} files.")
            else:
                process_file(cipher, inp, out, op)
                self.log.append(f"[OK] {op} → {out}"); QMessageBox.information(self, "Done", f"Saved to {out}")
        except Exception as e:
            self.log.append(f"[ERR] {e}"); QMessageBox.critical(self, "Error", str(e))

from pathlib import Path # Added here for FileTab brevity

class TransliterationTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        left = QVBoxLayout(); grp = QGroupBox("Transliteration Settings"); form = QFormLayout(grp)
        self.map_combo = QComboBox(); self.map_combo.addItems(Transliterator.list_maps()); form.addRow("Map:", self.map_combo)
        self.reverse_cb = QCheckBox("Reverse direction"); form.addRow(self.reverse_cb)
        self.combine_cb = QCheckBox("Also apply cipher"); form.addRow(self.combine_cb)
        self.cipher_first_rb = QRadioButton("Cipher → Trans"); self.trans_first_rb = QRadioButton("Trans → Cipher")
        self.cipher_first_rb.setChecked(True)
        ord_grp = QGroupBox("Order"); ol = QVBoxLayout(ord_grp); ol.addWidget(self.cipher_first_rb); ol.addWidget(self.trans_first_rb)
        ord_grp.setEnabled(False); self.combine_cb.stateChanged.connect(lambda s: ord_grp.setEnabled(s == Qt.Checked))
        form.addRow(ord_grp)
        self.config = ConfigPanel(); self.config.setTitle("Cipher Config"); self.config.setVisible(False)
        self.combine_cb.stateChanged.connect(lambda s: self.config.setVisible(s == Qt.Checked))
        left.addWidget(grp); left.addWidget(self.config); left.addStretch()
        left_w = QWidget(); left_w.setLayout(left); left_w.setFixedWidth(320)
        
        right = QVBoxLayout()
        self.input_edit = QTextEdit(); self.input_edit.setPlaceholderText("Text to transliterate..."); self.input_edit.setFont(QFont("Consolas", 12))
        self.output_edit = QTextEdit(); self.output_edit.setReadOnly(True); self.output_edit.setFont(QFont("Consolas", 12))
        btn_row = QHBoxLayout()
        self.btn_trans = QPushButton("→ Transliterate"); self.btn_copy = QPushButton("📋 Copy"); self.btn_copy.setObjectName("secondary")
        self.btn_swap = QPushButton("⇄ Swap"); self.btn_swap.setObjectName("secondary")
        for b in [self.btn_trans, self.btn_swap, self.btn_copy]: btn_row.addWidget(b)
        splitter = QSplitter(Qt.Vertical); splitter.addWidget(self.input_edit); splitter.addWidget(self.output_edit)
        right.addWidget(splitter); right.addLayout(btn_row)
        layout.addWidget(left_w); layout.addLayout(right, 1)
        self.btn_trans.clicked.connect(self._trans)
        self.btn_copy.clicked.connect(lambda: QApplication.clipboard().setText(self.output_edit.toPlainText()))
        self.btn_swap.clicked.connect(lambda: (self.input_edit.setPlainText(self.output_edit.toPlainText()), self.output_edit.clear()))

    def _trans(self):
        try:
            text = self.input_edit.toPlainText()
            if not text: return
            res = Transliterator(self.map_combo.currentText()).transliterate(text, self.reverse_cb.isChecked())
            if self.combine_cb.isChecked():
                c = self.config.build_cipher()
                if self.cipher_first_rb.isChecked(): res = c.encrypt(res)
                else: res = c.encrypt(text); res = Transliterator(self.map_combo.currentText()).transliterate(res, self.reverse_cb.isChecked())
            self.output_edit.setPlainText(res)
        except Exception as e: self.output_edit.setPlainText(f"Error: {e}")

class AnalysisTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.lang_combo = QComboBox(); self.lang_combo.addItems(list(LANGUAGE_FREQUENCIES.keys()))
        top.addWidget(QLabel("Ref Lang:")); top.addWidget(self.lang_combo)
        self.input_edit = QTextEdit(); self.input_edit.setMaximumHeight(120); self.input_edit.setPlaceholderText("Paste text...")
        top.addWidget(self.input_edit, 1); layout.addLayout(top)
        
        btn_row = QHBoxLayout()
        self.btn_analyze = QPushButton("📊 Analyze"); self.btn_suggest = QPushButton("💡 Suggest Map"); self.btn_suggest.setObjectName("secondary")
        self.btn_open = QPushButton("📁 Open"); self.btn_open.setObjectName("secondary")
        for b in [self.btn_analyze, self.btn_suggest, self.btn_open]: btn_row.addWidget(b)
        btn_row.addStretch(); layout.addLayout(btn_row)
        
        stats = QGroupBox("Statistics"); sg = QGridLayout(stats)
        self.lbl_len, self.lbl_uni, self.lbl_ic, self.lbl_ent, self.lbl_lang, self.lbl_conf = (QLabel("0") for _ in range(6))
        for i, (n, l) in enumerate([("Length:", self.lbl_len), ("Unique:", self.lbl_uni), ("IC:", self.lbl_ic), ("Entropy:", self.lbl_ent), ("Lang:", self.lbl_lang), ("Conf:", self.lbl_conf)]):
            sg.addWidget(QLabel(n), i, 0); sg.addWidget(l, i, 1); l.setObjectName("stat")
        layout.addWidget(stats)
        
        chart_grp = QGroupBox("Frequency Chart"); cl = QVBoxLayout(chart_grp)
        self.chart = MatplotlibChart() if HAS_MATPLOTLIB else FrequencyBarChart(); cl.addWidget(self.chart)
        layout.addWidget(chart_grp, 1)
        
        ngrams = QGroupBox("N-grams"); nl = QHBoxLayout(ngrams)
        self.bigrams_list, self.trigrams_list = QListWidget(), QListWidget()
        nl.addWidget(QLabel("Bigrams:")); nl.addWidget(self.bigrams_list, 1); nl.addWidget(QLabel("Trigrams:")); nl.addWidget(self.trigrams_list, 1)
        layout.addWidget(ngrams)
        
        self.btn_analyze.clicked.connect(self._analyze); self.btn_suggest.clicked.connect(self._suggest)
        self.btn_open.clicked.connect(lambda: self.input_edit.setPlainText(open(QFileDialog.getOpenFileName(self, "Open")[0], encoding='utf-8').read()) if QFileDialog.getOpenFileName(self, "Open")[0] else None)
        self._res = None

    def _analyze(self):
        text = self.input_edit.toPlainText()
        if not text: return
        self._res = FrequencyAnalyzer(self.lang_combo.currentText()).analyze(text); r = self._res
        self.lbl_len.setText(str(r.text_length)); self.lbl_uni.setText(str(r.unique_chars))
        self.lbl_ic.setText(f"{r.index_of_coincidence:.6f}"); self.lbl_ent.setText(f"{r.entropy:.4f}")
        self.lbl_lang.setText(r.language_guess or "-"); self.lbl_conf.setText(f"{r.confidence*100:.1f}%")
        ref = LANGUAGE_FREQUENCIES.get(self.lang_combo.currentText(), {}); self.chart.set_data(r.char_frequency, ref)
        self.bigrams_list.clear(); self.trigrams_list.clear()
        for bg, c in r.bigram_frequency.items(): self.bigrams_list.addItem(f"{bg}: {c}")
        for tg, c in r.trigram_frequency.items(): self.trigrams_list.addItem(f"{tg}: {c}")

    def _suggest(self):
        if not self._res: self._analyze()
        if self._res:
            s = FrequencyAnalyzer(self.lang_combo.currentText()).suggest_map(self._res.char_frequency)
            QMessageBox.information(self, "Suggestion", "Suggested map:\n\n  " + ", ".join(f"{k}→{v}" for k, v in sorted(s.items())))

class CrackTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); layout = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(QLabel("Alpha:")); self.alpha_edit = QLineEdit("ABCDEFGHIJKLMNOPQRSTUVWXYZ"); top.addWidget(self.alpha_edit)
        top.addWidget(QLabel("Lang:")); self.lang_combo = QComboBox(); self.lang_combo.addItems(list(LANGUAGE_FREQUENCIES.keys())); top.addWidget(self.lang_combo)
        layout.addLayout(top)
        self.input_edit = QTextEdit(); self.input_edit.setMaximumHeight(100); self.input_edit.setPlaceholderText("Ciphertext..."); layout.addWidget(self.input_edit)
        btn_row = QHBoxLayout()
        b1 = QPushButton("📁 Open"); b1.setObjectName("secondary"); b1.clicked.connect(lambda: self.input_edit.setPlainText(open(QFileDialog.getOpenFileName(self, "Open")[0], encoding='utf-8').read()) if QFileDialog.getOpenFileName(self, "Open")[0] else None)
        self.btn_crack = QPushButton("🔓 Crack Caesar"); self.btn_crack.setObjectName("danger")
        btn_row.addWidget(b1); btn_row.addWidget(self.btn_crack); btn_row.addStretch(); layout.addLayout(btn_row)
        self.result_list = QListWidget(); self.result_list.setFont(QFont("Consolas", 11)); layout.addWidget(self.result_list)
        btn_row2 = QHBoxLayout()
        self.btn_use = QPushButton("Use Selected"); self.btn_use.setObjectName("success")
        self.btn_copy = QPushButton("📋 Copy"); self.btn_copy.setObjectName("secondary")
        btn_row2.addWidget(self.btn_use); btn_row2.addWidget(self.btn_copy); layout.addLayout(btn_row2)
        self.btn_crack.clicked.connect(self._crack); self._results = []
        self.btn_use.clicked.connect(lambda: QMessageBox.information(self, "Shift", f"Use shift={self._results[self.result_list.currentRow()][0]}") if self.result_list.currentRow() >= 0 else None)
        self.btn_copy.clicked.connect(lambda: QApplication.clipboard().setText(self._results[self.result_list.currentRow()][1]) if self.result_list.currentRow() >= 0 else None)

    def _crack(self):
        text = self.input_edit.toPlainText()
        if not text: return
        self._results = CipherCracker(self.alpha_edit.text()).crack_caesar(text, self.lang_combo.currentText())
        self.result_list.clear()
        for s, sa, sc in self._results: self.result_list.addItem(f"[Shift {s:2d}] Score: {sc:.4f}  →  {sa}...")

class KeyTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); layout = QVBoxLayout(self)
        self.config = ConfigPanel(); self.config.setFixedHeight(320); layout.addWidget(self.config)
        btn_row = QHBoxLayout()
        self.btn_gen = QPushButton("🔑 Generate"); self.btn_exp = QPushButton("💾 Export"); self.btn_exp.setObjectName("success")
        self.btn_imp = QPushButton("📂 Import"); self.btn_imp.setObjectName("secondary"); self.btn_copy = QPushButton("📋 Copy"); self.btn_copy.setObjectName("secondary")
        for b in [self.btn_gen, self.btn_exp, self.btn_imp, self.btn_copy]: btn_row.addWidget(b)
        layout.addLayout(btn_row)
        self.display = QTextEdit(); self.display.setReadOnly(True); self.display.setFont(QFont("Consolas", 11)); layout.addWidget(self.display)
        self.btn_gen.clicked.connect(self._gen); self.btn_exp.clicked.connect(self._exp); self.btn_imp.clicked.connect(self._imp)
        self.btn_copy.clicked.connect(lambda: QApplication.clipboard().setText(self.display.toPlainText()))
        self._cipher = None

    def _gen(self):
        try: self._cipher = self.config.build_cipher(); self.display.setPlainText(self._cipher.get_key().to_json())
        except Exception as e: self.display.setPlainText(f"Error: {e}")
    def _exp(self):
        if not self._cipher: self._gen()
        if not self._cipher: return
        f, _ = QFileDialog.getSaveFileName(self, "Export", "key.json", "JSON (*.json)")
        if f:
            try: KeyManager.export_key(self._cipher, f); QMessageBox.information(self, "Done", f"Saved to {f}")
            except Exception as e: QMessageBox.critical(self, "Error", str(e))
    def _imp(self):
        f, _ = QFileDialog.getOpenFileName(self, "Import", "", "JSON (*.json)")
        if f:
            try:
                cfg = KeyManager.import_key(f); self._cipher = SubstitutionCipher(cfg)
                self.display.setPlainText(self._cipher.get_key().to_json())
                QMessageBox.information(self, "Done", "Key imported.")
            except Exception as e: QMessageBox.critical(self, "Error", str(e))