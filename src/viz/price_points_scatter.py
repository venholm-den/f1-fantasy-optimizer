"""Create an interactive scatter: price vs points (per round), with optional animation.

Reads raw f1fantasytools CSVs and writes HTML to outputs/.

Usage:
  python -m src.viz.price_points_scatter --season 2025

Outputs:
  outputs/price_vs_points_drivers_2025.html
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

    prices = pd.read_csv(raw / "f1fantasytools_prices_drivers_long.csv")
    points = pd.read_csv(raw / "f1fantasytools_points_drivers_long.csv")

    df = prices.merge(points[["season", "round", "id", "totalPoints"]], on=["season", "round", "id"], how="left")

    # Clean up types
    for col in ["price", "priceChange", "percentOwned", "x2PercentOwned", "totalPoints"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["round"] = df["round"].astype(int)

    fig = px.scatter(
        df,
        x="price",
        y="totalPoints",
        animation_frame="round",
        hover_name="abbr",
        hover_data={
            "id": True,
            "price": ":.2f",
            "priceChange": ":.2f",
            "percentOwned": ":.1f",
            "totalPoints": True,
        },
        size="percentOwned",
        size_max=40,
        title=f"F1 Fantasy Tools: Driver price vs points (Season {args.season})",
    )
    fig.update_layout(xaxis_title="Price", yaxis_title="Total points")

    outdir = root / "outputs"
    outdir.mkdir(exist_ok=True)
    out = outdir / f"price_vs_points_drivers_{args.season}.html"
    fig.write_html(out, include_plotlyjs="cdn")
    print("Wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
