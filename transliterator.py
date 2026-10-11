"""Language-to-Language Transliteration Engine."""
from typing import Dict, List, Optional, Union
from constants import TRANSLITERATION_MAPS, REVERSE_TRANSLITERATION_MAPS
from core_ciphers import SubstitutionCipher

class Transliterator:
    def __init__(self, map_name: str, custom_map: Optional[Dict[str, str]] = None):
        self.map_name = map_name
        if custom_map:
            self.fwd = custom_map
            self.rev = {v: k for k, v in custom_map.items() if v}
        elif map_name in TRANSLITERATION_MAPS:
            self.fwd = TRANSLITERATION_MAPS[map_name]
            rn = map_name.replace("to_latin", "from_latin")
            self.rev = REVERSE_TRANSLITERATION_MAPS.get(rn, {})
        else:
            raise ValueError(f"Unknown map: {map_name}")

    def transliterate(self, text: str, reverse: bool = False) -> str:
        m = self.rev if reverse else self.fwd
        keys = sorted(m.keys(), key=len, reverse=True)
        result, i = [], 0
        while i < len(text):
            matched = False
            for k in keys:
                if text[i:i+len(k)] == k:
                    result.append(m[k]); i += len(k); matched = True; break
            if not matched: result.append(text[i]); i += 1
        return ''.join(result)

    def forward(self, t): return self.transliterate(t, False)
    def reverse(self, t): return self.transliterate(t, True)

    @staticmethod
    def list_maps(): return list(TRANSLITERATION_MAPS.keys())

class MultiStepTransliterator:
    def __init__(self, steps: List[Union[str, Transliterator]]):
        self.transliterators = [Transliterator(s) if isinstance(s, str) else s for s in steps]
    def transliterate(self, text: str) -> str:
        for t in self.transliterators: text = t.forward(text)
        return text
    def reverse(self, text: str) -> str:
        for t in reversed(self.transliterators): text = t.reverse(text)
        return text

class CipherTransliterator:
    def __init__(self, cipher: SubstitutionCipher, transliterator: Transliterator, cipher_first: bool = True):
        self.cipher, self.transliterator, self.cipher_first = cipher, transliterator, cipher_first
    
    def process(self, text: str, encrypt: bool = True) -> str:
        c_func = self.cipher.encrypt if encrypt else self.cipher.decrypt
        t_func = self.transliterator.forward if encrypt else self.transliterator.reverse
        if self.cipher_first: return t_func(c_func(text))
        return c_func(t_func(text))