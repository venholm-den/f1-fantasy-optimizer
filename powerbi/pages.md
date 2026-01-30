# Power BI page plan

This is a suggested report layout for **Power BI Desktop (Windows)**.
It assumes you imported the CSVs in `data/seasons/2025/raw/` and created relationships
as described in `powerbi/README.md`.

> Tip: Build **measures once**, then reuse across pages.

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

Once the optimizer is implemented and writes to `data/seasons/2025/derived/`:
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
