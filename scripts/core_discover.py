from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from job_agent.config import load_targets, load_yaml
from job_agent.db import connect, list_jobs, upsert_jobs
from job_agent.matching.score_job import score_job
from job_agent.models import Job
from job_agent.sources.greenhouse import fetch_greenhouse_jobs
from job_agent.sources.lever import fetch_lever_jobs
from job_agent.sources.page_crawler import crawl_source_pages
from job_agent.sources.page_sources import load_source_pages_csv
from job_agent.text import contains_any, normalize_ws

console = Console()


def _as_list(value: object) -> list[str]:
    return [str(x) for x in value] if isinstance(value, list) else []


def _region_terms(targets: dict, mode: str) -> list[str]:
    locations = targets.get("locations", {}) or {}
    if mode == "all":
        return []
    if mode == "core":
        return _as_list(locations.get("core"))
    if mode == "core-secondary":
        return _as_list(locations.get("core")) + _as_list(locations.get("secondary"))
    if mode == "core-secondary-acceptable":
        return (
            _as_list(locations.get("core"))
            + _as_list(locations.get("secondary"))
            + _as_list(locations.get("acceptable"))
        )
    raise ValueError(f"Unknown region mode: {mode}")


def _region_ok(job: Job, targets: dict, mode: str) -> bool:
    terms = _region_terms(targets, mode)
    if not terms:
        return True
    text = f"{job.location} {job.description} {job.title}"
    return contains_any(text, terms)


def _score_filter(jobs: list[Job], targets: dict, min_score: float, region_mode: str) -> list[Job]:
    scored: list[Job] = []
    for job in jobs:
        if not job.url or not job.title:
            continue
        if not _region_ok(job, targets, region_mode):
            continue
        candidate = job.with_score(score_job(job, targets))
        if candidate.score is not None and candidate.score >= min_score:
            scored.append(candidate)
    return scored


def _dedupe_in_memory(jobs: list[Job]) -> list[Job]:
    best: dict[str, Job] = {}
    for job in jobs:
        key = "|".join(
            normalize_ws(part).lower()
            for part in [job.company, job.title, job.location]
        )
        prev = best.get(key)
        if prev is None or (job.score or -9999) > (prev.score or -9999):
            best[key] = job
    return list(best.values())


def dedupe_db(conn: sqlite3.Connection) -> int:
    rows = conn.execute("SELECT * FROM jobs ORDER BY score DESC NULLS LAST, id ASC").fetchall()
    seen: set[str] = set()
    delete_ids: list[int] = []
    for row in rows:
        key = "|".join(
            normalize_ws(str(row[col])).lower()
            for col in ["company", "title", "location"]
        )
        if key in seen:
            delete_ids.append(int(row["id"]))
        else:
            seen.add(key)
    for job_id in delete_ids:
        conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    return len(delete_ids)


def _print_rank(conn: sqlite3.Connection, min_score: float, limit: int) -> None:
    rows = list_jobs(conn, min_score=min_score, limit=limit)
    table = Table(title="Ranked discovered jobs")
    for col in ["id", "score", "source", "company", "title", "location"]:
        table.add_column(col)
    for row in rows:
        table.add_row(
            str(row["id"]),
            f"{row['score']:.2f}" if row["score"] is not None else "",
            str(row["source"])[:14],
            str(row["company"])[:24],
            str(row["title"])[:60],
            str(row["location"])[:36],
        )
    console.print(table)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Discover specific job announcements into the DB, dedupe, score, then rank. No browser tabs. No submit."
    )
    parser.add_argument("--db", default="chiara_core.sqlite")
    parser.add_argument("--targets", default="configs/targets.yaml")
    parser.add_argument("--boards", default="configs/direct_boards.yaml")
    parser.add_argument("--sources", default="configs/source_pages.csv")
    parser.add_argument("--min-score", type=float, default=-20.0, help="Minimum score to save after scoring.")
    parser.add_argument("--rank-min-score", type=float, default=0.0, help="Minimum score to display in final rank.")
    parser.add_argument("--limit", type=int, default=150)
    parser.add_argument(
        "--region-mode",
        default="core",
        choices=["core", "core-secondary", "core-secondary-acceptable", "all"],
        help="Hard region filter before saving. Use core for Switzerland/Paris/France/Northern Italy first.",
    )
    parser.add_argument("--no-ats", action="store_true")
    parser.add_argument("--no-pages", action="store_true")
    args = parser.parse_args()

    targets = load_targets(args.targets)
    jobs: list[Job] = []

    if not args.no_ats:
        boards_cfg = load_yaml(args.boards)
        for board in boards_cfg.get("greenhouse", []) or []:
            try:
                found = fetch_greenhouse_jobs(str(board))
                jobs.extend(found)
                console.print(f"[green]greenhouse[/green] {board}: {len(found)} jobs")
            except Exception as exc:  # noqa: BLE001
                console.print(f"[yellow]skip greenhouse:{board}: {exc}[/yellow]")
        for company in boards_cfg.get("lever", []) or []:
            try:
                found = fetch_lever_jobs(str(company))
                jobs.extend(found)
                console.print(f"[green]lever[/green] {company}: {len(found)} jobs")
            except Exception as exc:  # noqa: BLE001
                console.print(f"[yellow]skip lever:{company}: {exc}[/yellow]")

    if not args.no_pages:
        page_cfg = load_source_pages_csv(args.sources)
        found = crawl_source_pages(page_cfg, targets)
        jobs.extend(found)
        console.print(f"[green]source pages[/green]: {len(found)} candidate links")

    scored = _score_filter(jobs, targets, args.min_score, args.region_mode)
    scored = _dedupe_in_memory(scored)

    conn = connect(args.db)
    saved = upsert_jobs(conn, scored)
    deleted = dedupe_db(conn)
    console.print(f"Saved/updated {saved} jobs in {args.db}; removed {deleted} duplicate row(s).")
    _print_rank(conn, min_score=args.rank_min_score, limit=args.limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
