from job_agent.matching.score_job import score_breakdown, score_job
from job_agent.models import Job


def _targets():
    return {
        "role_keywords": {
            "strong": ["quant researcher", "quant trader", "research scientist", "control scientist"],
            "medium": ["software engineer", "computational biologist", "optimization engineer"],
            "weak": ["internship"],
        },
        "keyword_groups": {
            "finance": {
                "weight": 18,
                "cap": 3,
                "keywords": ["alpha", "trading", "portfolio"],
            },
            "science_biology_pharma": {
                "weight": 16,
                "cap": 4,
                "keywords": ["pharma", "biology", "bioinformatics", "scientist"],
            },
            "numerical_analysis": {
                "weight": 15,
                "cap": 3,
                "keywords": ["numerical analysis", "simulation", "scientific computing"],
            },
            "optimization_control": {
                "weight": 15,
                "cap": 3,
                "keywords": ["optimization", "control theory", "model predictive control"],
            },
            "multi_agent_systems": {
                "weight": 14,
                "cap": 3,
                "keywords": ["multi-agent", "distributed systems", "autonomous agents"],
            },
        },
        "finance_keywords": ["alpha", "trading", "portfolio"],
        "ml_keywords": ["machine learning", "python"],
        "locations": {"preferred": ["Zurich", "London", "Paris", "Ticino"], "remote_ok": True},
        "seniority": {"prefer": ["phd"], "avoid": ["director"]},
        "negative_keywords": ["sales"],
        "score_weights": {
            "title_strong": 30,
            "title_medium": 14,
            "title_weak": 5,
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


def test_score_prefers_scientific_pharma_biology_role():
    job = Job(
        company="test",
        title="Research Scientist Computational Biology",
        location="Paris",
        url="https://example.com/bio",
        description="Pharma research, biology, bioinformatics, scientific computing, PhD welcome.",
        source="csv",
    )
    assert score_job(job, _targets()) > 70


def test_score_prefers_control_and_numerical_analysis_role():
    job = Job(
        company="test",
        title="Control Scientist",
        location="Ticino",
        url="https://example.com/control",
        description="Optimization, control theory, model predictive control, numerical analysis, simulation.",
        source="csv",
    )
    assert score_job(job, _targets()) > 70


def test_score_breakdown_exposes_keyword_groups():
    job = Job(
        company="test",
        title="Optimization Engineer",
        location="Paris",
        url="https://example.com/opt",
        description="Large-scale multi-agent optimization and distributed systems.",
        source="csv",
    )
    names = {component.name for component in score_breakdown(job, _targets())}
    assert "keyword_group:optimization_control" in names
    assert "keyword_group:multi_agent_systems" in names


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
