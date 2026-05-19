from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from app.utils.text_cleaner import normalize_text

try:
    import yaml
except ModuleNotFoundError:
    yaml = None

PRIORITY_ORDER = ("alta_prioridad", "media_prioridad", "baja_prioridad")


@dataclass(frozen=True)
class KeywordMatch:
    keyword: str
    match_type: str
    context: str


class KeywordMatcher:
    def __init__(self, keywords_path: str | Path) -> None:
        with Path(keywords_path).open(encoding="utf-8") as fh:
            if yaml is not None:
                self.keywords: dict[str, list[str]] = yaml.safe_load(fh) or {}
            else:
                self.keywords = _load_simple_yaml(fh.read())

    def find_matches(self, *parts: str | None) -> list[KeywordMatch]:
        original = " ".join(part or "" for part in parts)
        normalized = normalize_text(original)
        matches: list[KeywordMatch] = []
        for match_type, words in self.keywords.items():
            for keyword in words or []:
                normalized_keyword = normalize_text(keyword)
                if re.search(rf"\b{re.escape(normalized_keyword)}\b", normalized):
                    matches.append(
                        KeywordMatch(keyword=keyword, match_type=match_type, context=self._context(original, keyword))
                    )
        return matches

    @staticmethod
    def _context(text: str, keyword: str, width: int = 80) -> str:
        normalized_text = normalize_text(text)
        idx = normalized_text.find(normalize_text(keyword))
        if idx < 0:
            return text[:width]
        start = max(0, idx - width // 2)
        end = min(len(text), idx + len(keyword) + width // 2)
        return text[start:end].strip()


def _load_simple_yaml(content: str) -> dict[str, list[str]]:
    data: dict[str, list[str]] = {}
    current: str | None = None
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith(":"):
            current = line[:-1]
            data[current] = []
        elif line.startswith("- ") and current:
            data[current].append(line[2:].strip())
    return data
