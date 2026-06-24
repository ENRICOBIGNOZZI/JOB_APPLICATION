from __future__ import annotations

import argparse
import sys
from pathlib import Path

from job_agent.config import load_targets
from job_agent.db import connect, upsert_jobs
from job_agent.matching.score_job import score_job
from job_agent.models import Job


def main() -> int:
    parser = argparse.ArgumentParser(description="Add one specific job URL to the ranked DB.")
    parser.add_argument("url")
    parser.add_argument("--db", default="chiara_core.sqlite")
    parser.add_argument("--targets", default="configs/targets.yaml")
    parser.add_argument("--company", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--location", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--description-file", default=None)
    parser.add_argument("--source", default="manual_url")
    args = parser.parse_args()

    description = args.description
    if args.description_file:
        description = Path(args.description_file).read_text(encoding="utf-8")

    job = Job(
        company=args.company,
        title=args.title,
        location=args.location,
        url=args.url,
        description=description or f"Manual job URL imported from {args.source}.",
        source=args.source,
    )
    targets = load_targets(args.targets)
    scored = job.with_score(score_job(job, targets))
    upsert_jobs(connect(args.db), [scored])
    print(f"Added: {args.company} — {args.title} | score={scored.score} | {args.url}")
    print(f"Run: job-agent rank --db {args.db} --limit 50")
    return 0


if __name__ == "__main__":
    sys.exit(main())
