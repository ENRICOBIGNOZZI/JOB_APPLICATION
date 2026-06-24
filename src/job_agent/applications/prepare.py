from __future__ import annotations

import re
from pathlib import Path

from job_agent.documents.answers import render_answers
from job_agent.documents.cover_letter import render_cover_letter


def slugify(value: str, max_len: int = 80) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-") or "job"
    return value[:max_len].strip("-")


def prepare_application(job: dict, profile: dict, output_root: str | Path = "applications") -> Path:
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
    (folder / "cover_letter.md").write_text(render_cover_letter(job, profile), encoding="utf-8")
    (folder / "answers.md").write_text(render_answers(profile), encoding="utf-8")
    (folder / "application_notes.md").write_text(
        f"# Application notes\n\n"
        f"Company: {job['company']}\n\n"
        f"Title: {job['title']}\n\n"
        f"Location: {job['location']}\n\n"
        f"URL: {job['url']}\n\n"
        f"Score: {job['score']}\n\n"
        "## Fit notes\n\n"
        "- Why this role fits: TODO\n"
        "- Specific CV bullets to emphasize: TODO\n"
        "- People/company notes: TODO\n"
        "- Compensation/location constraints: TODO\n",
        encoding="utf-8",
    )
    (folder / "checklist.md").write_text(
        "# Submission checklist\n\n"
        "- [ ] CV attached and correct version selected\n"
        "- [ ] Cover letter reviewed and made specific\n"
        "- [ ] Work authorization answer checked\n"
        "- [ ] Compensation answer checked\n"
        "- [ ] No false claims\n"
        "- [ ] Manual submit completed\n"
        "- [ ] Tracker marked as applied\n",
        encoding="utf-8",
    )
    return folder
