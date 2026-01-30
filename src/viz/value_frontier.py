"""Value frontier (drivers): rolling points vs average price.

Creates a scatter of:
- X = avg price across season (or selected window)
- Y = rolling N-round points (default 3)
- Labels = driver abbreviation

Also computes and highlights an approximate Pareto frontier (high points, low price).

Usage:
  python -m src.viz.value_frontier --season 2025 --window 3

Output:
  outputs/value_frontier_drivers_2025_w3.html
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import plotly.express as px


def pareto_frontier(df: pd.DataFrame, x: str, y: str) -> pd.DataFrame:
    """Return rows on a simple Pareto frontier for (min x, max y)."""
    d = df.dropna(subset=[x, y]).sort_values([x, y], ascending=[True, False]).copy()
    best_y = None
    keep = []
    for _, row in d.iterrows():
        if best_y is None or row[y] > best_y:
            keep.append(True)
            best_y = row[y]
        else:
            keep.append(False)
    return d.loc[keep]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=2025)
    ap.add_argument("--window", type=int, default=3)
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[2]
    raw = root / "data" / "seasons" / str(args.season) / "raw"

    prices = pd.read_csv(raw / "f1fantasytools_prices_drivers_long.csv")
    points = pd.read_csv(raw / "f1fantasytools_points_drivers_long.csv")

    for col in ["price", "totalPoints"]:
        if col in prices.columns:
            prices[col] = pd.to_numeric(prices[col], errors="coerce")
        if col in points.columns:
            points[col] = pd.to_numeric(points[col], errors="coerce")

    prices["round"] = prices["round"].astype(int)
    points["round"] = points["round"].astype(int)

    # avg season price per driver
    avg_price = prices.groupby(["id", "abbr"], as_index=False)["price"].mean().rename(columns={"price": "avg_price"})

    # rolling window points per driver
    pts = points.sort_values(["id", "round"]).copy()
    pts["rolling_points"] = pts.groupby("id")["totalPoints"].rolling(args.window).sum().reset_index(level=0, drop=True)

    # take latest rolling value per driver (end of season)
    latest = pts.groupby(["id", "abbr"], as_index=False).tail(1)[["id", "abbr", "rolling_points"]]

    df = avg_price.merge(latest, on=["id", "abbr"], how="left")

    frontier = pareto_frontier(df, "avg_price", "rolling_points")
    df["is_frontier"] = df["id"].isin(frontier["id"].tolist())

    fig = px.scatter(
        df,
        x="avg_price",
        y="rolling_points",
        hover_name="abbr",
        hover_data={"id": True, "avg_price": ":.2f", "rolling_points": True, "is_frontier": True},
        color="is_frontier",
        title=f"Driver value frontier (Season {args.season}) — rolling {args.window}-round points vs avg price",
    )
    fig.update_layout(xaxis_title="Avg price", yaxis_title=f"Rolling {args.window}-round points (latest)")

    outdir = root / "outputs"
    outdir.mkdir(exist_ok=True)
    out = outdir / f"value_frontier_drivers_{args.season}_w{args.window}.html"
    fig.write_html(out, include_plotlyjs="cdn")
    print("Wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
