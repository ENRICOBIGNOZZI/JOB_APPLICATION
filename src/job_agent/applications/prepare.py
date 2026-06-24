from __future__ import annotations

import re
from pathlib import Path

from job_agent.documents.answers import render_answers
from job_agent.documents.contact_message import render_contact_message
from job_agent.documents.cover_letter import render_cover_letter
from job_agent.matching.domain import domain_scores, fit_reasons, primary_domain, risk_flags
from job_agent.matching.score_job import score_breakdown
from job_agent.models import Job


def slugify(value: str, max_len: int = 80) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-") or "job"
    return value[:max_len].strip("-")


def _job_from_row(job: dict) -> Job:
    return Job(
        company=str(job["company"]),
        title=str(job["title"]),
        location=str(job["location"]),
        url=str(job["url"]),
        description=str(job["description"]),
        source=str(job["source"]),
        date_found=str(job.get("date_found") or ""),
        score=float(job["score"]) if job.get("score") is not None else None,
        status=str(job.get("status") or "found"),
    )


def _render_fit_review(job: dict, targets: dict | None) -> str:
    if not targets:
        return "# Fit review\n\nNo targets config supplied. Run `job-agent explain --job-id <ID>` for details.\n"

    model_job = _job_from_row(job)
    components = score_breakdown(model_job, targets)
    primary = primary_domain(components)
    domains = domain_scores(components)
    reasons = fit_reasons(components)
    flags = risk_flags(components)

    lines = [
        "# Fit review",
        "",
        f"Company: {job['company']}",
        f"Title: {job['title']}",
        f"Location: {job['location']}",
        f"Score: {job['score']}",
        "",
        "## Primary domain",
        "",
        primary.label if primary else "No strong domain signal detected.",
        "",
        "## Domain scores",
        "",
    ]
    if domains:
        lines.extend(f"- {fit.label}: {fit.score:.2f}" for fit in domains)
    else:
        lines.append("- None")

    lines.extend(["", "## Fit reasons", ""])
    if reasons:
        lines.extend(f"- {reason}" for reason in reasons)
    else:
        lines.append("- None")

    lines.extend(["", "## Risk flags", ""])
    if flags:
        lines.extend(f"- {flag}" for flag in flags)
    else:
        lines.append("- None")

    lines.extend(["", "## Manual decision", "", "- Decision: TODO", "- Notes: TODO"])
    return "\n".join(lines) + "\n"


def prepare_application(
    job: dict,
    profile: dict,
    output_root: str | Path = "applications",
    targets: dict | None = None,
) -> Path:
    folder = Path(output_root) / f"{int(job['id']):04d}-{slugify(job['company'])}-{slugify(job['title'])}"
    folder.mkdir(parents=True, exist_ok=True)

    (folder / "job_description.md").write_text(
        f"# {job['company']} — {job['title']}\n\n"
        f"Location: {job['location']}\n\n"
        f"URL: {job['url']}\n\n"
        f"Source: {job['source']}\n\n"
        f"Score: {job['score']}\n\n"
        "---\n\n"
        f"{job['description']}\n",
        encoding="utf-8",
    )
    (folder / "fit_review.md").write_text(_render_fit_review(job, targets), encoding="utf-8")
    (folder / "cover_letter.md").write_text(render_cover_letter(job, profile), encoding="utf-8")
    (folder / "contact_message.txt").write_text(render_contact_message(job, profile), encoding="utf-8")
    (folder / "answers.md").write_text(render_answers(profile), encoding="utf-8")
    (folder / "application_notes.md").write_text(
        f"# Application notes\n\n"
        f"Company: {job['company']}\n\n"
        f"Title: {job['title']}\n\n"
        f"Location: {job['location']}\n\n"
        f"URL: {job['url']}\n\n"
        f"Score: {job['score']}\n\n"
        "## Fit notes\n\n"
        "- Why this role fits: see fit_review.md\n"
        "- Specific CV bullets to emphasize: TODO\n"
        "- People/company notes: TODO\n"
        "- Compensation/location constraints: TODO\n",
        encoding="utf-8",
    )
    (folder / "checklist.md").write_text(
        "# Submission checklist\n\n"
        "- [ ] CV attached and correct version selected\n"
        "- [ ] Fit review checked\n"
        "- [ ] Contact message reviewed if used\n"
        "- [ ] Cover letter reviewed and made specific\n"
        "- [ ] Standard answers reviewed\n"
        "- [ ] Work authorization answer checked\n"
        "- [ ] Compensation answer checked\n"
        "- [ ] No false claims\n"
        "- [ ] Manual submit completed\n"
        "- [ ] Tracker marked as applied\n",
        encoding="utf-8",
    )
    return folder
