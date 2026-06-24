from __future__ import annotations

import re

THEME_KEYWORDS: dict[str, list[str]] = {
    "scientific computing and numerical methods": [
        "scientific computing",
        "numerical",
        "simulation",
        "hpc",
        "computational",
        "large-scale",
    ],
    "optimization and control": [
        "optimization",
        "optimisation",
        "optimal control",
        "model predictive control",
        "mpc",
        "robust control",
        "decision",
    ],
    "multi-agent and mean-field modelling": [
        "multi-agent",
        "multi agent",
        "mean-field",
        "mean field",
        "collective dynamics",
        "agent",
        "coordination",
    ],
    "machine learning with mathematical modelling": [
        "machine learning",
        "deep learning",
        "neural",
        "kernel",
        "surrogate",
        "reinforcement learning",
        "model behaviour",
    ],
    "uncertainty quantification and stochastic modelling": [
        "uncertainty",
        "stochastic",
        "monte carlo",
        "probabilistic",
        "robustness",
        "evaluation",
    ],
    "mathematical finance and quantitative research": [
        "quant",
        "finance",
        "trading",
        "portfolio",
        "option",
        "pricing",
        "risk",
        "derivatives",
    ],
}


def _format_item(item: object) -> str:
    if isinstance(item, dict):
        return "; ".join(f"{key}: {value}" for key, value in item.items())
    return str(item)


def _bullet_list(items: list[object], limit: int = 5) -> str:
    return "\n".join(f"- {_format_item(item)}" for item in items[:limit])


def _job_text(job: dict) -> str:
    return f"{job.get('title', '')} {job.get('company', '')} {job.get('location', '')} {job.get('description', '')}".lower()


def _matched_themes(job: dict, limit: int = 4) -> list[str]:
    text = _job_text(job)
    scored: list[tuple[int, str]] = []
    for theme, keywords in THEME_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score:
            scored.append((score, theme))
    scored.sort(reverse=True)
    return [theme for _, theme in scored[:limit]] or [
        "applied mathematics",
        "numerical analysis",
        "scientific computing",
    ]


def _matched_profile_points(job: dict, profile: dict, limit: int = 4) -> list[str]:
    text = _job_text(job)
    points = list(profile.get("core_profile", []) or [])
    pubs = list(profile.get("selected_publications", []) or [])
    projects = list(profile.get("research_projects", []) or [])
    candidates = points + pubs + projects
    ranked: list[tuple[int, str]] = []
    for item in candidates:
        clean = _format_item(item)
        tokens = {tok for tok in re.findall(r"[a-zA-Z][a-zA-Z\-]{4,}", clean.lower())}
        score = sum(1 for tok in tokens if tok in text)
        if score:
            ranked.append((score, clean))
    ranked.sort(reverse=True)
    selected = [item for _, item in ranked[:limit]]
    if selected:
        return selected
    return [_format_item(item) for item in points[:limit]]


def render_motivation_text(job: dict, profile: dict, max_chars: int = 2200) -> str:
    name = profile.get("name", "")
    themes = _matched_themes(job)
    points = _matched_profile_points(job, profile, limit=4)
    title = job.get("title", "this role")
    company = job.get("company", "your team")
    location = job.get("location", "")

    text = f"""Dear Hiring Team,

I am applying for the {title} role at {company}. My profile is in applied mathematics, numerical analysis, optimization/control, multi-agent and mean-field systems, kernel methods, uncertainty quantification, scientific computing, and mathematical finance.

The role is especially relevant to my background because the job description connects with {', '.join(themes)}. I would bring a research-oriented and computational perspective, with experience translating rigorous mathematical models into numerical and algorithmic methods.

The most relevant points from my background are:
{_bullet_list(points, 4)}

I am particularly interested in roles where mathematical modelling, robust numerical methods, and machine-learning or optimization tools are used to solve complex research or industrial problems. {('The location preference is also aligned with ' + location + '.') if location else ''}

Best regards,
{name}
""".strip()
    return text[:max_chars].rstrip()


def render_cover_letter(job: dict, profile: dict) -> str:
    return f"# Cover letter draft: {job['company']} — {job['title']}\n\n{render_motivation_text(job, profile)}\n"
