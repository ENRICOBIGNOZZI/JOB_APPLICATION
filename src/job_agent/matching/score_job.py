from __future__ import annotations

from job_agent.models import Job
from job_agent.text import contains_any, count_matches


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(x) for x in value]
    return []


def _score_keyword_groups(full_text: str, targets: dict, weights: dict) -> float:
    groups = targets.get("keyword_groups", {}) or {}
    if groups:
        total = 0.0
        for group in groups.values():
            if not isinstance(group, dict):
                continue
            keywords = _as_list(group.get("keywords"))
            cap = int(group.get("cap", 5) or 5)
            weight = float(group.get("weight", 10) or 10)
            hits = count_matches(full_text, keywords)
            total += min(hits, cap) / cap * weight
        return total

    finance_hits = count_matches(full_text, _as_list(targets.get("finance_keywords")))
    ml_hits = count_matches(full_text, _as_list(targets.get("ml_keywords")))
    return (
        min(finance_hits, 6) / 6 * float(weights.get("description_finance", 16))
        + min(ml_hits, 5) / 5 * float(weights.get("description_ml", 13))
    )


def score_job(job: Job, targets: dict) -> float:
    role_keywords = targets.get("role_keywords", {}) or {}
    locations = targets.get("locations", {}) or {}
    seniority = targets.get("seniority", {}) or {}
    weights = targets.get("score_weights", {}) or {}

    title = f"{job.title}".lower()
    full_text = f"{job.company} {job.title} {job.location} {job.description}".lower()

    score = 0.0

    negative_terms = _as_list(targets.get("negative_keywords"))
    negative_hits = count_matches(full_text, negative_terms)
    if negative_hits:
        score += float(weights.get("negative", -45)) * negative_hits

    strong_hits = count_matches(title, _as_list(role_keywords.get("strong")))
    medium_hits = count_matches(title, _as_list(role_keywords.get("medium")))
    weak_hits = count_matches(title, _as_list(role_keywords.get("weak")))
    score += min(strong_hits, 2) * float(weights.get("title_strong", 30))
    score += min(medium_hits, 2) * float(weights.get("title_medium", 14))
    score += min(weak_hits, 2) * float(weights.get("title_weak", 5))

    score += _score_keyword_groups(full_text, targets, weights)

    preferred_locations = _as_list(locations.get("preferred"))
    if contains_any(job.location, preferred_locations):
        score += float(weights.get("location_preferred", 18))
    if locations.get("remote_ok") and "remote" in job.location.lower():
        score += float(weights.get("remote", 8))

    if contains_any(full_text, _as_list(seniority.get("prefer"))):
        score += float(weights.get("seniority_prefer", 8))
    if contains_any(full_text, _as_list(seniority.get("avoid"))):
        score += float(weights.get("seniority_avoid", -20))

    if job.source in {"greenhouse", "lever", "csv"}:
        score += float(weights.get("source_known", 4))
    if len(job.description) > 800:
        score += float(weights.get("description_length", 3))

    return round(score, 2)


def rescore_jobs(conn, targets: dict) -> int:
    rows = conn.execute("SELECT * FROM jobs").fetchall()
    for row in rows:
        job = Job(
            company=row["company"],
            title=row["title"],
            location=row["location"],
            url=row["url"],
            description=row["description"],
            source=row["source"],
            date_found=row["date_found"],
            score=row["score"],
            status=row["status"],
        )
        conn.execute("UPDATE jobs SET score = ? WHERE id = ?", (score_job(job, targets), row["id"]))
    conn.commit()
    return len(rows)
