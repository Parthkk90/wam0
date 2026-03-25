# src/preprocessing/tokenizer.py
import spacy
from typing import Dict, List, Tuple
import hashlib

# Regex patterns for banking entity recognition
PAN_REGEX = "[A-Z]{5}[0-9]{4}[A-Z]"
AADHAAR_REGEX = "[0-9]{4}[0-9]{4}[0-9]{4}"
PHONE_REGEX = r"\+?91[6-9]\d{9}"
INCOME_PATTERN = None  # Uses spaCy IS_DIGIT, not regex

class BankingTokenizer:
    def __init__(self):
        self.nlp = spacy.blank("en")
        self._add_custom_patterns()
        self.token_map = {}  # { "ABCDE1234F": "[TOKEN:PAN:hash123]" }

    def _add_custom_patterns(self):
        ruler = self.nlp.add_pipe("entity_ruler", before="ner")
        patterns = [
            {"label": "PAN", "pattern": [{"TEXT": {"REGEX": PAN_REGEX}}]},
            {"label": "AADHAAR", "pattern": [{"TEXT": {"REGEX": AADHAAR_REGEX}}]},
            {"label": "PHONE", "pattern": [{"TEXT": {"REGEX": PHONE_REGEX}}]},
            {"label": "INCOME", "pattern": [{"IS_DIGIT": True}, {"LOWER": "rupees"}]}
        ]
        ruler.add_patterns(patterns)

    def tokenize(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Replace PII with tokens, return (text, mapping)"""
        doc = self.nlp(text)
        token_mapping = {}
        output = text

        for ent in doc.ents:
            if ent.label_ in ["PAN", "AADHAAR", "PHONE"]:
                token = f"[TOKEN:{ent.label_}:{hashlib.sha256(ent.text.encode()).hexdigest()[:8]}]"
                token_mapping[ent.text] = token
                output = output.replace(ent.text, token)

        return output, token_mapping

    def detokenize(self, text: str, mapping: Dict[str, str]) -> str:
        """Reverse mapping (for demo only; never in real output)"""
        reverse = {v: k for k, v in mapping.items()}
        for token, original in reverse.items():
            text = text.replace(token, original)
        return text
