"""Normalization for lookup keys; original display text is never rewritten."""

import unicodedata


def normalize_text(text: str) -> str:
    """NFC, Unicode case folding and whitespace folding, retaining accents."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    canonical = unicodedata.normalize("NFC", text)
    return " ".join(unicodedata.normalize("NFC", canonical.casefold()).split())
