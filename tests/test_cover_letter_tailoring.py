from job_agent.documents.cover_letter import render_motivation_text


def test_motivation_text_uses_job_description_themes():
    job = {
        "company": "Example Lab",
        "title": "Research Scientist in Optimization and Scientific Computing",
        "location": "Zurich",
        "description": "Numerical optimization, scientific computing, simulation, kernel methods, uncertainty quantification.",
    }
    profile = {
        "name": "Chiara Segala",
        "core_profile": [
            "Research focus: numerical analysis, optimization, kernel methods, uncertainty quantification.",
        ],
    }
    text = render_motivation_text(job, profile)
    assert "Research Scientist in Optimization" in text
    assert "scientific computing" in text
    assert "optimization" in text
    assert "Chiara Segala" in text
