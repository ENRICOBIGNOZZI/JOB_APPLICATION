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
    targets = {
        "role_keywords": {"strong": ["quant trader"], "medium": [], "weak": []},
        "keyword_groups": {"finance": {"weight": 10, "cap": 2, "keywords": ["trading", "research"]}},
        "locations": {"preferred": ["London"], "remote_ok": True},
        "seniority": {"prefer": [], "avoid": []},
        "negative_keywords": [],
        "score_weights": {"title_strong": 30, "location_preferred": 20},
    }
    folder = prepare_application(job, profile, output_root=tmp_path, targets=targets)
    assert (folder / "cover_letter.md").exists()
    assert (folder / "job_description.md").exists()
    assert (folder / "fit_review.md").exists()
    assert (folder / "contact_message.txt").exists()
    assert (folder / "answers.md").exists()
    assert "Jane Street" in (folder / "cover_letter.md").read_text(encoding="utf-8")
    assert "Domain scores" in (folder / "fit_review.md").read_text(encoding="utf-8")
