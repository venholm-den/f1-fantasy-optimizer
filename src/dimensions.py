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
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def index_by(rows: list[dict], key: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for r in rows:
        k = (r.get(key) or "").strip()
        if not k:
            continue
        out[k] = r
    return out


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

    # Optional mappings to add Ergast ids/names for nicer visuals.
    maps_dir = root / "mappings"
    driver_map = index_by(read_csv(maps_dir / "drivers_abbr_to_ergast.csv"), "abbr")
    constructor_map = index_by(read_csv(maps_dir / "constructors_abbr_to_ergast.csv"), "abbr")

    dprices = read_csv(raw / "f1fantasytools_prices_drivers_long.csv")
    cprices = read_csv(raw / "f1fantasytools_prices_constructors_long.csv")

    rounds = sorted({(int(r["season"]), int(r["round"])) for r in dprices})
    dim_round = [{"season": s, "round": r, "season_round": f"{s}-R{r:02d}"} for s, r in rounds]

    drivers = {}
    for r in dprices:
        abbr = (r.get("abbr") or "").strip().upper()
        m = driver_map.get(abbr) or {}
        drivers[r["id"]] = {
            "driver_id": r["id"],
            "abbr": abbr,
            "ergast_driver_id": (m.get("ergast_driver_id") or "").strip(),
            "driver_name": (m.get("driver_name") or "").strip(),
        }
    dim_driver = [drivers[k] for k in sorted(drivers.keys())]

    constructors = {}
    for r in cprices:
        abbr = (r.get("abbr") or "").strip().upper()
        m = constructor_map.get(abbr) or {}
        constructors[r["id"]] = {
            "constructor_id": r["id"],
            "abbr": abbr,
            "ergast_constructor_id": (m.get("ergast_constructor_id") or "").strip(),
            "constructor_name": (m.get("constructor_name") or "").strip(),
        }
    dim_constructor = [constructors[k] for k in sorted(constructors.keys())]

    write_csv(raw / "dim_round.csv", dim_round, ["season", "round", "season_round"])
    write_csv(raw / "dim_driver.csv", dim_driver, ["driver_id", "abbr", "ergast_driver_id", "driver_name"])
    write_csv(raw / "dim_constructor.csv", dim_constructor, ["constructor_id", "abbr", "ergast_constructor_id", "constructor_name"])

    print("Wrote dim_* CSVs to", raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
