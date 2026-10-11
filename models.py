"""Data models, enums, and serializable structures."""
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from enum import Enum

class CipherMode(Enum):
    SIMPLE = "simple"
    CAESAR = "caesar"
    ATBASH = "atbash"
    HOMOPHONIC = "homophonic"
    KEYWORD = "keyword"

@dataclass
class CipherKey:
    """Serializable key file format."""
    version: str = "2.0"
    alphabet: str = ""
    mode: str = "simple"
    num_layers: int = 1
    layers: List[Dict] = field(default_factory=list)
    random_seed: Optional[int] = None
    options: Dict = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, s: str) -> "CipherKey":
        return cls(**json.loads(s))

@dataclass
class AnalysisResult:
    """Results of frequency analysis."""
    text_length: int = 0
    unique_chars: int = 0
    char_frequency: Dict[str, float] = field(default_factory=dict)
    bigram_frequency: Dict[str, int] = field(default_factory=dict)
    trigram_frequency: Dict[str, int] = field(default_factory=dict)
    index_of_coincidence: float = 0.0
    entropy: float = 0.0
    language_guess: Optional[str] = None
    confidence: float = 0.0