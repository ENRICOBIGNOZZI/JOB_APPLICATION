from job_agent.db import connect, get_job, list_jobs, update_status, upsert_jobs
from job_agent.models import Job


def test_upsert_and_status(tmp_path):
    conn = connect(tmp_path / "jobs.sqlite")
    n = upsert_jobs(
        conn,
        [
            Job(
                company="A",
                title="Quant Trader",
                location="London",
                url="https://example.com/a",
                description="Trading role",
                source="csv",
                score=75,
            )
        ],
    )
    assert n == 1
    rows = list_jobs(conn)
    assert len(rows) == 1
    update_status(conn, rows[0]["id"], "shortlisted", "good fit")
    assert get_job(conn, rows[0]["id"])["status"] == "shortlisted"
