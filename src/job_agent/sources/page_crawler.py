from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin

import requests

from job_agent.models import Job
from job_agent.text import contains_any, normalize_ws


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attrs_dict = dict(attrs)
        href = attrs_dict.get("href")
        if href:
            self._href = href
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            text = normalize_ws(" ".join(self._text))
            if text:
                self.links.append((text, self._href))
            self._href = None
            self._text = []


def _fetch_html(url: str, timeout: int = 20) -> str:
    response = requests.get(
        url,
        headers={"User-Agent": "job-application-agent/0.4 (+manual-review; no-auto-submit)"},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.text


def _keywords_from_targets(targets: dict) -> list[str]:
    keywords: list[str] = []
    role_keywords = targets.get("role_keywords", {}) or {}
    for bucket in ["strong", "medium", "weak"]:
        keywords.extend(str(x) for x in role_keywords.get(bucket, []) or [])
    groups = targets.get("keyword_groups", {}) or {}
    for group in groups.values():
        if isinstance(group, dict):
            keywords.extend(str(x) for x in group.get("keywords", []) or [])
    return sorted(set(keywords), key=len, reverse=True)


def crawl_source_pages(config: dict, targets: dict) -> list[Job]:
    pages = config.get("pages", []) or []
    target_keywords = _keywords_from_targets(targets)
    jobs: list[Job] = []

    for page in pages:
        if not isinstance(page, dict):
            continue
        url = str(page.get("url", ""))
        if not url:
            continue
        include_terms = [str(x) for x in page.get("include_terms", []) or []] or target_keywords
        exclude_terms = [str(x) for x in page.get("exclude_terms", []) or []]
        organization = str(page.get("organization", "unknown"))
        region = str(page.get("region", ""))
        category = str(page.get("category", "page"))

        try:
            html = _fetch_html(url)
        except Exception:
            continue

        parser = LinkParser()
        parser.feed(html)
        for title, href in parser.links:
            text = f"{title} {href}"
            if not contains_any(text, include_terms):
                continue
            if exclude_terms and contains_any(text, exclude_terms):
                continue
            absolute_url = urljoin(url, href)
            jobs.append(
                Job(
                    company=organization,
                    title=title,
                    location=region,
                    url=absolute_url,
                    description=f"Discovered from {url}. Category: {category}. Link text: {title}.",
                    source="page_crawler",
                )
            )
    return jobs
