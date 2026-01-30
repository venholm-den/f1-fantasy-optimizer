"""Scrape season tables from f1fantasytools.com/statistics.

The site embeds a big JSON blob into the HTML via Next.js flight data.
We extract that, then export long-format CSVs suitable for PowerBI.

Outputs:
- data/seasons/<season>/raw/f1fantasytools_points_drivers_long.csv
- data/seasons/<season>/raw/f1fantasytools_points_constructors_long.csv
- data/seasons/<season>/raw/f1fantasytools_prices_drivers_long.csv
- data/seasons/<season>/raw/f1fantasytools_prices_constructors_long.csv

Fields include round, abbreviation, price, totalPoints, nnTotalPoints, priceChange.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]


def _extract_season_blob(html: str) -> dict:
    # Find the embedded chunk containing seasonResult and raceResults
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)\s*;?', html, flags=re.S)
    big = None
    for c in chunks:
        if "seasonResult" in c and "raceResults" in c:
            big = c
            break
    if not big:
        raise RuntimeError("Could not find embedded seasonResult blob")

    # Unescape JS string escapes (\" etc)
    raw = big.encode("utf-8").decode("unicode_escape")

    # raw looks like: 5:["$","$L..",null,{"seasonResult":{...}}]
    start = raw.find('{"seasonResult"')
    end = raw.rfind("}")
    if start < 0 or end < 0:
        raise RuntimeError("Could not locate JSON object in blob")

    import json

    obj = json.loads(raw[start : end + 1])
    return obj


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
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

    url = "https://f1fantasytools.com/statistics"
    html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60).text
    blob = _extract_season_blob(html)

    sr = blob.get("seasonResult") or {}
    season = int(sr.get("season") or args.season)
    race_results = (sr.get("raceResults") or {})

    drivers_points = []
    drivers_prices = []
    constructors_points = []
    constructors_prices = []

    for round_str, rr in race_results.items():
        rnd = int(round_str)
        for d in rr.get("drivers") or []:
            drivers_points.append(
                {
                    "season": season,
                    "round": rnd,
                    "id": d.get("id"),
                    "abbr": d.get("abbreviation"),
                    "type": d.get("type"),
                    "totalPoints": d.get("totalPoints"),
                    "nnTotalPoints": d.get("nnTotalPoints"),
                }
            )
            drivers_prices.append(
                {
                    "season": season,
                    "round": rnd,
                    "id": d.get("id"),
                    "abbr": d.get("abbreviation"),
                    "price": d.get("price"),
                    "priceChange": d.get("priceChange"),
                    "percentOwned": d.get("percentOwned"),
                    "x2PercentOwned": d.get("x2PercentOwned"),
                }
            )

        for c in rr.get("constructors") or []:
            constructors_points.append(
                {
                    "season": season,
                    "round": rnd,
                    "id": c.get("id"),
                    "abbr": c.get("abbreviation"),
                    "type": c.get("type"),
                    "totalPoints": c.get("totalPoints"),
                    "nnTotalPoints": c.get("nnTotalPoints"),
                }
            )
            constructors_prices.append(
                {
                    "season": season,
                    "round": rnd,
                    "id": c.get("id"),
                    "abbr": c.get("abbreviation"),
                    "price": c.get("price"),
                    "priceChange": c.get("priceChange"),
                    "percentOwned": c.get("percentOwned"),
                    "x2PercentOwned": c.get("x2PercentOwned"),
                }
            )

    outdir = ROOT / "data" / "seasons" / str(season) / "raw"
    _write_csv(
        outdir / "f1fantasytools_points_drivers_long.csv",
        ["season", "round", "id", "abbr", "type", "totalPoints", "nnTotalPoints"],
        drivers_points,
    )
    _write_csv(
        outdir / "f1fantasytools_points_constructors_long.csv",
        ["season", "round", "id", "abbr", "type", "totalPoints", "nnTotalPoints"],
        constructors_points,
    )
    _write_csv(
        outdir / "f1fantasytools_prices_drivers_long.csv",
        ["season", "round", "id", "abbr", "price", "priceChange", "percentOwned", "x2PercentOwned"],
        drivers_prices,
    )
    _write_csv(
        outdir / "f1fantasytools_prices_constructors_long.csv",
        ["season", "round", "id", "abbr", "price", "priceChange", "percentOwned", "x2PercentOwned"],
        constructors_prices,
    )

    print(f"Wrote f1fantasytools tables to {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
