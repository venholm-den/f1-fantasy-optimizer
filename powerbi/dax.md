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
