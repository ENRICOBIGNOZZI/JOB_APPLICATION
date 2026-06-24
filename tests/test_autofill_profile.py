from job_agent.apply.autofill import alias_map, flatten_answers


def test_flatten_answers_and_aliases():
    profile = {
        "candidate": {"first_name": "Chiara", "email": "chiara@example.com"},
        "answers": {"relocation": "Open"},
        "files": {"resume": "documents/cv.pdf"},
        "field_aliases": {"first_name": ["First Name", "Given name"]},
    }
    values = flatten_answers(profile)
    aliases = alias_map(profile)
    assert values["first_name"] == "Chiara"
    assert values["relocation"] == "Open"
    assert values["resume"] == "documents/cv.pdf"
    assert aliases["first_name"] == ["first name", "given name"]
