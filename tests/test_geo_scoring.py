from job_agent.matching.score_job import score_job
from job_agent.models import Job


def _job(location: str) -> Job:
    return Job(
        company="Example",
        title="Research Scientist",
        location=location,
        url="https://example.com/job",
        description="Optimization, scientific computing, kernel methods, uncertainty quantification.",
        source="greenhouse",
    )


def test_core_geography_beats_new_york(targets):
    assert score_job(_job("Zurich, Switzerland"), targets) > score_job(_job("New York, NY"), targets)


def test_new_york_role_can_still_appear_but_is_penalized(targets):
    score = score_job(_job("New York, NY"), targets)
    assert score > 0
    assert score < score_job(_job("Paris, France"), targets)
