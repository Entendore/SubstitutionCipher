"""Core Substitution Cipher logic."""
import random
from typing import List, Optional, Union, Dict
from models import CipherKey

class SubstitutionCipherConfig:
    def __init__(
        self, alphabet: str,
        substitutions: Optional[List[Union[str, Dict[str, str]]]] = None,
        num_layers: Optional[int] = None, random_choice: bool = False,
        ignore_case: bool = False, force_case: Optional[str] = None,
        random_seed: Optional[int] = None, mode: str = "simple",
        caesar_shift: Optional[int] = None, keyword: Optional[str] = None,
        remove_spaces: bool = False, homophonic_pool_size: Optional[int] = None,
    ):
        self.alphabet = alphabet
        self.random_choice = random_choice
        self.ignore_case = ignore_case
        self.force_case = force_case
        self.random_seed = random_seed
        self.mode = mode
        self.caesar_shift = caesar_shift
        self.keyword = keyword
        self.remove_spaces = remove_spaces
        self.homophonic_pool_size = homophonic_pool_size or len(alphabet) * 2

        if substitutions is None:
            substitutions = self._gen_for_mode()
        elif not substitutions:
            raise ValueError("At least one substitution required")

        self.substitutions: List[Dict[str, str]] = []
        for sub in substitutions:
            if isinstance(sub, str):
                if len(sub) != len(alphabet):
                    raise ValueError("Substitution length mismatch")
                self.substitutions.append({a: b for a, b in zip(alphabet, sub)})
            elif isinstance(sub, dict):
                self.substitutions.append({a: sub.get(a, a) for a in alphabet})
            else:
                raise TypeError

        self.num_layers = num_layers if num_layers else len(self.substitutions)
        if self.num_layers <= 0:
            raise ValueError("num_layers must be positive")

    def _gen_for_mode(self) -> List[str]:
        rng = random.Random(self.random_seed)
        a = self.alphabet
        if self.mode in ("simple", "homophonic"):
            return [self._rand_sub(a, self.random_seed)]
        elif self.mode == "caesar":
            s = self.caesar_shift if self.caesar_shift is not None else rng.randint(1, len(a) - 1)
            self.caesar_shift = s
            return [a[s:] + a[:s]]
        elif self.mode == "atbash":
            return [a[::-1]]
        elif self.mode == "keyword":
            if not self.keyword: raise ValueError("Keyword required")
            seen, kp = set(), ""
            for ch in self.keyword.upper():
                if ch in a and ch not in seen: kp += ch; seen.add(ch)
            return [kp + ''.join(c for c in a if c not in seen)]
        return [self._rand_sub(a, self.random_seed)]

    @staticmethod
    def _rand_sub(alphabet: str, seed=None) -> str:
        rng = random.Random(seed)
        chars = list(alphabet); rng.shuffle(chars)
        return ''.join(chars)

    def to_key(self) -> CipherKey:
        layers = [{"encrypt": s, "decrypt": {v: k for k, v in s.items()},
                    "shift": self.caesar_shift, "keyword": self.keyword} for s in self.substitutions]
        return CipherKey(
            version="2.0", alphabet=self.alphabet, mode=self.mode,
            num_layers=self.num_layers, layers=layers, random_seed=self.random_seed,
            options={"random_choice": self.random_choice, "ignore_case": self.ignore_case,
                     "force_case": self.force_case, "remove_spaces": self.remove_spaces}
        )


class SubstitutionCipher:
    def __init__(self, config: SubstitutionCipherConfig, verbose: bool = False):
        self.config = config
        self.verbose = verbose
        rng = random.Random(config.random_seed)
        if config.random_choice:
            self.chosen = [rng.choice(config.substitutions) for _ in range(config.num_layers)]
        else:
            self.chosen = [config.substitutions[i % len(config.substitutions)] for i in range(config.num_layers)]

        self.enc_layers, self.dec_layers = [], []
        for sm in self.chosen:
            em, dm = dict(sm), {v: k for k, v in sm.items()}
            if config.ignore_case and config.alphabet.isalpha():
                if config.alphabet.isupper():
                    em.update({k.lower(): v.lower() for k, v in em.items() if k.isupper()})
                    dm.update({k.lower(): v.lower() for k, v in dm.items() if k.isupper()})
                elif config.alphabet.islower():
                    em.update({k.upper(): v.upper() for k, v in em.items() if k.islower()})
                    dm.update({k.upper(): v.upper() for k, v in dm.items() if k.islower()})
            self.enc_layers.append(em)
            self.dec_layers.append(dm)

    def _preprocess(self, text):
        if self.config.remove_spaces: text = text.replace(" ", "")
        if self.config.ignore_case and self.config.alphabet.isalpha():
            text = text.upper() if self.config.alphabet.isupper() else text.lower()
        return text

    def _case(self, text):
        if self.config.force_case == 'upper': return text.upper()
        if self.config.force_case == 'lower': return text.lower()
        return text

    def encrypt(self, plaintext: str) -> str:
        text = self._preprocess(plaintext)
        for layer in self.enc_layers:
            text = ''.join(layer.get(ch, ch) for ch in text)
        return self._case(text)

    def decrypt(self, ciphertext: str) -> str:
        text = self._preprocess(ciphertext)
        for layer in reversed(self.dec_layers):
            text = ''.join(layer.get(ch, ch) for ch in text)
        return self._case(text)

    def get_key(self) -> CipherKey:
        return self.config.to_key()