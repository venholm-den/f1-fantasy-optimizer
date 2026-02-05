# Public report (GitHub Pages)

This folder contains a **free, publicly accessible** report hosted via **GitHub Pages**.

It is intentionally simple:
- no backend
- no auth
- loads CSV files from `docs/data/<season>/...`

## 1) Export data into `docs/`

After you update your season data (e.g. after running your scrape/points scripts), run:

```bash
node scripts/export_public_report.mjs --season 2025
```

(There’s also a Python version at `scripts/export_public_report.py` if you prefer.)

That copies selected CSVs from:
- `data/seasons/2025/raw/`

into:
- `docs/data/2025/`

Commit the changed files:

```bash
git add docs/data/2025/*.csv
git commit -m "Update public report data (2025)"
git push
```

## 2) Enable GitHub Pages

On GitHub:
1. Repo → **Settings** → **Pages**
2. **Build and deployment**
3. Source: **Deploy from a branch**
4. Branch: `main` (or `master`) and folder: **`/docs`**
5. Save

GitHub will give you a public URL like:

`https://<username>.github.io/<repo>/`

## 3) View the report

Open the Pages URL. The entrypoint is:
- `docs/index.html`

## Notes
- If you add more seasons, export them the same way and add options in `docs/index.html`.
- Everything in `docs/` is public.
