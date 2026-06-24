from __future__ import annotations

import csv
from pathlib import Path


def load_source_pages_csv(path: str | Path) -> dict:
    p = Path(path)
    pages: list[dict] = []
    with p.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        required = {"organization", "category", "region", "url", "include_terms"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Source pages CSV is missing columns: {sorted(missing)}")
        for row in reader:
            pages.append(
                {
                    "organization": row["organization"],
                    "category": row["category"],
                    "region": row["region"],
                    "url": row["url"],
                    "include_terms": [term.strip() for term in row["include_terms"].split("|") if term.strip()],
                }
            )
    return {"pages": pages}
