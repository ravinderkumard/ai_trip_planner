import logging
import re

logger = logging.getLogger(__name__)

SUSPICIOUS_PATTERNS = [
    r"ignore (all|any|the|your|previous) instructions",
    r"disregard (all|any|the|your|previous) instructions",
    r"reveal (the )?(system prompt|prompt|secrets|api key|api keys|environment variables|env vars)",
    r"show (the )?(system prompt|prompt|secrets|api key|api keys|environment variables|env vars)",
    r"(print|dump|expose|leak) .*?(system prompt|secrets|api key|environment variables|env vars)",
    r"(os\.environ|process\.env|\.env|/etc/passwd)",
    r"(tool output|search results?) .*?(override|supersede|replace)",
    r"(execute|run) (shell|command|commands)",
]


def contains_suspicious_prompt_patterns(text: str) -> bool:
    normalized = " ".join(text.lower().split())
    return any(re.search(pattern, normalized) for pattern in SUSPICIOUS_PATTERNS)


def sanitize_untrusted_text(text: str, max_length: int = 2000) -> str:
    normalized = " ".join(str(text).split())
    cleaned = re.sub(r"(?i)(system prompt|ignore previous instructions|reveal secrets)", "[filtered]", normalized)
    return cleaned[:max_length]


def validate_place_query(place: str) -> str:
    normalized = place.strip()
    if not normalized:
        raise ValueError("Place must not be empty.")
    if len(normalized) > 120:
        raise ValueError("Place query is too long.")
    if contains_suspicious_prompt_patterns(normalized):
        logger.warning("Rejected suspicious place query")
        raise ValueError("Place query contains unsupported instructions.")
    return normalized
