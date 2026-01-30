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
      rounds/
        R01/
          prices_drivers.csv
          prices_constructors.csv
          notes.json
      derived/
        driver_metrics.csv
        constructor_metrics.csv
        team_recommendations.csv
schemas/
src/
```

## CSV schemas

### `prices_drivers.csv`
Required columns:
- `season` (int)
- `round` (int)
- `driver_id` (string, Ergast driverId, e.g. `max_verstappen`)
- `driver_name` (string)
- `constructor` (string)
- `price` (number)

### `prices_constructors.csv`
Required columns:
- `season` (int)
- `round` (int)
- `constructor_id` (string, Ergast constructorId, e.g. `red_bull`)
- `constructor_name` (string)
- `price` (number)

## Quick start

1) Put weekly snapshots in `data/seasons/2025/rounds/RXX/`.
2) Run:

```bash
python3 -m src.compute_metrics --season 2025 --round 1
```

This will write outputs into `data/seasons/2025/derived/`.

> Note: this repo scaffolds the pipeline and file formats first. The modelling/optimisation will be filled in iteratively.
