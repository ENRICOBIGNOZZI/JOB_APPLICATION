from __future__ import annotations

import html
import re

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def html_to_text(value: str | None) -> str:
    if not value:
        return ""
    text = html.unescape(value)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p>", "\n\n", text)
    text = _TAG_RE.sub(" ", text)
    return normalize_ws(text)


def normalize_ws(value: str | None) -> str:
    if not value:
        return ""
    value = value.replace("\xa0", " ")
    value = _WS_RE.sub(" ", value).strip()
    return value


def contains_any(text: str, terms: list[str] | tuple[str, ...] | set[str]) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in terms)


def count_matches(text: str, terms: list[str] | tuple[str, ...] | set[str]) -> int:
    lower = text.lower()
    return sum(1 for term in terms if term.lower() in lower)
