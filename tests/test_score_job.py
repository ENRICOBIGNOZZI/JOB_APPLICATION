from job_agent.matching.score_job import score_job
from job_agent.models import Job


def _targets():
    return {
        "role_keywords": {
            "strong": ["quant researcher", "quant trader"],
            "medium": ["software engineer"],
            "weak": ["internship"],
        },
        "finance_keywords": ["alpha", "trading", "portfolio"],
        "ml_keywords": ["machine learning", "python"],
        "locations": {"preferred": ["Zurich", "London"], "remote_ok": True},
        "seniority": {"prefer": ["phd"], "avoid": ["director"]},
        "negative_keywords": ["sales"],
        "score_weights": {
            "title_strong": 30,
            "title_medium": 14,
            "title_weak": 5,
            "description_finance": 18,
            "description_ml": 12,
            "location_preferred": 20,
            "remote": 8,
            "seniority_prefer": 7,
            "seniority_avoid": -20,
            "negative": -45,
            "source_known": 4,
            "description_length": 3,
        },
    }


def test_score_prefers_quant_finance_role():
    job = Job(
        company="test",
        title="Quant Researcher",
        location="Zurich",
        url="https://example.com/1",
        description="Alpha research, portfolio construction, machine learning, Python, PhD welcome.",
        source="lever",
    )
    assert score_job(job, _targets()) > 70


def test_score_penalizes_negative_terms():
    job = Job(
        company="test",
        title="Sales Analyst",
        location="London",
        url="https://example.com/2",
        description="Sales role for trading clients.",
        source="lever",
    )
    assert score_job(job, _targets()) < 0
