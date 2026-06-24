from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import quote_plus, urljoin, urlparse, urlunparse

from rich.console import Console
from rich.table import Table

from job_agent.config import load_targets, load_yaml
from job_agent.db import connect, list_jobs, upsert_jobs
from job_agent.matching.score_job import score_job
from job_agent.models import Job
from job_agent.text import normalize_ws

console = Console()


def _clean_linkedin_url(url: str) -> str:
    absolute = urljoin("https://www.linkedin.com", url)
    parsed = urlparse(absolute)
    path = parsed.path
    match = re.search(r"/jobs/view/(\d+)", path)
    if match:
        path = f"/jobs/view/{match.group(1)}/"
    return urlunparse(("https", "www.linkedin.com", path, "", "", ""))


def _search_urls(matrix: dict, *, region: str | None, keyword: str | None, limit: int) -> list[dict[str, str]]:
    regions = matrix.get("regions", {}) or {}
    keywords = matrix.get("keywords", []) or []
    rows: list[dict[str, str]] = []
    for region_key, region_cfg in regions.items():
        if region and region_key != region:
            continue
        if not isinstance(region_cfg, dict):
            continue
        location = str(region_cfg.get("label", region_key))
        for raw_keyword in keywords:
            kw = str(raw_keyword)
            if keyword and keyword.lower() not in kw.lower():
                continue
            rows.append(
                {
                    "region": region_key,
                    "location": location,
                    "keyword": kw,
                    "url": "https://www.linkedin.com/jobs/search/?keywords="
                    + quote_plus(kw)
                    + "&location="
                    + quote_plus(location),
                }
            )
            if len(rows) >= limit:
                return rows
    return rows


def _extract_cards(page, fallback_location: str) -> list[dict[str, str]]:
    data = page.evaluate(
        """
        () => {
          const anchors = Array.from(document.querySelectorAll("a[href*='/jobs/view/']"));
          const rows = [];
          const seen = new Set();
          for (const a of anchors) {
            const href = a.href || a.getAttribute('href') || '';
            if (!href || seen.has(href)) continue;
            seen.add(href);
            const card = a.closest('li') || a.closest('[data-job-id]') || a.closest('.job-card-container') || a.closest('div');
            const text = (card ? card.innerText : a.innerText || '').split('\n').map(x => x.trim()).filter(Boolean);
            const title = (a.innerText || text[0] || '').trim();
            let company = '';
            let location = '';
            for (const line of text) {
              if (!company && line !== title && !line.match(/Promoted|Viewed|Easy Apply|Actively reviewing/i)) company = line;
              else if (!location && line.match(/Switzerland|Suisse|Schweiz|Zurich|Zürich|Lugano|Ticino|Basel|Geneva|Genève|Lausanne|Paris|France|Milan|Milano|Turin|Torino|Italy|Italia|Remote|Hybrid/i)) location = line;
            }
            if (title && href) rows.push({title, company, location, url: href, text: text.slice(0, 12).join(' | ')});
          }
          return rows;
        }
        """
    )
    jobs: list[dict[str, str]] = []
    for item in data or []:
        title = normalize_ws(str(item.get("title", "")))
        if not title or title.lower() in {"jobs", "show more"}:
            continue
        jobs.append(
            {
                "title": title,
                "company": normalize_ws(str(item.get("company") or "LinkedIn company")),
                "location": normalize_ws(str(item.get("location") or fallback_location)),
                "url": _clean_linkedin_url(str(item.get("url", ""))),
                "description": normalize_ws(str(item.get("text") or "Discovered from LinkedIn Jobs visible results.")),
            }
        )
    return jobs


def _print_rank(db: str, limit: int) -> None:
    rows = list_jobs(connect(db), limit=limit)
    table = Table(title="Ranked jobs after LinkedIn discovery")
    for col in ["id", "score", "source", "company", "title", "location"]:
        table.add_column(col)
    for row in rows:
        table.add_row(
            str(row["id"]),
            f"{row['score']:.2f}" if row["score"] is not None else "",
            str(row["source"])[:12],
            str(row["company"])[:24],
            str(row["title"])[:60],
            str(row["location"])[:34],
        )
    console.print(table)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect visible LinkedIn job cards into the same ranked DB. No auto-apply, no credential handling, no submit."
    )
    parser.add_argument("--db", default="chiara_core.sqlite")
    parser.add_argument("--targets", default="configs/targets.yaml")
    parser.add_argument("--matrix", default="configs/core_search_matrix.yaml")
    parser.add_argument("--profile-dir", default=".browser_profiles/linkedin")
    parser.add_argument("--region", default=None, help="Region key, e.g. ticino, lugano, zurich, paris, milan")
    parser.add_argument("--keyword", default=None, help="Keyword substring filter")
    parser.add_argument("--searches", type=int, default=20, help="Number of LinkedIn search pages to visit sequentially")
    parser.add_argument("--per-search", type=int, default=25, help="Max cards to save per search page")
    parser.add_argument("--scrolls", type=int, default=2)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--rank-limit", type=int, default=100)
    args = parser.parse_args()

    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError:
        raise RuntimeError("Install browser support with: pip install -e .[browser] && playwright install chromium")

    targets = load_targets(args.targets)
    matrix = load_yaml(args.matrix)
    searches = _search_urls(matrix, region=args.region, keyword=args.keyword, limit=args.searches)
    if not searches:
        console.print("[red]No LinkedIn searches generated. Check --region/--keyword.[/red]")
        return 1

    jobs: list[Job] = []
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=args.profile_dir,
            headless=args.headless,
            viewport={"width": 1440, "height": 1000},
        )
        page = context.new_page()
        for idx, search in enumerate(searches, start=1):
            console.print(f"[cyan]{idx}/{len(searches)}[/cyan] LinkedIn {search['region']} | {search['keyword']}")
            page.goto(search["url"], wait_until="domcontentloaded", timeout=60_000)
            try:
                page.wait_for_load_state("networkidle", timeout=8_000)
            except PlaywrightTimeoutError:
                pass
            for _ in range(max(args.scrolls, 0)):
                page.mouse.wheel(0, 2500)
                page.wait_for_timeout(1200)
            cards = _extract_cards(page, fallback_location=search["location"])
            for card in cards[: args.per_search]:
                job = Job(
                    company=card["company"] or "LinkedIn company",
                    title=card["title"],
                    location=card["location"] or search["location"],
                    url=card["url"],
                    description=card["description"]
                    + f" Search keyword: {search['keyword']}. Search location: {search['location']}.",
                    source="linkedin",
                )
                jobs.append(job.with_score(score_job(job, targets)))
        context.close()

    saved = upsert_jobs(connect(args.db), jobs)
    console.print(f"Saved/updated {saved} LinkedIn jobs into {args.db}.")
    _print_rank(args.db, args.rank_limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
