# f1-fantasy-optimizer

A small, file-first pipeline to help optimise **Official F1 Fantasy** team selection using weekly **CSV price snapshots** + computed metrics.

## Goals
- PowerBI-friendly: everything important becomes a CSV in a stable folder layout.
- Reproducible: results depend on an explicit snapshot folder (no hidden state).
- Pluggable rules: budget/team composition/scoring can be updated without rewriting the pipeline.

## Data layout

```text
data/
  seasons/
    2025/
      raw/                      # scraped long-format tables (PowerBI-friendly)
      rounds/                   # optional manual snapshots (if you prefer)
      derived/                  # generated metrics/recommendations (planned)
schemas/
src/
powerbi/
```

### Raw (recommended)
The default data source is **f1fantasytools** (scraped, no login):
- `data/seasons/2025/raw/f1fantasytools_prices_*_long.csv`
- `data/seasons/2025/raw/f1fantasytools_points_*_long.csv`

IDs in these files use **f1fantasytools IDs** (e.g. `AST_ALO`, `RED`, etc.).

### Optional manual snapshots
If you want to manually store prices you copy from the official game, you can still use:
- `data/seasons/2025/rounds/RXX/prices_drivers.csv`
- `data/seasons/2025/rounds/RXX/prices_constructors.csv`

(Those schemas live under `schemas/`.)

## Quick start

### A) Pull the season tables (recommended)

```bash
python3 -m src.scrape_f1fantasytools --season 2025
python3 -m src.dimensions --season 2025
```

### A2) (Optional) Pull official F1 championship points (drivers + constructors)

This fetches *real* points from Ergast/Jolpica (not F1 Fantasy scoring) and writes round-grained CSVs under `data/seasons/<season>/raw/`.

```bash
python3 -m src.ergast_points --season 2025
# or (for your report range)
python3 -m src.ergast_points --season 2023
python3 -m src.ergast_points --season 2024
python3 -m src.ergast_points --season 2025
```

### B) Generate placeholder derived outputs

```bash
python3 -m src.compute_metrics --season 2025 --round 1
```

Outputs are written under `data/seasons/2025/derived/`.

## Optional: Python visuals

Interactive HTML visuals (Plotly) can be generated locally.

Install:
```bash
pip install -r requirements-viz.txt
```

Examples:
```bash
python3 -m src.viz.price_points_scatter --season 2025
python3 -m src.viz.heatmap_points --season 2025
```

Outputs are written to `outputs/` (gitignored).

> Note: this repo scaffolds the pipeline and file formats first. The modelling/optimisation will be filled in iteratively.

## Public dashboards (GitHub Pages + Looker Studio)

- GitHub Pages report: see [`docs/README.md`](docs/README.md)
- Looker Studio setup (using the public `mycsv/` files): see [`docs/looker-studio.md`](docs/looker-studio.md)
