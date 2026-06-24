from __future__ import annotations

from dataclasses import dataclass

from job_agent.matching.score_job import ScoreComponent

DOMAIN_COMPONENTS = {
    "core_applied_math": {"keyword_group:chiara_core", "keyword_group:math_physics"},
    "scientific_computing": {"keyword_group:scientific_computing"},
    "optimization_control": {"keyword_group:optimization_control"},
    "multi_agent_mean_field": {"keyword_group:multi_agent_systems"},
    "machine_learning": {"keyword_group:machine_learning"},
    "mathematical_finance": {"keyword_group:finance"},
    "computational_life_sciences": {"keyword_group:computational_life_sciences"},
}

DOMAIN_LABELS = {
    "core_applied_math": "Applied mathematics / numerical analysis core",
    "scientific_computing": "Scientific computing",
    "optimization_control": "Optimization and control",
    "multi_agent_mean_field": "Multi-agent / mean-field systems",
    "machine_learning": "Mathematical machine learning",
    "mathematical_finance": "Mathematical finance / quant research",
    "computational_life_sciences": "Computational life sciences",
}


@dataclass(frozen=True)
class DomainFit:
    domain: str
    label: str
    score: float


def domain_scores(components: list[ScoreComponent]) -> list[DomainFit]:
    values: dict[str, float] = {domain: 0.0 for domain in DOMAIN_COMPONENTS}
    for component in components:
        for domain, names in DOMAIN_COMPONENTS.items():
            if component.name in names:
                values[domain] += component.value

    fits = [
        DomainFit(domain=domain, label=DOMAIN_LABELS[domain], score=round(score, 2))
        for domain, score in values.items()
        if score > 0
    ]
    return sorted(fits, key=lambda item: item.score, reverse=True)


def primary_domain(components: list[ScoreComponent]) -> DomainFit | None:
    fits = domain_scores(components)
    return fits[0] if fits else None


def fit_reasons(components: list[ScoreComponent], min_component: float = 5.0) -> list[str]:
    reasons: list[str] = []
    for fit in domain_scores(components)[:3]:
        reasons.append(f"Strong domain signal: {fit.label} ({fit.score:.2f})")

    for component in sorted(components, key=lambda item: item.value, reverse=True):
        if component.value >= min_component and component.name.startswith("title_"):
            reasons.append(f"Relevant title match: {component.detail} (+{component.value:.2f})")
        if component.value >= min_component and component.name == "location_preferred":
            reasons.append(f"Preferred region/location: {component.detail} (+{component.value:.2f})")
        if component.value >= min_component and component.name == "seniority_prefer":
            reasons.append(f"Compatible seniority/research level (+{component.value:.2f})")
    return reasons[:8]


def risk_flags(components: list[ScoreComponent]) -> list[str]:
    flags: list[str] = []
    for component in components:
        if component.name == "negative_keywords":
            flags.append(f"Negative keyword hit: {component.detail} ({component.value:.2f})")
        if component.name == "seniority_avoid":
            flags.append(f"Seniority may be too high or managerial ({component.value:.2f})")
    if not domain_scores(components):
        flags.append("No strong domain signal from configured keyword groups")
    return flags
