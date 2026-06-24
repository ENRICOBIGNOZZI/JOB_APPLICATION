from __future__ import annotations

import csv
import sqlite3
from collections.abc import Iterable
from pathlib import Path

from job_agent.models import VALID_STATUSES, Job

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    location TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    source TEXT NOT NULL,
    date_found TEXT NOT NULL,
    score REAL,
    status TEXT NOT NULL DEFAULT 'found',
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS application_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY(job_id) REFERENCES jobs(id)
);
"""


def connect(db_path: str | Path = "jobs.sqlite") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def upsert_jobs(conn: sqlite3.Connection, jobs: Iterable[Job]) -> int:
    count = 0
    for job in jobs:
        conn.execute(
            """
            INSERT INTO jobs(company, title, location, url, description, source, date_found, score, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                company=excluded.company,
                title=excluded.title,
                location=excluded.location,
                description=excluded.description,
                source=excluded.source,
                date_found=excluded.date_found,
                score=excluded.score,
                status=jobs.status
            """,
            (
                job.company,
                job.title,
                job.location,
                job.url,
                job.description,
                job.source,
                job.date_found,
                job.score,
                job.status,
            ),
        )
        count += 1
    conn.commit()
    return count


def list_jobs(
    conn: sqlite3.Connection,
    min_score: float | None = None,
    status: str | None = None,
    limit: int | None = None,
) -> list[sqlite3.Row]:
    clauses: list[str] = []
    params: list[object] = []
    if min_score is not None:
        clauses.append("score >= ?")
        params.append(min_score)
    if status is not None:
        clauses.append("status = ?")
        params.append(status)
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    sql = f"SELECT * FROM jobs {where} ORDER BY score DESC NULLS LAST, id DESC"
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)
    return list(conn.execute(sql, params).fetchall())


def get_job(conn: sqlite3.Connection, job_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if row is None:
        raise KeyError(f"No job found with id={job_id}")
    return row


def update_status(conn: sqlite3.Connection, job_id: int, status: str, note: str = "") -> None:
    if status not in VALID_STATUSES:
        valid = ", ".join(sorted(VALID_STATUSES))
        raise ValueError(f"Invalid status {status!r}. Valid values: {valid}")
    conn.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
    conn.execute(
        "INSERT INTO application_events(job_id, status, note) VALUES (?, ?, ?)",
        (job_id, status, note),
    )
    conn.commit()


def import_jobs_csv(conn: sqlite3.Connection, path: str | Path) -> int:
    p = Path(path)
    with p.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        required = {"company", "title", "location", "url", "description"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV is missing columns: {sorted(missing)}")
        jobs = [
            Job(
                company=row["company"],
                title=row["title"],
                location=row["location"],
                url=row["url"],
                description=row["description"],
                source=row.get("source") or "csv",
                date_found=row.get("date_found") or None,
                score=float(row["score"]) if row.get("score") else None,
                status=row.get("status") or "found",
            )
            for row in reader
        ]
    return upsert_jobs(conn, jobs)


def export_jobs_csv(conn: sqlite3.Connection, path: str | Path) -> Path:
    rows = list_jobs(conn)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "id",
        "company",
        "title",
        "location",
        "url",
        "source",
        "date_found",
        "score",
        "status",
        "notes",
    ]
    with p.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in fields})
    return p
