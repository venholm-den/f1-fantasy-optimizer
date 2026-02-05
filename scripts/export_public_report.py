#!/usr/bin/env python3
"""Copy season exports into docs/ so GitHub Pages can serve them.

Usage:
  python scripts/export_public_report.py --season 2025

It copies a handful of CSV files from:
  data/seasons/<season>/raw/
into:
  docs/data/<season>/

This is meant for MANUAL refresh: run it after you update the raw data,
then commit + push.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

FILES = [
    "f1_official_driver_standings.csv",
    "f1_official_constructor_standings.csv",
    "f1_official_driver_race_points.csv",
    "f1_official_constructor_race_points.csv",
    "dim_round.csv",
    "dim_round_dates.csv",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", default="2025")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "data" / "seasons" / str(args.season) / "raw"
    out_dir = repo_root / "docs" / "data" / str(args.season)

    if not src_dir.exists():
        raise SystemExit(f"Source directory not found: {src_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)

    copied = []
    missing = []
    for name in FILES:
        src = src_dir / name
        dst = out_dir / name
        if not src.exists():
            missing.append(name)
            continue
        shutil.copyfile(src, dst)
        copied.append(name)

    print(f"Exported season {args.season} to {out_dir}")
    if copied:
        print("Copied:")
        for n in copied:
            print(f"  - {n}")
    if missing:
        print("Missing (skipped):")
        for n in missing:
            print(f"  - {n}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
