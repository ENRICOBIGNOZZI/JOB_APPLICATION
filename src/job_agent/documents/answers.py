from __future__ import annotations


def render_answers(profile: dict) -> str:
    answers = profile.get("standard_answers", {}) or {}
    lines = ["# Standard application answers", ""]
    for key, value in answers.items():
        title = key.replace("_", " ").title()
        lines.append(f"## {title}")
        lines.append("")
        lines.append(str(value))
        lines.append("")
    lines.append("## Important")
    lines.append("")
    lines.append("Review every answer manually before submission. Do not make false claims.")
    return "\n".join(lines)
