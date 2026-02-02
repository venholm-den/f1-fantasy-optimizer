# DAX measures (starter)

> Adjust table names to match your Power BI query names.

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
- Details/Legend is at driver level: `DimDriver[driver_id]`

### Driver trendline slope
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
VAR Fit = LINESTX ( PointsByDriver, [y], [x] )
RETURN
    -- Some builds expose the slope column as Fit[Slope1]; others as Fit[Slope].
    COALESCE ( MAXX ( Fit, Fit[Slope1] ), MAXX ( Fit, Fit[Slope] ) )
```

### Driver trendline intercept
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
VAR Fit = LINESTX ( PointsByDriver, [y], [x] )
RETURN
    -- Intercept is usually Fit[Intercept], but some builds return Fit[Intercept1].
    COALESCE ( MAXX ( Fit, Fit[Intercept] ), MAXX ( Fit, Fit[Intercept1] ) )
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
- If you get “column not found” on `Slope1`/`Intercept`, your `LINESTX` output columns are named differently.
  Quick way to inspect: create a **calculated table** temporarily:
  ```DAX
  __TrendlineFit =
  VAR PointsByDriver =
      FILTER (
          ADDCOLUMNS (
              ALL ( DimDriver[driver_id] ),
              "x", [Avg Driver Price],
              "y", [Total Driver Points]
          ),
          NOT ISBLANK ( [x] ) && NOT ISBLANK ( [y] )
      )
  RETURN LINESTX ( PointsByDriver, [y], [x] )
  ```
  Then look at the table columns in Data view (or in DAX Studio `EVALUATE __TrendlineFit`).
- You can duplicate these measures for constructors by swapping `DimDriver`/driver facts for constructor equivalents.

