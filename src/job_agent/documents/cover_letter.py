from __future__ import annotations


def render_cover_letter(job: dict, profile: dict) -> str:
    name = profile.get("name", "")
    headline = profile.get("headline", "")
    core = profile.get("core_profile", []) or []
    bullets = "\n".join(f"- {item}" for item in core[:4])
    return f"""# Cover letter draft: {job['company']} — {job['title']}

Dear Hiring Team,

I am applying for the **{job['title']}** role at **{job['company']}**. {headline}

The reason this role is relevant for me is the overlap between quantitative research, statistical modelling, machine learning, and live decision systems. My background is closest to roles where research quality, implementation discipline, and market intuition have to meet in code.

Relevant points:

{bullets}

For this application, I would emphasize three links to the job description:

1. **Quantitative modelling:** econometrics, statistics, time series, optimization, and model validation.
2. **Research engineering:** Python implementation, reproducible experiments, backtesting-style workflows, and diagnostics.
3. **Finance orientation:** portfolio construction, systematic strategies, risk, and trading-related modelling.

Best regards,  
{name}
"""
