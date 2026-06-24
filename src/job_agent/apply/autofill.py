from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from job_agent.config import load_yaml


@dataclass(frozen=True)
class FillResult:
    field: str
    value_preview: str
    ok: bool
    reason: str


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


def autofill_application(
    *,
    url: str,
    profile_path: str | Path = "configs/autofill_profile.yaml",
    headless: bool = False,
    pause: bool = True,
) -> list[FillResult]:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:
        raise RuntimeError(_install_hint()) from exc

    profile = load_autofill_profile(profile_path)
    values = flatten_answers(profile)
    aliases = alias_map(profile)
    results: list[FillResult] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)

        for key, value in values.items():
            if not value:
                continue
            labels = aliases.get(key, []) + [key.replace("_", " ")]
            filled = False
            for label in labels:
                try:
                    locator = page.get_by_label(label, exact=False).first
                    if locator.count() > 0:
                        if key == "resume" and Path(value).exists():
                            locator.set_input_files(value)
                        else:
                            locator.fill(value)
                        results.append(FillResult(key, _value_preview(value), True, f"label matched: {label}"))
                        filled = True
                        break
                except Exception:
                    pass

                selector = (
                    f"input[name*='{label}' i], textarea[name*='{label}' i], "
                    f"input[id*='{label}' i], textarea[id*='{label}' i], "
                    f"input[placeholder*='{label}' i], textarea[placeholder*='{label}' i]"
                )
                try:
                    locator = page.locator(selector).first
                    if locator.count() > 0:
                        if key == "resume" and Path(value).exists():
                            locator.set_input_files(value)
                        else:
                            locator.fill(value)
                        results.append(FillResult(key, _value_preview(value), True, f"selector matched: {label}"))
                        filled = True
                        break
                except Exception:
                    pass

            if not filled:
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
