from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from job_agent.config import load_yaml
from job_agent.documents.cover_letter import render_cover_letter


@dataclass(frozen=True)
class FillResult:
    field: str
    value_preview: str
    ok: bool
    reason: str


FIELD_SELECTORS: dict[str, list[str]] = {
    "first_name": [
        "input#first_name",
        "input[name='first_name']",
        "input[name*='first_name' i]",
        "input[autocomplete='given-name']",
    ],
    "last_name": [
        "input#last_name",
        "input[name='last_name']",
        "input[name*='last_name' i]",
        "input[autocomplete='family-name']",
    ],
    "full_name": [
        "input#name",
        "input[name='name']",
        "input[name*='full_name' i]",
        "input[autocomplete='name']",
    ],
    "email": [
        "input#email",
        "input[name='email']",
        "input[type='email']",
        "input[autocomplete='email']",
    ],
    "phone": [
        "input#phone",
        "input[name='phone']",
        "input[type='tel']",
        "input[autocomplete='tel']",
    ],
    "location": [
        "input#location",
        "input[name='location']",
        "input[name*='location' i]",
        "input[placeholder*='location' i]",
        "input[placeholder*='city' i]",
    ],
    "country": [
        "select#country",
        "select[name='country']",
        "select[name*='country' i]",
        "input[name*='country' i]",
        "input[placeholder*='country' i]",
    ],
    "linkedin": [
        "input[name*='linkedin' i]",
        "input[id*='linkedin' i]",
        "input[placeholder*='linkedin' i]",
    ],
    "github": [
        "input[name*='github' i]",
        "input[id*='github' i]",
        "input[placeholder*='github' i]",
    ],
    "website": [
        "input[name*='website' i]",
        "input[id*='website' i]",
        "input[placeholder*='website' i]",
        "input[name*='url' i]",
    ],
    "resume": [
        "input[type='file'][name*='resume' i]",
        "input[type='file'][id*='resume' i]",
        "input[type='file'][name*='cv' i]",
        "input[type='file'][id*='cv' i]",
        "input[type='file']",
    ],
    "cover_letter": [
        "textarea[name*='cover' i]",
        "textarea[id*='cover' i]",
        "textarea[placeholder*='cover' i]",
        "input[type='file'][name*='cover' i]",
        "input[type='file'][id*='cover' i]",
    ],
    "cover_note": [
        "textarea[name*='motivation' i]",
        "textarea[id*='motivation' i]",
        "textarea[placeholder*='motivation' i]",
        "textarea[name*='additional' i]",
        "textarea[id*='additional' i]",
        "textarea[placeholder*='additional' i]",
        "textarea[name*='message' i]",
        "textarea[id*='message' i]",
    ],
}


def load_autofill_profile(path: str | Path = "configs/autofill_profile.yaml") -> dict[str, Any]:
    return load_yaml(path)


def flatten_answers(profile: dict[str, Any]) -> dict[str, str]:
    candidate = profile.get("candidate", {}) or {}
    answers = profile.get("answers", {}) or {}
    files = profile.get("files", {}) or {}
    values: dict[str, str] = {}
    for group in [candidate, answers, files]:
        for key, value in group.items():
            values[str(key)] = "" if value is None else str(value)
    return values


def alias_map(profile: dict[str, Any]) -> dict[str, list[str]]:
    aliases = profile.get("field_aliases", {}) or {}
    return {str(key): [str(item).lower() for item in value or []] for key, value in aliases.items()}


def _value_preview(value: str) -> str:
    value = value.replace("\n", " ").strip()
    return value[:80] + ("..." if len(value) > 80 else "")


def _install_hint() -> str:
    return "Install browser support with: pip install -e .[browser] && playwright install chromium"


def _plain_text(markdown: str) -> str:
    text = re.sub(r"^#+\s*", "", markdown, flags=re.MULTILINE)
    text = text.replace("**", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _job_specific_values(
    autofill_profile: dict[str, Any],
    job: dict[str, Any] | None,
    candidate_profile_path: str | Path | None,
) -> dict[str, str]:
    values = flatten_answers(autofill_profile)
    if job and candidate_profile_path:
        candidate_profile = load_yaml(candidate_profile_path)
        letter = _plain_text(render_cover_letter(job, candidate_profile))
        values["cover_note"] = letter
        values["cover_letter"] = letter
    return values


def _contexts(page):
    contexts = [page]
    contexts.extend(page.frames)
    seen = []
    unique = []
    for ctx in contexts:
        key = getattr(ctx, "url", None) or id(ctx)
        if key not in seen:
            seen.append(key)
            unique.append(ctx)
    return unique


def _try_file(locator, value: str) -> bool:
    path = Path(value).expanduser()
    if not path.exists():
        return False
    locator.set_input_files(str(path))
    return True


def _try_fill(locator, value: str) -> bool:
    try:
        tag = locator.evaluate("el => el.tagName.toLowerCase()")
        locator.scroll_into_view_if_needed(timeout=1500)
        if tag == "select":
            try:
                locator.select_option(label=value)
            except Exception:
                locator.select_option(value=value)
        else:
            locator.fill(value)
        return True
    except Exception:
        return False


def _fill_by_selector(ctx, key: str, value: str) -> str | None:
    for selector in FIELD_SELECTORS.get(key, []):
        try:
            locator = ctx.locator(selector).first
            if locator.count() <= 0:
                continue
            if key in {"resume", "cover_letter"} and selector.startswith("input[type='file'"):
                if _try_file(locator, value):
                    return f"selector matched: {selector}"
            elif _try_fill(locator, value):
                return f"selector matched: {selector}"
        except Exception:
            continue
    return None


def _fill_by_label(ctx, key: str, value: str, labels: list[str]) -> str | None:
    for label in labels:
        try:
            locator = ctx.get_by_label(label, exact=False).first
            if locator.count() <= 0:
                continue
            if key in {"resume", "cover_letter"}:
                try:
                    if _try_file(locator, value):
                        return f"label matched: {label}"
                except Exception:
                    pass
            if _try_fill(locator, value):
                return f"label matched: {label}"
        except Exception:
            continue
    return None


def _fill_key(page, key: str, value: str, labels: list[str]) -> str | None:
    for ctx in _contexts(page):
        reason = _fill_by_selector(ctx, key, value)
        if reason:
            return reason
        reason = _fill_by_label(ctx, key, value, labels)
        if reason:
            return reason
    return None


def autofill_application(
    *,
    url: str,
    profile_path: str | Path = "configs/autofill_profile.yaml",
    candidate_profile_path: str | Path | None = None,
    job: dict[str, Any] | None = None,
    headless: bool = False,
    pause: bool = True,
) -> list[FillResult]:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:
        raise RuntimeError(_install_hint()) from exc

    autofill_profile = load_autofill_profile(profile_path)
    values = _job_specific_values(autofill_profile, job, candidate_profile_path)
    aliases = alias_map(autofill_profile)
    results: list[FillResult] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        try:
            page.wait_for_load_state("networkidle", timeout=12_000)
        except PlaywrightTimeoutError:
            pass
        page.wait_for_timeout(1500)

        order = [
            "first_name",
            "last_name",
            "full_name",
            "email",
            "phone",
            "location",
            "country",
            "linkedin",
            "github",
            "website",
            "resume",
            "cover_letter",
            "cover_note",
        ]
        for key in order:
            value = values.get(key, "")
            if not value:
                continue
            labels = aliases.get(key, []) + [key.replace("_", " ")]
            reason = _fill_key(page, key, value, labels)
            if reason:
                results.append(FillResult(key, _value_preview(value), True, reason))
            else:
                results.append(FillResult(key, _value_preview(value), False, "no matching field found"))

        try:
            page.wait_for_timeout(1000)
        except PlaywrightTimeoutError:
            pass

        if pause:
            print("\nAutofill finished. Review the form manually. The script will not submit.")
            print("Press Enter in this terminal to close the browser when you are done.")
            input()
        browser.close()

    return results
