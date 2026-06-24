from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime

VALID_STATUSES = {
    "found",
    "shortlisted",
    "prepared",
    "applied",
    "rejected",
    "interview",
    "offer",
    "ignored",
}


@dataclass(frozen=True)
class Job:
    company: str
    title: str
    location: str
    url: str
    description: str
    source: str
    date_found: str | None = None
    score: float | None = None
    status: str = "found"

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {self.status}")
        if not self.date_found:
            object.__setattr__(
                self,
                "date_found",
                datetime.now(tz=UTC).replace(microsecond=0).isoformat(),
            )

    def with_score(self, score: float) -> Job:
        return replace(self, score=score)
