import random
import argparse
import os
from typing import List, Optional, Union, Dict


class SubstitutionCipherConfig:
    def __init__(
        self,
        alphabet: str,
        substitutions: Optional[List[Union[str, Dict[str, str]]]] = None,
        num_layers: Optional[int] = None,
        random_choice: bool = False,
        ignore_case: bool = False,
        force_case: Optional[str] = None,
        random_seed: Optional[int] = None,
    ):
        self.alphabet = alphabet
        self.random_choice = random_choice
        self.ignore_case = ignore_case
        self.force_case = force_case
        self.random_seed = random_seed

        if substitutions is None:
            substitutions = self.generate_multiple_random_substitutions(alphabet, 1, random_seed)
        elif not substitutions:
            raise ValueError("At least one substitution sequence required")

        self.substitutions: List[Dict[str, str]] = []
        for sub in substitutions:
            if isinstance(sub, str):
                if len(sub) != len(alphabet):
                    raise ValueError("Substitution string must match length of alphabet")
                self.substitutions.append({a: b for a, b in zip(alphabet, sub)})
            elif isinstance(sub, dict):
                self.substitutions.append({a: sub.get(a, a) for a in alphabet})
            else:
                raise TypeError("Substitution must be str or dict")

        if num_layers is None:
            self.num_layers = len(self.substitutions)
        elif num_layers <= 0:
            raise ValueError("num_layers must be positive")
        else:
            self.num_layers = num_layers

    @staticmethod
    def generate_random_substitution(alphabet: str, seed: Optional[int] = None) -> str:
        rng = random.Random(seed)
        chars = list(alphabet)
        rng.shuffle(chars)
        return ''.join(chars)

    @staticmethod
    def generate_multiple_random_substitutions(
        alphabet: str,
        count: int,
        seed: Optional[int] = None
    ) -> List[str]:
        rng = random.Random(seed)
        return [
            ''.join(rng.sample(alphabet, len(alphabet))) for _ in range(count)
        ]


class SubstitutionCipher:
    def __init__(self, config: SubstitutionCipherConfig, verbose: bool = False):
        self.config = config
        self.verbose = verbose

        rng = random.Random(config.random_seed)
        if config.random_choice:
            self.chosen_subs = [rng.choice(config.substitutions) for _ in range(config.num_layers)]
        else:
            self.chosen_subs = [
                config.substitutions[i % len(config.substitutions)]
                for i in range(config.num_layers)
            ]

        if verbose:
            print(f"[Init] Using {config.num_layers} substitution layers:")
            for i, layer in enumerate(self.chosen_subs, 1):
                print(f" Layer {i}: {layer}")

        self.encrypt_layers = []
        self.decrypt_layers = []

        for sub_map in self.chosen_subs:
            encrypt_map = dict(sub_map)
            decrypt_map = {v: k for k, v in sub_map.items()}

            if config.ignore_case and config.alphabet.isalpha():
                if config.alphabet.isupper():
                    encrypt_map.update({k.lower(): v for k, v in encrypt_map.items() if k.isupper()})
                    decrypt_map.update({v.lower(): k for k, v in encrypt_map.items() if k.isupper()})
                elif config.alphabet.islower():
                    encrypt_map.update({k.upper(): v for k, v in encrypt_map.items() if k.islower()})
                    decrypt_map.update({v.upper(): k for k, v in encrypt_map.items() if k.islower()})

            self.encrypt_layers.append(encrypt_map)
            self.decrypt_layers.append(decrypt_map)

    def _apply_case_rules(self, text: str) -> str:
        if self.config.force_case == 'upper':
            return text.upper()
        elif self.config.force_case == 'lower':
            return text.lower()
        return text

    def encrypt(self, plaintext: str) -> str:
        text = plaintext
        if self.config.ignore_case and self.config.alphabet.isalpha():
            text = text.upper() if self.config.alphabet.isupper() else text.lower()

        for i, layer in enumerate(self.encrypt_layers, 1):
            text = ''.join(layer.get(ch, ch) for ch in text)
            if self.verbose:
                print(f"[Encrypt] After layer {i}: {text}")

        return self._apply_case_rules(text)

    def decrypt(self, ciphertext: str) -> str:
        text = ciphertext
        if self.config.ignore_case and self.config.alphabet.isalpha():
            text = text.upper() if self.config.alphabet.isupper() else text.lower()

        for i, layer in enumerate(reversed(self.decrypt_layers), 1):
            text = ''.join(layer.get(ch, ch) for ch in text)
            if self.verbose:
                print(f"[Decrypt] After layer {i}: {text}")

        return self._apply_case_rules(text)

def encrypt_file(
    cipher: SubstitutionCipher,
    input_path: str,
    output_path: str,
    encoding: str = "utf-8"
):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file '{input_path}' not found.")

    with open(input_path, "r", encoding=encoding) as infile, \
         open(output_path, "w", encoding=encoding) as outfile:
        for line in infile:
            outfile.write(cipher.encrypt(line.rstrip('\n')) + '\n')
    print(f"[EncryptFile] Output written to {output_path}")


def decrypt_file(
    cipher: SubstitutionCipher,
    input_path: str,
    output_path: str,
    encoding: str = "utf-8"
):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file '{input_path}' not found.")

    with open(input_path, "r", encoding=encoding) as infile, \
         open(output_path, "w", encoding=encoding) as outfile:
        for line in infile:
            outfile.write(cipher.decrypt(line.rstrip('\n')) + '\n')
    print(f"[DecryptFile] Output written to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Substitution Cipher CLI Tool")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-e", "--encrypt", metavar="INPUT", help="Encrypt the given input file")
    group.add_argument("-d", "--decrypt", metavar="INPUT", help="Decrypt the given input file")

    parser.add_argument("-o", "--output", required=True, help="Output file path")
    parser.add_argument("-a", "--alphabet", default="ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                        help="Alphabet to use (default: A-Z)")
    parser.add_argument("-n", "--num-layers", type=int, default=1,
                        help="Number of substitution layers (default: 1)")
    parser.add_argument("-s", "--seed", type=int, default=None,
                        help="Random seed (for reproducible results)")
    parser.add_argument("-rc", "--random-choice", action="store_true",
                        help="Use random substitution layer selection")
    parser.add_argument("-ic", "--ignore-case", action="store_true",
                        help="Ignore case during encryption/decryption")
    parser.add_argument("-fc", "--force-case", choices=["upper", "lower"],
                        help="Force all output to given case")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Setup config and cipher
    substitutions = SubstitutionCipherConfig.generate_multiple_random_substitutions(
        alphabet=args.alphabet,
        count=args.num_layers,
        seed=args.seed
    )

    config = SubstitutionCipherConfig(
        alphabet=args.alphabet,
        substitutions=substitutions,
        num_layers=args.num_layers,
        random_choice=args.random_choice,
        ignore_case=args.ignore_case,
        force_case=args.force_case,
        random_seed=args.seed
    )

    cipher = SubstitutionCipher(config, verbose=args.verbose)

    # File operation
    if args.encrypt:
        encrypt_file(cipher, args.encrypt, args.output)
    elif args.decrypt:
        decrypt_file(cipher, args.decrypt, args.output)


if __name__ == "__main__":
    main()
