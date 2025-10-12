import logging
import re
from typing import List

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Simple keyword-based moderation
HARMFUL_KEYWORDS = [
    "hack", "exploit", "malware", "virus", "phishing", "scam", "illegal", "drug", "weapon"
]

def moderate_content(text: str) -> bool:
    """Check if content contains harmful keywords. Returns True if safe."""
    text_lower = text.lower()
    for keyword in HARMFUL_KEYWORDS:
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
            logger.warning(f"Harmful content detected: {keyword}")
            return False
    return True

def filter_sources(sources: List[str]) -> List[str]:
    """Filter source documents for sensitive information."""
    filtered = []
    for src in sources:
        if moderate_content(src):
            filtered.append(src)
    return filtered