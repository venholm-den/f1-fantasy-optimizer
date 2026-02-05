# Looker Studio (Google Data Studio) setup

This repo produces **CSV files** (including a public set under `mycsv/`). You can use those CSVs as a data source for **Looker Studio**.

There are two practical approaches:

- **A) Google Sheets (recommended for simplicity)**: use `IMPORTDATA()` to pull the CSV from GitHub → connect Looker Studio to the Sheet.
- **B) BigQuery (recommended for scale/refresh control)**: load the CSVs into BigQuery → connect Looker Studio to BigQuery.

---

## Where the CSVs live

Public website/report CSVs are in:

- `mycsv/` (in this repo)

When the repo is public, these files are publicly readable via GitHub’s “raw” URLs.

Typical raw URL format:

```text
https://raw.githubusercontent.com/<owner>/<repo>/<branch>/mycsv/<file>.csv
```

Example:

```text
https://raw.githubusercontent.com/venholm-den/f1-fantasy-optimizer/main/mycsv/<file>.csv
```

---

## A) Connect Looker Studio via Google Sheets (IMPORTDATA)

This is the easiest “no backend” approach.

### Step 1 — Create a Google Sheet that mirrors a CSV

1. Create a new Google Sheet.
2. In cell `A1`, enter:

```gs
=IMPORTDATA("https://raw.githubusercontent.com/venholm-den/f1-fantasy-optimizer/main/mycsv/<file>.csv")
```

3. Give the sheet tab a helpful name (e.g. `prices_long`).

Notes:
- `IMPORTDATA()` works best when the CSV is not huge.
- Google Sheets will periodically refresh imported data. If you need a guaranteed refresh cadence, consider BigQuery.

### Step 2 — Connect Looker Studio to the Sheet

1. Open **Looker Studio** → **Create** → **Data source**.
2. Choose **Google Sheets**.
3. Select your spreadsheet and the tab you created.
4. Turn on **“Use first row as headers”**.
5. Check field types (numbers sometimes come in as text on first import).

### Step 3 — Build your report

Create a new report and add charts using the connected data source.

### Adding multiple CSVs

Repeat Step 1 for each CSV (either separate tabs in one spreadsheet, or separate spreadsheets). In Looker Studio, create a separate data source per tab.

---

## B) Connect Looker Studio via BigQuery (more robust)

Use this if:
- the CSVs are large,
- you need predictable refresh,
- you want joins/modeling in SQL,
- you want to blend multiple sources cleanly.

High-level flow:

1. Create a BigQuery dataset (e.g. `f1_fantasy`).
2. Load CSV(s) from:
   - direct upload, **or**
   - Google Cloud Storage, **or**
   - a scheduled pipeline you control.
3. Create tables/views with the schema you want.
4. In Looker Studio: **Create → Data source → BigQuery**.

---

## Tips / gotchas

- **Stable column names matter**: Looker Studio is happiest when CSV headers don’t change.
- **Date fields**: if you have a `date`/`timestamp` column, make sure it parses as a Date in the data source.
- **IDs and joins**: this repo often uses **f1fantasytools IDs** (e.g. `AST_ALO`, `RED`). Keep those as keys consistently across tables.

---

## Quick checklist

- [ ] CSVs exist in `mycsv/`
- [ ] CSV raw URL works in an incognito browser
- [ ] Google Sheet imports via `IMPORTDATA()`
- [ ] Looker Studio data source uses first row as headers
- [ ] Field types look correct (numbers/dates)
