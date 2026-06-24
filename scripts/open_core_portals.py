from __future__ import annotations

import argparse
import csv
import sys
import time
import webbrowser
from pathlib import Path
from urllib.parse import quote_plus

import yaml


def load_matrix(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def build_rows(matrix: dict, source: str | None, region: str | None, keyword: str | None) -> list[dict[str, str]]:
    regions = matrix.get("regions", {}) or {}
    keywords = matrix.get("keywords", []) or []
    portals = matrix.get("portals", {}) or {}
    rows: list[dict[str, str]] = []

    for portal_name, portal in portals.items():
        if source and portal_name != source:
            continue
        if not isinstance(portal, dict) or not portal.get("enabled", True):
            continue
        template = str(portal.get("url_template", ""))
        if not template:
            continue
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
                url = template.format(query=quote_plus(kw), location=quote_plus(location))
                rows.append(
                    {
                        "source": portal_name,
                        "region": region_key,
                        "location": location,
                        "keyword": kw,
                        "url": url,
                    }
                )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Open or export broad core-region job portal searches.")
    parser.add_argument("--matrix", default="configs/core_search_matrix.yaml")
    parser.add_argument("--source", default=None, help="Filter source, e.g. linkedin, jobs_ch, jobup, indeed")
    parser.add_argument("--region", default=None, help="Filter region key, e.g. ticino, lugano, zurich, paris, milan")
    parser.add_argument("--keyword", default=None, help="Substring filter over keywords")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--open", action="store_true", help="Open URLs in browser. Otherwise only print/export.")
    parser.add_argument("--sleep", type=float, default=0.4, help="Delay between browser tabs when --open is used.")
    parser.add_argument("--out", default=None, help="Optional CSV export path.")
    args = parser.parse_args()

    rows = build_rows(load_matrix(Path(args.matrix)), args.source, args.region, args.keyword)
    selected = rows[args.offset : args.offset + args.limit]

    if args.out:
        out = Path(args.out)
        with out.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=["source", "region", "location", "keyword", "url"])
            writer.writeheader()
            writer.writerows(selected)
        print(f"Exported {len(selected)} search URLs to {out}")

    for i, row in enumerate(selected, start=args.offset + 1):
        print(f"{i:04d} | {row['source']} | {row['region']} | {row['keyword']} | {row['url']}")
        if args.open:
            webbrowser.open(row["url"])
            time.sleep(args.sleep)

    print(f"\nSelected {len(selected)} of {len(rows)} generated search URLs.")
    if not args.open:
        print("Add --open to open these searches in the browser. Open small batches to avoid clutter.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
