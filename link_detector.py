from __future__ import annotations

import re
from typing import Iterable

URL_PATTERNS = [
    re.compile(r"https?://[^\s]+", re.IGNORECASE),
    re.compile(r"www\.[^\s]+", re.IGNORECASE),
    re.compile(r"\b[a-z0-9][a-z0-9-]{0,62}\.(com|cn|net|org|io|co|cc|vip|top|xyz|site|shop|online|tv|me|link|app|info|biz|pro|tech|store|live|fm|im|ink|cloud|ai|hk|us|uk|jp|de|fr|ru|sg|tw|mo)(/[\w\-./?%&=:#]*)?\b", re.IGNORECASE),
    re.compile(r"\b[a-z0-9-]+\.(com|cn|net|org|io|co|cc|vip|top|xyz|site|shop|online|tv|me|link|app|info|biz|pro|tech|store|live|fm|im|ink|cloud|ai)\b", re.IGNORECASE),
]


def find_links(text: str) -> list[str]:
    if not text:
        return []
    hits: list[str] = []
    for pattern in URL_PATTERNS:
        for match in pattern.findall(text):
            if isinstance(match, tuple):
                matched = ''.join(str(x) for x in match if x)
                # tuple return for grouped regex is not useful; use full match instead
                continue
        for match in pattern.finditer(text):
            value = match.group(0).strip()
            if value and value not in hits:
                hits.append(value)
    return hits


def contains_link(texts: Iterable[str]) -> tuple[bool, list[str]]:
    all_hits: list[str] = []
    for text in texts:
        for hit in find_links(text or ""):
            if hit not in all_hits:
                all_hits.append(hit)
    return (len(all_hits) > 0, all_hits)
