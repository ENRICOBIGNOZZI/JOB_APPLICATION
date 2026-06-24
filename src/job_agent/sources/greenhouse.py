from __future__ import annotations

from job_agent.http import get_json
from job_agent.models import Job
from job_agent.text import html_to_text, normalize_ws

API_URL = "https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"


def fetch_greenhouse_jobs(board: str) -> list[Job]:
    payload = get_json(API_URL.format(board=board))
    if not isinstance(payload, dict):
        raise ValueError(f"Unexpected Greenhouse payload for {board}")
    jobs: list[Job] = []
    for item in payload.get("jobs", []):
        if not isinstance(item, dict):
            continue
        offices = item.get("offices") or []
        office_names = [o.get("name", "") for o in offices if isinstance(o, dict) and o.get("name")]
        location = ", ".join(office_names)
        if not location:
            location = (
                (item.get("location") or {}).get("name", "")
                if isinstance(item.get("location"), dict)
                else ""
            )
        jobs.append(
            Job(
                company=board,
                title=normalize_ws(item.get("title", "")),
                location=normalize_ws(location),
                url=item.get("absolute_url", ""),
                description=html_to_text(item.get("content", "")),
                source="greenhouse",
            )
        )
    return jobs
