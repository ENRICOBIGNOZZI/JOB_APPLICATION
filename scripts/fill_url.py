from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from job_agent.apply.autofill import autofill_application

console = Console()


def main() -> int:
    parser = argparse.ArgumentParser(description="Autofill a single application URL without submitting.")
    parser.add_argument("url")
    parser.add_argument("--company", default="Target company")
    parser.add_argument("--title", default="Target role")
    parser.add_argument("--location", default="")
    parser.add_argument("--description", default="")
    parser.add_argument("--description-file", default=None)
    parser.add_argument("--profile", default="configs/autofill_profile.yaml")
    parser.add_argument("--candidate-profile", default="configs/profile.yaml")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--no-pause", action="store_true")
    args = parser.parse_args()

    description = args.description
    if args.description_file:
        description = Path(args.description_file).read_text(encoding="utf-8")

    job = {
        "company": args.company,
        "title": args.title,
        "location": args.location,
        "url": args.url,
        "description": description,
        "source": "manual_url",
        "score": None,
        "status": "found",
    }
    results = autofill_application(
        url=args.url,
        profile_path=args.profile,
        candidate_profile_path=args.candidate_profile,
        job=job,
        headless=args.headless,
        pause=not args.no_pause,
    )

    table = Table(title="Browser form assistance results")
    table.add_column("field")
    table.add_column("ok")
    table.add_column("value")
    table.add_column("reason")
    for result in results:
        table.add_row(result.field, "yes" if result.ok else "no", result.value_preview, result.reason)
    console.print(table)
    console.print("Review manually. This script does not submit the form.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
