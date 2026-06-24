from __future__ import annotations

from job_agent.http import get_json
from job_agent.models import Job
from job_agent.text import html_to_text, normalize_ws

API_URL = "https://api.lever.co/v0/postings/{company}?mode=json"


def _description(item: dict) -> str:
    parts: list[str] = []
    if item.get("descriptionPlain"):
        parts.append(str(item["descriptionPlain"]))
    for section in item.get("lists", []) or []:
        if isinstance(section, dict):
            if section.get("text"):
                parts.append(str(section["text"]))
            for content in section.get("content", []) or []:
                if isinstance(content, dict) and content.get("text"):
                    parts.append(str(content["text"]))
    return html_to_text("\n\n".join(parts))


def fetch_lever_jobs(company: str) -> list[Job]:
    payload = get_json(API_URL.format(company=company))
    if not isinstance(payload, list):
        raise ValueError(f"Unexpected Lever payload for {company}")
    jobs: list[Job] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        categories = item.get("categories") or {}
        if not isinstance(categories, dict):
            categories = {}
        jobs.append(
            Job(
                company=company,
                title=normalize_ws(item.get("text", "")),
                location=normalize_ws(categories.get("location", "")),
                url=item.get("hostedUrl", "") or item.get("applyUrl", ""),
                description=_description(item),
                source="lever",
            )
        )
    return jobs
