# Multi-season setup (2023–2025)

You have two valid approaches in Power BI:

## Option A (recommended): one combined model

Create one set of dimension tables and one set of fact tables that include **season**.

### 1) Load each season’s raw tables
For each season folder:
- `data/seasons/2023/raw/*.csv`
- `data/seasons/2024/raw/*.csv`
- `data/seasons/2025/raw/*.csv`

Then **Append Queries** (Power Query) to create combined tables:
- `FactDriverPrices` = append all `f1fantasytools_prices_drivers_long.csv`
- `FactDriverPoints` = append all `f1fantasytools_points_drivers_long.csv`
- `FactConstructorPrices` = append all `f1fantasytools_prices_constructors_long.csv`
- `FactConstructorPoints` = append all `f1fantasytools_points_constructors_long.csv`

For dims:
- `DimRound` = append all `dim_round.csv`
- `DimDriver` = append all `dim_driver.csv` then **Remove Duplicates** on `driver_id`
- `DimConstructor` = append all `dim_constructor.csv` then **Remove Duplicates** on `constructor_id`
- `DimRoundDates` = append all `dim_round_dates.csv`

### 2) Add `season_round` once (facts)
Add the `season_round` column to each *combined* fact table.

### 3) Relationships
- `DimRound[season_round]` → each fact’s `season_round`
- `DimDriver[driver_id]` → driver facts `[id]`
- `DimConstructor[constructor_id]` → constructor facts `[id]`

### 4) Calendar
Merge `DimRoundDates` into `DimRound` on (season, round), expand `raceDate`, then relate `Calendar[Date]` → `DimRound[raceDate]`.

## Option B: separate per-season pages/models

Keep separate tables per season and separate report pages. This is simpler initially but harder to compare across years.

---

Tip: if you want year-over-year comparisons, Option A is much better.
