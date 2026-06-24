from job_agent.db import connect, import_jobs_csv, list_jobs


def test_import_jobs_csv(tmp_path):
    path = tmp_path / "jobs.csv"
    path.write_text(
        "company,title,location,url,description\n"
        "A,Quant Researcher,Zurich,https://example.com/a,Alpha research\n",
        encoding="utf-8",
    )
    conn = connect(tmp_path / "jobs.sqlite")
    assert import_jobs_csv(conn, path) == 1
    assert list_jobs(conn)[0]["company"] == "A"
