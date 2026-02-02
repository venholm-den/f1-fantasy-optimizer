# DAX measures (starter)

> Adjust table names to match your Power BI query names.

## Where should these measures live?

In Power BI, a **measure can technically live in any table** — the result is the same.

For sanity (and to make it easy to find things), create a dedicated table called something like **`Measures`** and put *all* measures there.

Recommended layout:
- **Measures** (disconnected table; no relationships)
  - Base measures (Totals, Averages)
  - Derived measures (rolling, ratios)
  - Visual-helper measures (colours, labels, tooltips)

How to create it:
- Home → **Enter data** → create a 1-column table with a single row (e.g. column `Name`, value `Measures`), then name the table **Measures**.
- Then for each measure: right-click the measure → **Home table** → set to **Measures**.

If you prefer grouping by subject instead, a second-best approach is:
- Put driver measures in `DimDriver`
- Constructor measures in `DimConstructor`
- Round/season measures in `DimRound` / `DimSeason`

But the dedicated **Measures** table is usually the cleanest.


## Base

### Total Driver Points
```DAX
Total Driver Points = SUM ( FactDriverPoints[totalPoints] )
```

### Total Constructor Points
```DAX
Total Constructor Points = SUM ( FactConstructorPoints[totalPoints] )
```

### Avg Driver Price
```DAX
Avg Driver Price = AVERAGE ( FactDriverPrices[price] )
```

### Avg Constructor Price
```DAX
Avg Constructor Price = AVERAGE ( FactConstructorPrices[price] )
```

## Value proxies

### Points per Price (Driver)
```DAX
Driver Points per Price =
DIVIDE ( [Total Driver Points], SUM ( FactDriverPrices[price] ) )
```

### Rolling 3-round driver points
```DAX
Driver Points (Rolling 3) =
VAR CurrentRound = MAX ( DimRound[round] )
RETURN
CALCULATE (
    [Total Driver Points],
    FILTER ( ALL ( DimRound ), DimRound[round] >= CurrentRound - 2 && DimRound[round] <= CurrentRound )
)
```

## Scatter: colour points above/below trendline

Power BI’s built-in scatter **Trend line** is visual-only, so to colour points you need to recreate the trendline math in DAX and then return a colour.

Assumptions (adjust names to match your model):
- Scatter **X** = `[Avg Driver Price]`
- Scatter **Y** = `[Total Driver Points]`
- Each dot is a driver (use `DimDriver[driver_id]` in **Details**, not Values — scatter doesn’t use a Values bucket).

### Driver trendline slope (manual; avoids LINESTX column-name issues)
```DAX
Driver Trendline Slope =
VAR PointsByDriver =
    FILTER (
        ADDCOLUMNS (
            ALLSELECTED ( DimDriver[driver_id] ),
            "x", [Avg Driver Price],
            "y", [Total Driver Points]
        ),
        NOT ISBLANK ( [x] ) && NOT ISBLANK ( [y] )
    )
VAR n = COUNTROWS ( PointsByDriver )
VAR sumX = SUMX ( PointsByDriver, [x] )
VAR sumY = SUMX ( PointsByDriver, [y] )
VAR sumXY = SUMX ( PointsByDriver, [x] * [y] )
VAR sumX2 = SUMX ( PointsByDriver, [x] * [x] )
VAR denom = n * sumX2 - sumX * sumX
RETURN
    DIVIDE ( n * sumXY - sumX * sumY, denom )
```

### Driver trendline intercept (manual)
```DAX
Driver Trendline Intercept =
VAR PointsByDriver =
    FILTER (
        ADDCOLUMNS (
            ALLSELECTED ( DimDriver[driver_id] ),
            "x", [Avg Driver Price],
            "y", [Total Driver Points]
        ),
        NOT ISBLANK ( [x] ) && NOT ISBLANK ( [y] )
    )
VAR n = COUNTROWS ( PointsByDriver )
VAR xBar = DIVIDE ( SUMX ( PointsByDriver, [x] ), n )
VAR yBar = DIVIDE ( SUMX ( PointsByDriver, [y] ), n )
RETURN
    yBar - [Driver Trendline Slope] * xBar
```

### Predicted Y on the trendline (at the current point’s X)
```DAX
Driver Trendline Y =
VAR x = [Avg Driver Price]
RETURN
    [Driver Trendline Slope] * x + [Driver Trendline Intercept]
```

### Colour for conditional formatting
Use this measure in the scatter visual’s **Data colors → fx → Format by: Field value**.

```DAX
Driver Trendline Colour =
VAR y = [Total Driver Points]
VAR yHat = [Driver Trendline Y]
RETURN
    IF ( y >= yHat, "#2E7D32", "#C62828" )
```

Notes:
- This respects the current report filters because it uses `ALLSELECTED`.
- This version uses the closed-form regression formula (covariance/variance) and avoids `LINESTX` entirely.
- If your scatter dots are not at `DimDriver[driver_id]` grain, swap `ALLSELECTED ( DimDriver[driver_id] )` for whatever field is in the scatter **Details** bucket.
- You can duplicate these measures for constructors by swapping `DimDriver`/driver facts for constructor equivalents.

