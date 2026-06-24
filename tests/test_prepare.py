from job_agent.applications.prepare import prepare_application


def test_prepare_application_writes_files(tmp_path):
    job = {
        "id": 1,
        "company": "Jane Street",
        "title": "Quant Trader",
        "location": "London",
        "url": "https://example.com/job",
        "source": "lever",
        "score": 88.0,
        "description": "Trading and quantitative research.",
    }
    profile = {"name": "Enrico", "headline": "Quant profile", "core_profile": ["Python", "Stats"]}
    folder = prepare_application(job, profile, output_root=tmp_path)
    assert (folder / "cover_letter.md").exists()
    assert (folder / "job_description.md").exists()
    assert (folder / "answers.md").exists()
    assert "Jane Street" in (folder / "cover_letter.md").read_text(encoding="utf-8")
