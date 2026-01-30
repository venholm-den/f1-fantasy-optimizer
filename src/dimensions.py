"""Build simple dimension tables for PowerBI.

Creates:
- data/seasons/<season>/raw/dim_round.csv
- data/seasons/<season>/raw/dim_driver.csv
- data/seasons/<season>/raw/dim_constructor.csv

These are generated from the f1fantasytools long tables.
"""

from __future__ import annotations

import argparse
import csv
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
    ap.add_argument("--season", type=int, default=2025)
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    raw = root / "data" / "seasons" / str(args.season) / "raw"

    dprices = read_csv(raw / "f1fantasytools_prices_drivers_long.csv")
    cprices = read_csv(raw / "f1fantasytools_prices_constructors_long.csv")

    rounds = sorted({(int(r["season"]), int(r["round"])) for r in dprices})
    dim_round = [{"season": s, "round": r, "season_round": f"{s}-R{r:02d}"} for s, r in rounds]

    drivers = {}
    for r in dprices:
        drivers[r["id"]] = {"driver_id": r["id"], "abbr": r.get("abbr") or ""}
    dim_driver = [drivers[k] for k in sorted(drivers.keys())]

    constructors = {}
    for r in cprices:
        constructors[r["id"]] = {"constructor_id": r["id"], "abbr": r.get("abbr") or ""}
    dim_constructor = [constructors[k] for k in sorted(constructors.keys())]

    write_csv(raw / "dim_round.csv", dim_round, ["season", "round", "season_round"])
    write_csv(raw / "dim_driver.csv", dim_driver, ["driver_id", "abbr"])
    write_csv(raw / "dim_constructor.csv", dim_constructor, ["constructor_id", "abbr"])

    print("Wrote dim_* CSVs to", raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
