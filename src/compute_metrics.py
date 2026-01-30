"""Compute baseline metrics from a weekly price snapshot.

This intentionally starts simple:
- validates that required CSVs exist
- loads driver/constructor prices
- writes PowerBI-friendly derived CSVs with basic fields

Next iterations will add:
- Ergast/Jolpica ingestion (results/quali/sprint)
- pace + DNF modelling
- expected fantasy points + optimisation under budget
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--round", type=int, required=True)
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    snap = root / "data" / "seasons" / str(args.season) / "rounds" / f"R{args.round:02d}"
    drivers_csv = snap / "prices_drivers.csv"
    constructors_csv = snap / "prices_constructors.csv"
    notes_json = snap / "notes.json"

    if not drivers_csv.exists():
        raise SystemExit(f"Missing {drivers_csv}")
    if not constructors_csv.exists():
        raise SystemExit(f"Missing {constructors_csv}")

    drivers = read_csv(drivers_csv)
    constructors = read_csv(constructors_csv)

    notes = {}
    if notes_json.exists():
        notes = json.loads(notes_json.read_text(encoding="utf-8"))

    derived = root / "data" / "seasons" / str(args.season) / "derived"

    # Minimal derived tables (placeholders)
    driver_rows = []
    for d in drivers:
        driver_rows.append(
            {
                "season": args.season,
                "round": args.round,
                "driver_id": d.get("driver_id"),
                "driver_name": d.get("driver_name"),
                "constructor": d.get("constructor"),
                "price": d.get("price"),
                "expected_points": "",  # to be computed later
                "dnf_risk": "",  # to be computed later
                "pace_score": "",  # to be computed later
                "value_score": "",  # to be computed later
            }
        )

    constructor_rows = []
    for c in constructors:
        constructor_rows.append(
            {
                "season": args.season,
                "round": args.round,
                "constructor_id": c.get("constructor_id"),
                "constructor_name": c.get("constructor_name"),
                "price": c.get("price"),
                "expected_points": "",
                "reliability": "",
                "value_score": "",
            }
        )

    write_csv(
        derived / "driver_metrics.csv",
        driver_rows,
        [
            "season",
            "round",
            "driver_id",
            "driver_name",
            "constructor",
            "price",
            "expected_points",
            "dnf_risk",
            "pace_score",
            "value_score",
        ],
    )

    write_csv(
        derived / "constructor_metrics.csv",
        constructor_rows,
        [
            "season",
            "round",
            "constructor_id",
            "constructor_name",
            "price",
            "expected_points",
            "reliability",
            "value_score",
        ],
    )

    # Placeholder recommendations table
    write_csv(
        derived / "team_recommendations.csv",
        [
            {
                "season": args.season,
                "round": args.round,
                "team_name": "placeholder",
                "drivers": "",
                "constructors": "",
                "total_price": "",
                "expected_points": "",
                "drs_boost": "",
                "chip_suggestion": "",
                "notes": notes.get("notes", ""),
            }
        ],
        [
            "season",
            "round",
            "team_name",
            "drivers",
            "constructors",
            "total_price",
            "expected_points",
            "drs_boost",
            "chip_suggestion",
            "notes",
        ],
    )

    print(f"Wrote derived outputs to: {derived}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
