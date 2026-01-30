"""Create an interactive heatmap: driver x round colored by points.

Usage:
  python -m src.viz.heatmap_points --season 2025

Outputs:
  outputs/heatmap_driver_points_2025.html
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import plotly.express as px


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=2025)
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[2]
    raw = root / "data" / "seasons" / str(args.season) / "raw"

    points = pd.read_csv(raw / "f1fantasytools_points_drivers_long.csv")
    points["totalPoints"] = pd.to_numeric(points["totalPoints"], errors="coerce")
    points["round"] = points["round"].astype(int)

    pivot = points.pivot_table(index="abbr", columns="round", values="totalPoints", aggfunc="sum")
    pivot = pivot.sort_index()

    fig = px.imshow(
        pivot,
        aspect="auto",
        color_continuous_scale="RdYlGn",
        title=f"Driver points heatmap (Season {args.season})",
        labels={"x": "Round", "y": "Driver", "color": "Points"},
    )

    outdir = root / "outputs"
    outdir.mkdir(exist_ok=True)
    out = outdir / f"heatmap_driver_points_{args.season}.html"
    fig.write_html(out, include_plotlyjs="cdn")
    print("Wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
