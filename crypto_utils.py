"""Cryptanalysis, File I/O, and Key Management utilities."""
import os
import math
import json
from pathlib import Path
from collections import Counter
from glob import glob
from typing import Dict, List, Optional, Tuple

from constants import LANGUAGE_FREQUENCIES
from models import CipherKey, AnalysisResult
from core_ciphers import SubstitutionCipher, SubstitutionCipherConfig

class FrequencyAnalyzer:
    def __init__(self, language="english"):
        self.language = language
        self.ref = LANGUAGE_FREQUENCIES.get(language, LANGUAGE_FREQUENCIES["english"])

    def analyze(self, text: str, ignore_case=True, only_alpha=True) -> AnalysisResult:
        if ignore_case: text = text.upper()
        if only_alpha: text = ''.join(c for c in text if c.isalpha())
        n = len(text)
        if n == 0: return AnalysisResult()
        cc = Counter(text)
        cf = {c: (cnt/n)*100 for c, cnt in cc.most_common()}
        bigs = dict(Counter(text[i:i+2] for i in range(n-1)).most_common(20))
        tris = dict(Counter(text[i:i+3] for i in range(n-2)).most_common(15))
        ic = sum(c*(c-1) for c in cc.values()) / (n*(n-1)) if n > 1 else 0
        ent = -sum((f/100)*math.log2(f/100) for f in cf.values() if f > 0)
        best_lang, best_score = None, 0
        for lang, rf in LANGUAGE_FREQUENCIES.items():
            sc = sum(max(0, 100 - abs(cf.get(c,0)-p)*5) for c,p in rf.items()) / max(len(rf),1)
            if sc > best_score: best_score, best_lang = sc, lang
        return AnalysisResult(n, len(cc), cf, bigs, tris, ic, ent, best_lang, min(1, best_score/80))

    def suggest_map(self, cf: Dict[str, float]) -> Dict[str, str]:
        so = sorted(cf, key=cf.get, reverse=True)
        sr = sorted(self.ref, key=self.ref.get, reverse=True)
        return {o: r for o, r in zip(so, sr)}

class CipherCracker:
    def __init__(self, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        self.alphabet = alphabet
        self.analyzer = FrequencyAnalyzer()

    def crack_caesar(self, text: str, language="english") -> List[Tuple[int, str, float]]:
        ref = LANGUAGE_FREQUENCIES.get(language, LANGUAGE_FREQUENCIES["english"])
        text = ''.join(c.upper() for c in text if c.upper() in self.alphabet)
        results = []
        for shift in range(len(self.alphabet)):
            dec = ''.join(self.alphabet[(self.alphabet.find(c)-shift) % len(self.alphabet)] if c in self.alphabet else c for c in text)
            a = self.analyzer.analyze(dec)
            obs_mean = sum(a.char_frequency.values())/max(len(a.char_frequency),1)
            ref_mean = sum(ref.values())/max(len(ref),1)
            common = set(a.char_frequency) & set(ref)
            num = sum((a.char_frequency.get(c,0)-obs_mean)*(ref.get(c,0)-ref_mean) for c in common)
            ostd = math.sqrt(sum((a.char_frequency.get(c,0)-obs_mean)**2 for c in common))
            rstd = math.sqrt(sum((ref.get(c,0)-ref_mean)**2 for c in common))
            sc = num/(ostd*rstd) if ostd and rstd else 0
            results.append((shift, dec[:200], sc))
        return sorted(results, key=lambda x: x[2], reverse=True)

class KeyManager:
    @staticmethod
    def export_key(cipher: SubstitutionCipher, filepath: str) -> None:
        with open(filepath, 'w', encoding='utf-8') as f: f.write(cipher.get_key().to_json())

    @staticmethod
    def import_key(filepath: str) -> SubstitutionCipherConfig:
        with open(filepath, 'r', encoding='utf-8') as f: key = CipherKey.from_json(f.read())
        subs = [layer["encrypt"] for layer in key.layers]
        return SubstitutionCipherConfig(
            alphabet=key.alphabet, substitutions=subs, num_layers=key.num_layers,
            mode=key.mode, random_seed=key.random_seed,
            random_choice=key.options.get("random_choice", False),
            ignore_case=key.options.get("ignore_case", False),
            force_case=key.options.get("force_case"),
        )

def process_file(cipher: SubstitutionCipher, input_path: str, output_path: str, operation: str = "encrypt", encoding: str = "utf-8"):
    if not os.path.exists(input_path): raise FileNotFoundError(f"File '{input_path}' not found.")
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    func = cipher.encrypt if operation == "encrypt" else cipher.decrypt
    with open(input_path, "r", encoding=encoding) as infile, \
         open(output_path, "w", encoding=encoding) as outfile:
        for line in infile: outfile.write(func(line.rstrip('\n')) + '\n')

def batch_process(cipher: SubstitutionCipher, input_dir: str, output_dir: str, operation: str = "encrypt", encoding: str = "utf-8", pattern: str = "*.txt"):
    out_path = Path(output_dir); out_path.mkdir(parents=True, exist_ok=True)
    files = list(Path(input_dir).glob(pattern))
    if not files: raise ValueError(f"No files matching '{pattern}'")
    for fp in files:
        process_file(cipher, str(fp), str(out_path / fp.name), operation, encoding)
    return len(files)