from __future__ import annotations

from collections.abc import Callable

from job_agent.models import Job
from job_agent.sources.greenhouse import fetch_greenhouse_jobs
from job_agent.sources.lever import fetch_lever_jobs

SOURCE_FETCHERS: dict[str, Callable[[str], list[Job]]] = {
    "greenhouse": fetch_greenhouse_jobs,
    "lever": fetch_lever_jobs,
}
