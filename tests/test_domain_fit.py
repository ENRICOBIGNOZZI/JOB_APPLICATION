from job_agent.matching.domain import domain_scores, fit_reasons, primary_domain
from job_agent.matching.score_job import score_breakdown
from job_agent.models import Job


def test_domain_fit_detects_control_role():
    targets = {
        "role_keywords": {"strong": ["control scientist"], "medium": [], "weak": []},
        "keyword_groups": {
            "optimization_control": {
                "weight": 18,
                "cap": 3,
                "keywords": ["optimal control", "model predictive control", "optimization"],
            },
            "scientific_computing": {
                "weight": 12,
                "cap": 2,
                "keywords": ["simulation", "scientific computing"],
            },
        },
        "locations": {"preferred": ["Zurich"], "remote_ok": True},
        "seniority": {"prefer": ["postdoc"], "avoid": []},
        "negative_keywords": [],
        "score_weights": {"title_strong": 30, "location_preferred": 20, "seniority_prefer": 8},
    }
    job = Job(
        company="Example",
        title="Control Scientist",
        location="Zurich",
        url="https://example.com",
        description="Optimal control, model predictive control, optimization, postdoc profile welcome.",
        source="manual",
    )
    components = score_breakdown(job, targets)
    assert primary_domain(components).domain == "optimization_control"
    assert domain_scores(components)[0].score > 0
    assert fit_reasons(components)
