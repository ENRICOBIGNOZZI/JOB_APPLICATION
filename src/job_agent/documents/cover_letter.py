from __future__ import annotations


def _format_item(item: object) -> str:
    if isinstance(item, dict):
        return "; ".join(f"{key}: {value}" for key, value in item.items())
    return str(item)


def _bullet_list(items: list[object], limit: int = 5) -> str:
    return "\n".join(f"- {_format_item(item)}" for item in items[:limit])


def _domain_focus(job: dict) -> str:
    text = f"{job.get('title', '')} {job.get('description', '')}".lower()
    if any(term in text for term in ["finance", "option", "pricing", "portfolio", "quant"]):
        return "mathematical finance, kernel methods, and large-scale numerical methods"
    if any(term in text for term in ["control", "optimization", "optimisation", "predictive"]):
        return "optimal control, model predictive control, and numerical optimization"
    if any(term in text for term in ["multi-agent", "multi agent", "mean-field", "crowd", "opinion"]):
        return "multi-agent systems, mean-field models, and multiscale modelling"
    if any(term in text for term in ["machine learning", "kernel", "neural", "ai", "surrogate"]):
        return "machine learning methods, kernel methods, and large-scale approximation"
    return "applied mathematics, numerical analysis, optimization, and scientific computing"


def render_cover_letter(job: dict, profile: dict) -> str:
    name = profile.get("name", "")
    headline = profile.get("headline", "")
    core = profile.get("core_profile", []) or []
    interests = profile.get("research_interests", []) or []
    projects = profile.get("research_projects", []) or []
    publications = profile.get("selected_publications", []) or []
    focus = _domain_focus(job)

    return f"""# Cover letter draft: {job['company']} — {job['title']}

Dear Hiring Team,

I am applying for the **{job['title']}** role at **{job['company']}**. {headline}

This role is relevant to my profile because it connects directly with {focus}. My background is in mathematical modelling, computational methods, and rigorous numerical algorithms for high-dimensional systems.

Relevant profile points:

{_bullet_list(core, 5)}

Research themes to emphasize:

- {', '.join(map(str, interests[:8]))}

Selected projects:

{_bullet_list(projects, 3)}

Selected publications:

{_bullet_list(publications, 3)}

Best regards,  
{name}
"""
