# Public report (GitHub Pages)

This folder contains a **free, publicly accessible** report hosted via **GitHub Pages**.

It is intentionally simple:
- no backend
- no auth
- loads CSV files from the repo's `mycsv/` folder via `raw.githubusercontent.com`

## 1) Data source

This public report reads CSVs directly from:

- `mycsv/` (in the repo)

so updates are as simple as committing new CSVs to `mycsv/`.

No additional export step is required for the website.

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
- If you add more seasons, add them to the season dropdown in `docs/index.html`.
- Everything in `docs/` is public.
- Everything in `mycsv/` is also public (since it’s in a public GitHub repo).
