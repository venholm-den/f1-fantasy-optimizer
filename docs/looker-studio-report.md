# Build the Looker Studio report (using `mycsv/`)

This guide assumes you already have the public CSV exports in this repo under `mycsv/`.

If you haven’t connected the data sources yet, start with:
- [`docs/looker-studio.md`](looker-studio.md)

---

## 0) Pick which tables to use (recommended set)

If you want a report that works across **multiple seasons** without having to swap data sources, use the **combined** (all-years) CSVs:

- Driver standings (season/round position):
  - `mycsv/f1_official_driver_standings/f1_official_driver_standings.csv`
- Constructor standings:
  - `mycsv/f1_official_constructor_standings/f1_official_constructor_standings.csv`
- Driver race points (per race):
  - `mycsv/f1_official_driver_race_points/f1_official_driver_race_points.csv`
- Constructor race points:
  - `mycsv/f1_official_constructor_race_points/f1_official_constructor_race_points.csv`
- Round dimension (race metadata):
  - `mycsv/dim_round/dim_round.csv`
  - `mycsv/dim_round_dates/dim_round_dates.csv`

F1 Fantasy Tools (useful for price/ownership trends):
- Driver prices (long):
  - `mycsv/f1fantasytools_prices_drivers_long/f1fantasytools_prices_drivers_long.csv`
- Constructor prices (long):
  - `mycsv/f1fantasytools_prices_constructors_long/f1fantasytools_prices_constructors_long.csv`
- Driver points (long):
  - `mycsv/f1fantasytools_points_drivers_long/f1fantasytools_points_drivers_long.csv`
- Constructor points (long):
  - `mycsv/f1fantasytools_points_constructors_long/f1fantasytools_points_constructors_long.csv`

Raw URL format:

```text
https://raw.githubusercontent.com/venholm-den/f1-fantasy-optimizer/main/mycsv/<table>/<table>.csv
```

---

## 1) Create the data sources

### Option A — via Google Sheets (fastest)

For each CSV you want to use:

1. Create (or reuse) a Google Sheet.
2. In a new tab, put this in `A1`:

```gs
=IMPORTDATA("https://raw.githubusercontent.com/venholm-den/f1-fantasy-optimizer/main/mycsv/<table>/<table>.csv")
```

3. In Looker Studio: **Create → Data source → Google Sheets** → pick that tab.

Repeat per table.

### Option B — via BigQuery (best long-term)

Load each CSV into BigQuery tables (or create views) and connect Looker Studio to BigQuery.

---

## 2) Fix field types (do this once per data source)

In Looker Studio → **Data sources** → open each source and confirm:

- `season` = **Number**
- `round` = **Number**
- `points` = **Number**
- `wins` = **Number**
- `position` = **Number** (some rows may be blank for DNS/DNF; blanks are OK)

If you have a round date column, set it to a **Date** type.

Tip: CSV imports sometimes make numeric columns **Text**. Switch them to Number so charts sort correctly.

---

## 3) Create a new report

1. Looker Studio → **Create → Report**
2. Add at least one data source (start with driver standings).

---

## 4) Add controls (filters) you’ll want everywhere

### A) Season dropdown

Add a control:
- **Add a control → Drop-down list**
- Dimension: `season`
- Sort: `season` descending

### B) Round selector (optional)

If you want a “current round” view:
- Drop-down list
- Dimension: `round`

---

## 5) Build the core pages (suggested layout)

### Page 1 — Overview

**Chart 1: Top drivers (bar chart)**
- Data source: `f1_official_driver_standings`
- Dimension: `driver_familyName` (or `driverAbbr`)
- Metric: `points`
- Sort by `points` desc
- Filter: (optional) `round` = max (see note below)

**Chart 2: Top constructors (bar chart)**
- Data source: `f1_official_constructor_standings`
- Dimension: `constructor_name`
- Metric: `points`

**Table: Driver standings**
- Dimensions: `position`, `driver_givenName`, `driver_familyName`, `constructor_name`
- Metrics: `points`, `wins`
- Add filter controls for `season` (and `round` if desired)

Note on “latest round only”:
- Looker Studio can do this via a chart filter like “round equals X”, but dynamic max-round filtering is easier if you use BigQuery (a view that selects the max round per season).
- If you stay in Sheets/CSV-only, a simple approach is: include all rounds and use a Round control.

### Page 2 — Race-by-race

**Time series: points by round**
- Source: `f1_official_driver_race_points`
- Dimension: `round` (or a date field if you have one)
- Metric: `points`
- Breakdown dimension: `driverAbbr` (or driver name)
- Add a filter for a single driver (optional control)

### Page 3 — Fantasy prices / ownership (optional)

**Scatter: price vs points**
- Source: `f1fantasytools_points_drivers_long` blended with `f1fantasytools_prices_drivers_long`
- Join key: `season`, `round`, `id`

If you don’t want to blend yet, start with one table and build simple price trend lines:
- Dimension: `round`
- Metric: `price`
- Breakdown: `abbr`

---

## 6) Calculated fields ("measures" like DAX)

Looker Studio doesn’t support DAX, and it doesn’t have a single semantic model like Power BI.
Instead you typically use **Calculated fields** (either at the *data source* level or the *chart* level).

Where to add them:
- **Data source calculated field**: reusable across the whole report (recommended)
- **Chart calculated field**: only for one chart

In Looker Studio:
- Edit report → pick a chart → **Data** panel → **Add a field**
- Or go to **Resource → Manage added data sources → Edit** and add fields there

### Common "DAX-like" patterns and how to do them

#### A) Basic arithmetic

Examples:
- `Points per million`:

```text
points / price
```

- `% owned as fraction` (if stored as a percent number like `27`):

```text
percentOwned / 100
```

#### B) Conditional logic (IF/CASE)

Bucket a driver into price tiers:

```text
CASE
  WHEN price < 6 THEN "Budget"
  WHEN price < 12 THEN "Mid"
  ELSE "Premium"
END
```

#### C) Safe division (avoid divide-by-zero)

```text
CASE WHEN price = 0 OR price IS NULL THEN NULL ELSE points / price END
```

#### D) Text concatenation (labels)

```text
CONCAT(driver_givenName, " ", driver_familyName)
```

#### E) "Latest round" values (important difference vs DAX)

Power BI/DAX often does "latest value" with filter context.
In Looker Studio with CSV/Sheets sources, the simplest approach is:

- Add a **Round** control and let users choose the round, **or**
- Precompute “latest round per season” in the data (recommended).

If you want an always-latest view without manual round selection, the best way is a **BigQuery view** that filters to `MAX(round)` per `season`.

#### F) Running totals / cumulative sums

Looker Studio supports “Running calculation” for some chart types:
- Time series / scorecards can use running sums depending on chart

But for consistent results, precompute cumulative totals in BigQuery (or in your pipeline) and export as a column.

### When calculated fields won’t be enough

Looker Studio blends + calculated fields can get limiting for:
- complex "filter context" measures
- measures that need a dynamic "latest round" per season
- many-to-many joins

For those, create a **prepared table/view** (ideally in BigQuery) that already contains the metrics you need (e.g. `points_last_round`, `price_change_last_round`, `value_score`, etc.).

---

## 7) Joining tables (Looker Studio “Blend Data”)

Looker Studio doesn’t do a full semantic model like Power BI. For joins you typically use **Blend data**.

Common join keys in this repo:

- Official standings / points tables:
  - Join on `season` + `round` + `ergast_driver_id` (or `constructorCode` depending on table)
- f1fantasytools tables:
  - Join on `season` + `round` + `id`

Steps:
1. Select a chart → **Data** panel → **Blend data**
2. Add the second data source
3. Choose the join keys
4. Add the fields you need from each side

Tip: if blends get slow or annoying, move joins into BigQuery views.

---

## 7) Publish / share

- To share privately: use Looker Studio sharing permissions.
- To share publicly: **File → Report settings / Share → Manage access** and enable link sharing / public (depends on your Google Workspace settings).
- To embed in SquareSpace: use the **Embed report** iframe.

---

## 8) Keeping it updated

If you update CSVs in `mycsv/` and commit/push:
- the raw GitHub URL updates immediately
- Google Sheets `IMPORTDATA()` will refresh on Google’s schedule (not instant)

If you need scheduled/guaranteed refresh:
- load into BigQuery and use scheduled queries / refresh cadence you control.
