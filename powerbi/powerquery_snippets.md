# Power Query snippets (M)

These are copy/paste helpers you can use in **Power BI Desktop**.

## 1) Replace `$undefined` → null

Select the column(s) that contain `$undefined`, then use **Transform → Replace Values**.
If you prefer M directly:

```powerquery
= Table.ReplaceValue(
    PreviousStep,
    "$undefined",
    null,
    Replacer.ReplaceValue,
    {"x2PercentOwned", "percentOwned"}
)
```

(Adjust the column list to match your table.)

## 2) Add `season_round` key to a fact table

```powerquery
= Table.AddColumn(
    PreviousStep,
    "season_round",
    each Text.From([season]) & "-R" & Text.PadStart(Text.From([round]), 2, "0"),
    type text
)
```

## 3) Convert column types (recommended)

Example for the **driver prices** fact table:

```powerquery
= Table.TransformColumnTypes(
    PreviousStep,
    {
        {"season", Int64.Type},
        {"round", Int64.Type},
        {"id", type text},
        {"abbr", type text},
        {"price", type number},
        {"priceChange", type number},
        {"percentOwned", type number},
        {"x2PercentOwned", type number},
        {"season_round", type text}
    }
)
```

Example for the **driver points** fact table:

```powerquery
= Table.TransformColumnTypes(
    PreviousStep,
    {
        {"season", Int64.Type},
        {"round", Int64.Type},
        {"id", type text},
        {"abbr", type text},
        {"totalPoints", type number},
        {"nnTotalPoints", type number},
        {"season_round", type text}
    }
)
```

## 4) Merge race dates into DimRound

Assumes:
- `DimRound` has `season` and `round`
- `dim_round_dates` has `season` and `round` and `raceDate`

```powerquery
let
    Source = DimRound,
    Merged = Table.NestedJoin(
        Source,
        {"season", "round"},
        dim_round_dates,
        {"season", "round"},
        "Race",
        JoinKind.LeftOuter
    ),
    Expanded = Table.ExpandTableColumn(
        Merged,
        "Race",
        {"raceName", "circuitName", "locality", "country", "raceDate", "raceTime"},
        {"raceName", "circuitName", "locality", "country", "raceDate", "raceTime"}
    ),
    Typed = Table.TransformColumnTypes(
        Expanded,
        {
            {"raceDate", type date},
            {"raceTime", type text}
        }
    )
in
    Typed
```

## 5) Relationship checklist

After transformations:
- `DimRound[season_round]` (text) → each Fact’s `[season_round]` (text)
- `DimDriver[driver_id]` (text) → Driver facts `[id]` (text)
- `DimConstructor[constructor_id]` (text) → Constructor facts `[id]` (text)

Cross filter: **single direction** (Dim → Fact).
