from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from job_agent.applications.prepare import prepare_application
from job_agent.config import load_profile, load_targets
from job_agent.db import (
    connect,
    export_jobs_csv,
    get_job,
    import_jobs_csv,
    list_jobs,
    update_status,
    upsert_jobs,
)
from job_agent.matching.domain import domain_scores, primary_domain
from job_agent.matching.score_job import rescore_jobs, score_breakdown, score_job
from job_agent.models import Job
from job_agent.sources.registry import SOURCE_FETCHERS

console = Console()


@click.group()
def main() -> None:
    """Semi-automated job discovery and application-preparation CLI."""


def _job_from_row(row) -> Job:
    return Job(
        company=row["company"],
        title=row["title"],
        location=row["location"],
        url=row["url"],
        description=row["description"],
        source=row["source"],
        date_found=row["date_found"],
        score=row["score"],
        status=row["status"],
    )


@main.command("init")
@click.option("--db", default="jobs.sqlite", show_default=True)
def init_db(db: str) -> None:
    connect(db).close()
    console.print(f"Initialized database: {db}")


@main.command()
@click.option("--db", default="jobs.sqlite", show_default=True)
@click.option("--targets", default="configs/targets.yaml", show_default=True)
def search(db: str, targets: str) -> None:
    cfg = load_targets(targets)
    companies = cfg.get("companies", {}) or {}
    jobs = []

    for source, fetcher in SOURCE_FETCHERS.items():
        for company in companies.get(source, []) or []:
            try:
                found = fetcher(company)
                jobs.extend(found)
                console.print(f"[green]{source}[/green] {company}: {len(found)} jobs")
            except Exception as exc:  # noqa: BLE001
                console.print(f"[yellow]{source} failed for {company}: {exc}[/yellow]")

    scored = [job.with_score(score_job(job, cfg)) for job in jobs if job.url and job.title]
    conn = connect(db)
    n = upsert_jobs(conn, scored)
    console.print(f"Saved/updated {n} jobs in {db}")


@main.command("import-csv")
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
@click.option("--db", default="jobs.sqlite", show_default=True)
def import_csv_cmd(path: str, db: str) -> None:
    conn = connect(db)
    n = import_jobs_csv(conn, path)
    console.print(f"Imported {n} jobs from {path}")


@main.command("rescore")
@click.option("--db", default="jobs.sqlite", show_default=True)
@click.option("--targets", default="configs/targets.yaml", show_default=True)
def rescore_cmd(db: str, targets: str) -> None:
    conn = connect(db)
    n = rescore_jobs(conn, load_targets(targets))
    console.print(f"Rescored {n} jobs")


@main.command()
@click.option("--db", default="jobs.sqlite", show_default=True)
@click.option("--min-score", default=None, type=float)
@click.option("--status", default=None)
@click.option("--limit", default=50, show_default=True)
def rank(db: str, min_score: float | None, status: str | None, limit: int) -> None:
    conn = connect(db)
    rows = list_jobs(conn, min_score=min_score, status=status, limit=limit)
    table = Table(title="Ranked jobs")
    for col in ["id", "score", "company", "title", "location", "status"]:
        table.add_column(col)
    for row in rows:
        table.add_row(
            str(row["id"]),
            f"{row['score']:.2f}" if row["score"] is not None else "",
            row["company"][:24],
            row["title"][:70],
            row["location"][:36],
            row["status"],
        )
    console.print(table)


@main.command("domains")
@click.option("--db", default="jobs.sqlite", show_default=True)
@click.option("--targets", default="configs/targets.yaml", show_default=True)
@click.option("--limit", default=50, show_default=True)
def domains_cmd(db: str, targets: str, limit: int) -> None:
    cfg = load_targets(targets)
    rows = list_jobs(connect(db), limit=limit)
    table = Table(title="Jobs by primary domain")
    for col in ["id", "score", "domain", "company", "title", "location"]:
        table.add_column(col)
    for row in rows:
        job = _job_from_row(row)
        primary = primary_domain(score_breakdown(job, cfg))
        table.add_row(
            str(row["id"]),
            f"{row['score']:.2f}" if row["score"] is not None else "",
            primary.label if primary else "No strong domain",
            row["company"][:22],
            row["title"][:55],
            row["location"][:28],
        )
    console.print(table)


@main.command()
@click.option("--db", default="jobs.sqlite", show_default=True)
@click.option("--job-id", required=True, type=int)
def show(db: str, job_id: int) -> None:
    row = get_job(connect(db), job_id)
    body = (
        f"[bold]{row['company']} — {row['title']}[/bold]\n"
        f"Location: {row['location']}\n"
        f"Score: {row['score']} | Status: {row['status']} | Source: {row['source']}\n"
        f"URL: {row['url']}\n\n"
        f"{row['description'][:3000]}"
    )
    console.print(Panel(body, title=f"Job {job_id}"))


@main.command()
@click.option("--db", default="jobs.sqlite", show_default=True)
@click.option("--targets", default="configs/targets.yaml", show_default=True)
@click.option("--job-id", required=True, type=int)
def explain(db: str, targets: str, job_id: int) -> None:
    cfg = load_targets(targets)
    row = get_job(connect(db), job_id)
    job = _job_from_row(row)
    components = score_breakdown(job, cfg)

    table = Table(title=f"Score breakdown: {job.company} — {job.title}")
    table.add_column("component")
    table.add_column("value", justify="right")
    table.add_column("detail")
    for component in components:
        table.add_row(component.name, f"{component.value:.2f}", component.detail)
    table.add_row("TOTAL", f"{sum(c.value for c in components):.2f}", "")
    console.print(table)

    domain_table = Table(title="Domain fit")
    domain_table.add_column("domain")
    domain_table.add_column("score", justify="right")
    for fit in domain_scores(components):
        domain_table.add_row(fit.label, f"{fit.score:.2f}")
    console.print(domain_table)


@main.command()
@click.option("--db", default="jobs.sqlite", show_default=True)
@click.option("--job-id", required=True, type=int)
def shortlist(db: str, job_id: int) -> None:
    update_status(connect(db), job_id, "shortlisted", "Shortlisted from CLI")
    console.print(f"Job {job_id} shortlisted")


@main.command()
@click.option("--db", default="jobs.sqlite", show_default=True)
@click.option("--profile", default="configs/profile.yaml", show_default=True)
@click.option("--targets", default="configs/targets.yaml", show_default=True)
@click.option("--job-id", required=True, type=int)
@click.option("--out", default="applications", show_default=True)
def prepare(db: str, profile: str, targets: str, job_id: int, out: str) -> None:
    conn = connect(db)
    row = get_job(conn, job_id)
    folder = prepare_application(
        dict(row),
        load_profile(profile),
        output_root=out,
        targets=load_targets(targets),
    )
    update_status(conn, job_id, "prepared", f"Prepared folder: {folder}")
    console.print(f"Prepared application folder: {folder}")


@main.command()
@click.option("--db", default="jobs.sqlite", show_default=True)
@click.option("--job-id", required=True, type=int)
@click.option("--status", "new_status", required=True)
@click.option("--note", default="")
def mark(db: str, job_id: int, new_status: str, note: str) -> None:
    update_status(connect(db), job_id, new_status, note)
    console.print(f"Job {job_id} marked as {new_status}")


@main.command()
@click.option("--db", default="jobs.sqlite", show_default=True)
def status(db: str) -> None:
    conn = connect(db)
    rows = conn.execute(
        "SELECT status, COUNT(*) AS n FROM jobs GROUP BY status ORDER BY n DESC, status"
    ).fetchall()
    table = Table(title="Application status")
    table.add_column("status")
    table.add_column("count")
    for row in rows:
        table.add_row(row["status"], str(row["n"]))
    console.print(table)


@main.command()
@click.option("--db", default="jobs.sqlite", show_default=True)
@click.option("--out", default="ranked_jobs.csv", show_default=True)
def export(db: str, out: str) -> None:
    path = export_jobs_csv(connect(db), out)
    console.print(f"Exported ranked jobs to {path}")


@main.command()
def doctor() -> None:
    checks = {
        "configs/targets.yaml": Path("configs/targets.yaml").exists(),
        "configs/profile.yaml": Path("configs/profile.yaml").exists(),
        "package src/job_agent": Path("src/job_agent").exists(),
    }
    table = Table(title="Doctor")
    table.add_column("check")
    table.add_column("ok")
    for name, ok in checks.items():
        table.add_row(name, "yes" if ok else "no")
    console.print(table)
