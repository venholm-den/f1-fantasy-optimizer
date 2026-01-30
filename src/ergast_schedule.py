"""Fetch F1 season schedule (Ergast/Jolpica) and emit dim_round_dates.csv.

Output:
- data/seasons/<season>/raw/dim_round_dates.csv

Columns:
- season (int)
- round (int)
- raceName (str)
- circuitName (str)
- locality (str)
- country (str)
- raceDate (YYYY-MM-DD)
- raceTime (HH:MM:SSZ or blank)

This is used to build a proper Calendar table in Power BI.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import requests


BASE_URLS = [
    "https://api.jolpi.ca/ergast",
    "https://ergast.com/mrd",
]


def _get_json(path: str) -> dict:
    last = None
    for base in BASE_URLS:
        url = base.rstrip("/") + "/" + path.lstrip("/")
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last = e
            continue
    raise RuntimeError(f"Failed to fetch schedule: {last}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=2025)
    args = ap.parse_args()

    data = _get_json(f"/f1/{args.season}.json")
    races = (((data.get("MRData") or {}).get("RaceTable") or {}).get("Races") or [])
    if not races:
        raise SystemExit("No races returned")

    root = Path(__file__).resolve().parents[1]
    out = root / "data" / "seasons" / str(args.season) / "raw" / "dim_round_dates.csv"
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "season",
                "round",
                "raceName",
                "circuitName",
                "locality",
                "country",
                "raceDate",
                "raceTime",
            ],
        )
        w.writeheader()
        for r in races:
            c = r.get("Circuit") or {}
            loc = c.get("Location") or {}
            w.writerow(
                {
                    "season": int(r.get("season")),
                    "round": int(r.get("round")),
                    "raceName": r.get("raceName"),
                    "circuitName": c.get("circuitName"),
                    "locality": loc.get("locality"),
                    "country": loc.get("country"),
                    "raceDate": r.get("date"),
                    "raceTime": r.get("time") or "",
                }
            )

    print("Wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
