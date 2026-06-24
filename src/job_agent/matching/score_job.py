from __future__ import annotations

from dataclasses import dataclass

from job_agent.models import Job
from job_agent.text import contains_any, count_matches


@dataclass(frozen=True)
class ScoreComponent:
    name: str
    value: float
    detail: str


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(x) for x in value]
    return []


def _keyword_group_components(full_text: str, targets: dict, weights: dict) -> list[ScoreComponent]:
    groups = targets.get("keyword_groups", {}) or {}
    components: list[ScoreComponent] = []
    if groups:
        for name, group in groups.items():
            if not isinstance(group, dict):
                continue
            keywords = _as_list(group.get("keywords"))
            cap = int(group.get("cap", 5) or 5)
            weight = float(group.get("weight", 10) or 10)
            hits = count_matches(full_text, keywords)
            value = min(hits, cap) / cap * weight
            if value:
                components.append(ScoreComponent(f"keyword_group:{name}", value, f"{hits} hits, cap={cap}"))
        return components

    finance_hits = count_matches(full_text, _as_list(targets.get("finance_keywords")))
    ml_hits = count_matches(full_text, _as_list(targets.get("ml_keywords")))
    components.append(
        ScoreComponent(
            "legacy_finance_keywords",
            min(finance_hits, 6) / 6 * float(weights.get("description_finance", 16)),
            f"{finance_hits} hits",
        )
    )
    components.append(
        ScoreComponent(
            "legacy_ml_keywords",
            min(ml_hits, 5) / 5 * float(weights.get("description_ml", 13)),
            f"{ml_hits} hits",
        )
    )
    return [c for c in components if c.value]


def _location_components(job: Job, locations: dict, weights: dict) -> list[ScoreComponent]:
    text = job.location or ""
    components: list[ScoreComponent] = []

    core_terms = _as_list(locations.get("core"))
    secondary_terms = _as_list(locations.get("secondary"))
    acceptable_terms = _as_list(locations.get("acceptable"))
    avoid_terms = _as_list(locations.get("avoid"))

    if core_terms and contains_any(text, core_terms):
        components.append(
            ScoreComponent("location_core", float(weights.get("location_core", 45)), text)
        )
    elif secondary_terms and contains_any(text, secondary_terms):
        components.append(
            ScoreComponent("location_secondary", float(weights.get("location_secondary", 22)), text)
        )
    elif acceptable_terms and contains_any(text, acceptable_terms):
        components.append(
            ScoreComponent("location_acceptable", float(weights.get("location_acceptable", 8)), text)
        )
    elif contains_any(text, _as_list(locations.get("preferred"))):
        components.append(
            ScoreComponent("location_preferred", float(weights.get("location_preferred", 18)), text)
        )

    avoid_hits = count_matches(text, avoid_terms)
    if avoid_hits:
        components.append(
            ScoreComponent(
                "location_avoid",
                float(weights.get("location_avoid", -35)) * avoid_hits,
                f"{avoid_hits} avoid location hits: {text}",
            )
        )

    if avoid_hits and (contains_any(text, core_terms) or contains_any(text, secondary_terms)):
        components.append(
            ScoreComponent(
                "location_mixed_global",
                float(weights.get("location_mixed_global", -20)),
                text,
            )
        )

    if locations.get("remote_ok") and "remote" in text.lower():
        components.append(ScoreComponent("remote", float(weights.get("remote", 8)), text))

    return components


def score_breakdown(job: Job, targets: dict) -> list[ScoreComponent]:
    role_keywords = targets.get("role_keywords", {}) or {}
    locations = targets.get("locations", {}) or {}
    seniority = targets.get("seniority", {}) or {}
    weights = targets.get("score_weights", {}) or {}

    title = f"{job.title}".lower()
    full_text = f"{job.company} {job.title} {job.location} {job.description}".lower()
    components: list[ScoreComponent] = []

    negative_terms = _as_list(targets.get("negative_keywords"))
    negative_hits = count_matches(full_text, negative_terms)
    if negative_hits:
        components.append(
            ScoreComponent(
                "negative_keywords",
                float(weights.get("negative", -45)) * negative_hits,
                f"{negative_hits} hits",
            )
        )

    strong_hits = count_matches(title, _as_list(role_keywords.get("strong")))
    medium_hits = count_matches(title, _as_list(role_keywords.get("medium")))
    weak_hits = count_matches(title, _as_list(role_keywords.get("weak")))
    if strong_hits:
        components.append(
            ScoreComponent(
                "title_strong",
                min(strong_hits, 2) * float(weights.get("title_strong", 30)),
                f"{strong_hits} title hits",
            )
        )
    if medium_hits:
        components.append(
            ScoreComponent(
                "title_medium",
                min(medium_hits, 2) * float(weights.get("title_medium", 14)),
                f"{medium_hits} title hits",
            )
        )
    if weak_hits:
        components.append(
            ScoreComponent(
                "title_weak",
                min(weak_hits, 2) * float(weights.get("title_weak", 5)),
                f"{weak_hits} title hits",
            )
        )

    components.extend(_keyword_group_components(full_text, targets, weights))
    components.extend(_location_components(job, locations, weights))

    if contains_any(full_text, _as_list(seniority.get("prefer"))):
        components.append(
            ScoreComponent("seniority_prefer", float(weights.get("seniority_prefer", 8)), "preferred seniority term")
        )
    if contains_any(full_text, _as_list(seniority.get("avoid"))):
        components.append(
            ScoreComponent("seniority_avoid", float(weights.get("seniority_avoid", -20)), "avoid seniority term")
        )

    if job.source in {"greenhouse", "lever", "csv", "manual", "manual_url", "linkedin", "page_crawler"}:
        components.append(ScoreComponent("source_known", float(weights.get("source_known", 4)), job.source))
    if len(job.description) > 800:
        components.append(
            ScoreComponent("description_length", float(weights.get("description_length", 3)), f"{len(job.description)} chars")
        )

    return components


def score_job(job: Job, targets: dict) -> float:
    return round(sum(component.value for component in score_breakdown(job, targets)), 2)


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
