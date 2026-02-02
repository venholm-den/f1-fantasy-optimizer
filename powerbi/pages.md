# Power BI page plan

This is a suggested report layout for **Power BI Desktop (Windows)**.
It assumes you imported the CSVs in `data/seasons/<season>/raw/` (available: 2023, 2024, 2025) and created relationships
as described in `powerbi/README.md`.

Note: the fact tables use **f1fantasytools IDs** (`Fact*.[id]`), and the dims are built from them (`DimDriver[driver_id]`, `DimConstructor[constructor_id]`).

> Tip: Build **measures once**, then reuse across pages.

## Page 0 — Cover / Start Here

Goal: a simple landing page so people instantly understand what the report is, what data it uses, and how to use the filters.

### Suggested layout

**Header**
- Title: `F1 Fantasy Optimiser` (or whatever you want to call it)
- Subtitle: season + round context (based on slicers)

**Info cards (left column)**
- **Data source:** f1fantasytools exports (drivers/constructors prices + points)
- **Scoring:** `totalPoints` = normal; `nnTotalPoints` = No Negative chip variant
- **Update cadence:** manual refresh (unless you wire a pipeline)

**How to use (center column)**
- 1) Pick **Season**
- 2) Pick **Round** (if applicable)
- 3) Use Driver/Constructor search to filter visuals
- 4) Hover points/bars for tooltips (price change, ownership, etc.)

**Disclaimers (bottom)**
- Not affiliated with F1 / F1 Fantasy
- For analysis only; not financial advice / not guaranteed outcomes

### Recommended fields to show dynamically
- `Selected Season` (measure or card)
- `Selected Round` (measure or card)
- `Last refresh` (optional: Power Query parameter / manual text)

### Optional: navigation buttons
- Buttons to jump to:
  - Round dashboard
  - Driver profile
  - Constructor profile
  - Value & movers

---

## Page 1 — Round dashboard (round-centric)

### Slicers
- Season
- Round (`DimRound[season_round]`)
- Optional: Driver search (`DimDriver[abbr]`) / Constructor search (`DimConstructor[abbr]`)

### KPI cards
- Avg Driver Price: `[Avg Driver Price]`
- Total Driver Points: `[Total Driver Points]`
- Avg Constructor Price: `[Avg Constructor Price]`
- Total Constructor Points: `[Total Constructor Points]`

### Visuals
- Bar (Top 10): Driver totalPoints for selected round
  - Axis: `DimDriver[abbr]`
  - Values: `[Total Driver Points]`
  - Filter: Top N = 10

- Bar (Top 10): Driver priceChange for selected round
  - Axis: `DimDriver[abbr]`
  - Values: `SUM(FactDriverPrices[priceChange])`
  - Filter: Top N = 10

- Scatter: Price vs Points (drivers)
  - Details: `DimDriver[abbr]`
  - X: `SUM(FactDriverPrices[price])`
  - Y: `[Total Driver Points]`
  - Tooltip: priceChange, percentOwned

- Table: Drivers (selected round)
  - Columns: abbr, price, priceChange, totalPoints, nnTotalPoints, percentOwned

- Table: Constructors (selected round)
  - Columns: abbr, price, priceChange, totalPoints, nnTotalPoints, percentOwned

## Tooltip — Driver year-over-year (YoY) comparison

Create a **tooltip page** that shows “this driver across seasons” at a glance.

### Setup (Power BI)
- New page → Page information → **Tooltip = On**
- Canvas settings → **Page size = Tooltip**
- Keep it compact: 320×240-ish (default tooltip size)

### Required model assumptions
- You have multiple seasons loaded (e.g. 2023–2025)
- Driver identity is consistent across seasons via `DimDriver[driver_id]`

### Visuals to include

**Header**
- Driver: `SELECTEDVALUE(DimDriver[abbr])` (as a card)

**Mini chart: Points by season**
- Visual: clustered column
- Axis: `DimSeason[season]` (or your season field)
- Values:
  - `SUM(FactDriverPoints[totalPoints])`
  - Optional: `SUM(FactDriverPoints[nnTotalPoints])` (as a second series)

**Mini chart: Avg price by season**
- Visual: line or clustered column
- Axis: season
- Values: `AVERAGE(FactDriverPrices[price])`

**Quick stats (cards)**
- Best season points
- Worst season points
- Avg points/round (current filter)

### How to wire it to the main pages
On your driver scatter/bar/table visuals:
- Visual → Format → **Tooltip** → Type: *Report page* → select this tooltip page.

Tip: keep the tooltip filtered to the hovered driver only. Avoid extra slicers on the tooltip page.

---

## Page 2 — Driver profile (driver-centric)

### Slicers
- Season
- Driver (`DimDriver[abbr]` single-select)

### Visuals
- Line: Driver price by round
  - X: `DimRound[round]`
  - Y: `AVERAGE(FactDriverPrices[price])`

- Line: Driver totalPoints by round
  - X: `DimRound[round]`
  - Y: `SUM(FactDriverPoints[totalPoints])`

- Line: totalPoints vs nnTotalPoints
  - X: `DimRound[round]`
  - Y1: `SUM(FactDriverPoints[totalPoints])`
  - Y2: `SUM(FactDriverPoints[nnTotalPoints])`

- Cards
  - Season total points: `[Total Driver Points]`
  - Avg points/round: `DIVIDE([Total Driver Points], DISTINCTCOUNT(DimRound[round]))`
  - Price delta (start→end): see measure below

## Page 3 — Constructor profile

### Slicers
- Season
- Constructor (`DimConstructor[abbr]` single-select)

### Visuals
- Line: Constructor price by round
- Line: Constructor totalPoints by round
- Line: totalPoints vs nnTotalPoints
- Cards: season totals, avg points/round

## Page 4 — Value & movers (season-wide)

### Slicers
- Season

### Visuals
- Scatter: season points vs avg price (drivers)
- Bar: biggest risers/fallers (sum of priceChange)
- Heatmap (matrix): abbr x round (values = points or price)

## Page 5 — Optimizer outputs (future)

Once the optimizer is implemented and writes to `data/seasons/<season>/derived/`:
- Table: recommended team per round
- Cards: expected vs actual
- Chip suggestions over time

## Useful measures

### Price delta (Driver) start→end
```DAX
Driver Price Delta =
VAR FirstRound = MIN ( DimRound[round] )
VAR LastRound = MAX ( DimRound[round] )
VAR P0 = CALCULATE ( AVERAGE ( FactDriverPrices[price] ), FILTER ( ALL ( DimRound ), DimRound[round] = FirstRound ) )
VAR P1 = CALCULATE ( AVERAGE ( FactDriverPrices[price] ), FILTER ( ALL ( DimRound ), DimRound[round] = LastRound ) )
RETURN
P1 - P0
```

### Price delta (Constructor) start→end
```DAX
Constructor Price Delta =
VAR FirstRound = MIN ( DimRound[round] )
VAR LastRound = MAX ( DimRound[round] )
VAR P0 = CALCULATE ( AVERAGE ( FactConstructorPrices[price] ), FILTER ( ALL ( DimRound ), DimRound[round] = FirstRound ) )
VAR P1 = CALCULATE ( AVERAGE ( FactConstructorPrices[price] ), FILTER ( ALL ( DimRound ), DimRound[round] = LastRound ) )
RETURN
P1 - P0
```

### Driver value proxy (points per avg price)
```DAX
Driver Value Proxy =
DIVIDE ( [Total Driver Points], AVERAGE ( FactDriverPrices[price] ) )
```

### Round points (driver)
```DAX
Driver Round Points = SUM ( FactDriverPoints[totalPoints] )
```

### Round price (driver)
```DAX
Driver Round Price = AVERAGE ( FactDriverPrices[price] )
```
