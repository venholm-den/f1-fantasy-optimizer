#!/usr/bin/env python3
"""Combine year-suffixed CSV exports in mycsv/ into single files.

In `mycsv/`, many tables are exported as one CSV per season/year, e.g.:

  mycsv/f1_official_driver_standings/
    f1_official_driver_standings2023.csv
    f1_official_driver_standings2024.csv
    f1_official_driver_standings2025.csv

This script will concatenate those into:

  mycsv/f1_official_driver_standings/f1_official_driver_standings.csv

It keeps the existing per-year files (safe) and writes the combined file.

Usage:
  python scripts/combine_mycsv_years.py
  python scripts/combine_mycsv_years.py --dry-run
  python scripts/combine_mycsv_years.py --table f1_official_driver_standings

Notes:
- Assumes all year files for a table share the same header.
- Will refuse to combine if headers differ.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Iterable

YEAR_SUFFIX_RE = re.compile(r"^(?P<base>.+?)(?P<year>20\d\d)\.csv$", re.IGNORECASE)


def iter_year_files(table_dir: Path) -> list[Path]:
    files: list[tuple[int, Path]] = []
    for p in table_dir.glob("*.csv"):
        m = YEAR_SUFFIX_RE.match(p.name)
        if not m:
            continue
        year = int(m.group("year"))
        files.append((year, p))
    files.sort(key=lambda t: t[0])
    return [p for _, p in files]


def read_header(path: Path) -> list[str]:
    # Handle possible UTF-8 BOM.
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        return next(reader)


def write_combined(out_path: Path, inputs: Iterable[Path], *, dry_run: bool) -> int:
    inputs = list(inputs)
    if not inputs:
        return 0

    header0 = read_header(inputs[0])
    for p in inputs[1:]:
        h = read_header(p)
        if h != header0:
            raise SystemExit(
                "Header mismatch while combining:\n"
                f"  - {inputs[0].name}: {header0}\n"
                f"  - {p.name}: {h}\n"
                "Fix the exports or keep them separate."
            )

    if dry_run:
        print(f"[dry-run] Would write {out_path} from {len(inputs)} files")
        for p in inputs:
            print(f"  - {p.name}")
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as out_f:
        writer = csv.writer(out_f)
        writer.writerow(header0)

        for p in inputs:
            with p.open("r", encoding="utf-8-sig", newline="") as in_f:
                reader = csv.reader(in_f)
                # skip header
                try:
                    next(reader)
                except StopIteration:
                    continue
                for row in reader:
                    writer.writerow(row)

    print(f"Wrote {out_path} ({len(inputs)} inputs)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", help="Optional: only combine one table folder under mycsv/")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    mycsv_dir = repo_root / "mycsv"

    if not mycsv_dir.exists():
        raise SystemExit(f"mycsv/ not found at: {mycsv_dir}")

    table_dirs: list[Path]
    if args.table:
        table_dirs = [mycsv_dir / args.table]
    else:
        table_dirs = [p for p in mycsv_dir.iterdir() if p.is_dir()]

    for table_dir in sorted(table_dirs):
        if not table_dir.exists():
            raise SystemExit(f"Table folder not found: {table_dir}")

        year_files = iter_year_files(table_dir)
        if not year_files:
            continue

        # Determine base name from first file
        m = YEAR_SUFFIX_RE.match(year_files[0].name)
        assert m
        base = m.group("base")
        out_path = table_dir / f"{base}.csv"

        write_combined(out_path, year_files, dry_run=args.dry_run)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
