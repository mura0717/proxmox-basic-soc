"""General-purpose text utility functions."""

import re

def normalize_text(text: str) -> str:
    """Normalizes text for consistent comparison."""
    if not isinstance(text, str):
        return ""
    # Remove special characters and extra whitespace, convert to lowercase
    normalized = re.sub(r'[()"/*-]', ' ', text.lower())
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized
