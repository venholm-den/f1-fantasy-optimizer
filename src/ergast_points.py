"""Fetch official F1 points (drivers + constructors) from Ergast/Jolpica.

Why:
- F1 Fantasy points (from f1fantasytools) are *game scoring*.
- This script pulls *real championship points* for use in reports/PowerBI.

Outputs (written under data/seasons/<season>/raw/):
- f1_official_driver_race_points.csv        # per-race points from Results
- f1_official_constructor_race_points.csv   # per-race points from Results
- f1_official_driver_standings.csv          # cumulative points after each round
- f1_official_constructor_standings.csv     # cumulative points after each round

All tables are long-format and round-grained (season, round).

Data source:
- Tries https://api.jolpi.ca/ergast first, falls back to https://ergast.com/mrd

Notes:
- Ergast is a community API and can lag briefly after sessions.
- For seasons 2023-2025, the scoring rules (including sprint points) are already
  baked into the published race results/standings.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

import requests


BASE_URLS = [
    "https://api.jolpi.ca/ergast",
    "https://ergast.com/mrd",
]


def _get_json(path: str, *, params: dict | None = None) -> dict:
    last = None
    for base in BASE_URLS:
        url = base.rstrip("/") + "/" + path.lstrip("/")
        try:
            r = requests.get(url, params=params or {}, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last = e
            continue
    raise RuntimeError(f"Failed to fetch {path}: {last}")


def _races_for_season(season: int) -> list[dict]:
    data = _get_json(f"/f1/{season}.json", params={"limit": 1000})
    races = (((data.get("MRData") or {}).get("RaceTable") or {}).get("Races") or [])
    if not races:
        raise RuntimeError(f"No races returned for season {season}")
    return races


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


@dataclass
class RoundInfo:
    season: int
    round: int
    race_name: str


def _rounds(season: int) -> list[RoundInfo]:
    out: list[RoundInfo] = []
    for r in _races_for_season(season):
        out.append(
            RoundInfo(
                season=int(r["season"]),
                round=int(r["round"]),
                race_name=r.get("raceName") or "",
            )
        )
    return out


def fetch_race_points(season: int) -> tuple[list[dict], list[dict]]:
    """Return (driver_rows, constructor_rows) with *per-race* points."""
    driver_rows: list[dict] = []
    constructor_rows: list[dict] = []

    for rd in _rounds(season):
        data = _get_json(f"/f1/{season}/{rd.round}/results.json", params={"limit": 500})
        races = (((data.get("MRData") or {}).get("RaceTable") or {}).get("Races") or [])
        if not races:
            continue
        results = (races[0].get("Results") or [])

        # Aggregate constructor points from driver results (P1 + P2 finishers etc.)
        # This matches the constructor points definition used for standings.
        c_points: dict[str, float] = {}
        c_meta: dict[str, dict] = {}

        for res in results:
            drv = res.get("Driver") or {}
            con = res.get("Constructor") or {}
            pts = float(res.get("points") or 0)

            driver_rows.append(
                {
                    "season": season,
                    "round": rd.round,
                    "raceName": rd.race_name,
                    "position": int(res.get("position") or 0) or "",
                    "points": pts,
                    "driverCode": (drv.get("code") or "").strip().upper(),
                    "ergast_driver_id": (drv.get("driverId") or "").strip(),
                    "driver_givenName": drv.get("givenName") or "",
                    "driver_familyName": drv.get("familyName") or "",
                    "constructorCode": (con.get("constructorId") or "").strip(),
                    "constructor_name": con.get("name") or "",
                }
            )

            cid = (con.get("constructorId") or "").strip()
            if cid:
                c_points[cid] = c_points.get(cid, 0.0) + pts
                c_meta[cid] = {"constructorCode": cid, "constructor_name": con.get("name") or ""}

        for cid, pts in sorted(c_points.items(), key=lambda kv: (-kv[1], kv[0])):
            meta = c_meta.get(cid) or {}
            constructor_rows.append(
                {
                    "season": season,
                    "round": rd.round,
                    "raceName": rd.race_name,
                    "points": pts,
                    "constructorCode": meta.get("constructorCode") or cid,
                    "constructor_name": meta.get("constructor_name") or "",
                }
            )

    return driver_rows, constructor_rows


def fetch_standings(season: int) -> tuple[list[dict], list[dict]]:
    """Return (driver_rows, constructor_rows) with *cumulative* points after each round."""
    driver_rows: list[dict] = []
    constructor_rows: list[dict] = []

    for rd in _rounds(season):
        d = _get_json(
            f"/f1/{season}/{rd.round}/driverStandings.json",
            params={"limit": 500},
        )
        c = _get_json(
            f"/f1/{season}/{rd.round}/constructorStandings.json",
            params={"limit": 500},
        )

        dlists = (((d.get("MRData") or {}).get("StandingsTable") or {}).get("StandingsLists") or [])
        clists = (((c.get("MRData") or {}).get("StandingsTable") or {}).get("StandingsLists") or [])

        if dlists:
            for row in (dlists[0].get("DriverStandings") or []):
                drv = row.get("Driver") or {}
                cons = (row.get("Constructors") or [])
                con0 = cons[0] if cons else {}
                driver_rows.append(
                    {
                        "season": season,
                        "round": rd.round,
                        "raceName": rd.race_name,
                        "position": int(row.get("position") or 0) or "",
                        "points": float(row.get("points") or 0),
                        "wins": int(row.get("wins") or 0),
                        "driverCode": (drv.get("code") or "").strip().upper(),
                        "ergast_driver_id": (drv.get("driverId") or "").strip(),
                        "driver_givenName": drv.get("givenName") or "",
                        "driver_familyName": drv.get("familyName") or "",
                        "constructorCode": (con0.get("constructorId") or "").strip(),
                        "constructor_name": con0.get("name") or "",
                    }
                )

        if clists:
            for row in (clists[0].get("ConstructorStandings") or []):
                con = row.get("Constructor") or {}
                constructor_rows.append(
                    {
                        "season": season,
                        "round": rd.round,
                        "raceName": rd.race_name,
                        "position": int(row.get("position") or 0) or "",
                        "points": float(row.get("points") or 0),
                        "wins": int(row.get("wins") or 0),
                        "constructorCode": (con.get("constructorId") or "").strip(),
                        "constructor_name": con.get("name") or "",
                    }
                )

    return driver_rows, constructor_rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument(
        "--mode",
        choices=["race", "standings", "both"],
        default="both",
        help="race=per-race points, standings=cumulative after each round, both=emit all",
    )
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    raw_dir = root / "data" / "seasons" / str(args.season) / "raw"

    if args.mode in ("race", "both"):
        drows, crows = fetch_race_points(args.season)
        _write_csv(
            raw_dir / "f1_official_driver_race_points.csv",
            drows,
            [
                "season",
                "round",
                "raceName",
                "position",
                "points",
                "driverCode",
                "ergast_driver_id",
                "driver_givenName",
                "driver_familyName",
                "constructorCode",
                "constructor_name",
            ],
        )
        _write_csv(
            raw_dir / "f1_official_constructor_race_points.csv",
            crows,
            ["season", "round", "raceName", "points", "constructorCode", "constructor_name"],
        )
        print("Wrote race points to", raw_dir)

    if args.mode in ("standings", "both"):
        drows, crows = fetch_standings(args.season)
        _write_csv(
            raw_dir / "f1_official_driver_standings.csv",
            drows,
            [
                "season",
                "round",
                "raceName",
                "position",
                "points",
                "wins",
                "driverCode",
                "ergast_driver_id",
                "driver_givenName",
                "driver_familyName",
                "constructorCode",
                "constructor_name",
            ],
        )
        _write_csv(
            raw_dir / "f1_official_constructor_standings.csv",
            crows,
            [
                "season",
                "round",
                "raceName",
                "position",
                "points",
                "wins",
                "constructorCode",
                "constructor_name",
            ],
        )
        print("Wrote standings to", raw_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
