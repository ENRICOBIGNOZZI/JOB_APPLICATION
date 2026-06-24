from __future__ import annotations


def render_contact_message(job: dict, profile: dict) -> str:
    name = profile.get("name", "")
    headline = profile.get("headline", "")
    cv_path = profile.get("cv_path", "documents/cv_chiara_segala.pdf")
    core = profile.get("core_profile", []) or []
    top_points = "\n".join(f"- {point}" for point in core[:3])

    return f"""Subject: Application package draft — {name} — {job['title']}

Dear Chiara,

I prepared an application package draft for the following role:

Company: {job['company']}
Role: {job['title']}
Location: {job['location']}
URL: {job['url']}
Score: {job['score']}

Profile summary:
{headline}

Most relevant CV points for this role:
{top_points}

Files to review locally:
- {cv_path}
- job_description.md
- fit_review.md
- cover_letter.md
- application_notes.md
- answers.md
- checklist.md

Please review the fit, the cover letter, and the standard answers before any manual submission.

Best,
Enrico
"""
