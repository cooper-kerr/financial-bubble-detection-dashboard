# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A single-page Vite + React + TypeScript dashboard that visualizes precomputed financial bubble estimates. The app fetches JSON from Vercel Blob and renders four Plotly charts (three bubble charts: put / call / combined; one adjusted-vs-raw price chart). The actual statistics happen offline in Python scripts run by a nightly GitHub Action — the browser never executes estimation code.

Treat this as an app repo with an attached data-generation pipeline, not a reusable library or backend service.

## Commands

Package manager: **Bun**. Some helper scripts (`tsx scripts/...`) are also runnable with `bun run scripts/<file>.ts`.

```bash
bun install                # install deps
bun run dev                # dev server on :3000 (alias: bun run start)
bun run build              # vite build && tsc — production build
bun run serve              # preview production build
bun run test               # vitest run (NOTE: no test files exist yet)
bun run lint               # biome lint
bun run format             # biome format
bun run check              # biome check (lint + format)

# Blob helpers (require BLOB_READ_WRITE_TOKEN in .env.local)
bun run upload-data        # upload public/data/*.json to Blob (older bulk helper)
bun run get-blob-urls      # legacy URL retrieval — likely stale, see "Known stale" below
bun run test-blob          # connectivity check
bun run scripts/update-blob-urls.ts   # current incremental upload + mapping (used by CI)
```

To run a single Vitest file once tests exist: `bun run test path/to/file.test.ts`.

Python scripts (run from repo root, require `pandas numpy yfinance scipy fredapi matplotlib requests`):

```bash
python scripts/yf_data_scraper.py      # scrape Yahoo + FRED → CSVs → upload to Blob
python scripts/sbub_run.py             # CSV → .mat bubble estimation
python scripts/bubble_estimator.py     # .mat → public/data/*.json + plot images
python scripts/reconcile_blob_csvs.py  # diff local vs Blob CSVs (writes blob_csv_reconciliation.{json,csv})
```

## Architecture

### Two data sources, two loading paths

The dashboard has a `DataSource` toggle (`WRDS` | `Yahoo Finance`) that completely changes how data is fetched. **This is the most important thing to understand before touching `src/utils/dataLoader.ts`.**

- **WRDS (1996–2023, static)**: blob URLs are hardcoded in `WRDS_BLOB_URLS` and `REGULAR_PRICE_URLS` in `src/utils/dataLoader.ts`. These never change.
- **Yahoo Finance (2025–present, daily)**: blob URLs are looked up at runtime from `blob_mapping.json` hosted in Blob (`BLOB_MAPPING_URL`). The mapping is regenerated each night by `scripts/update-blob-urls.ts`. Cached in-memory per page load (`yahooUrlCache`).

Do **not** hardcode Yahoo URLs in `dataLoader.ts` — the nightly job overwrites the mapping, and stale URLs will break the app.

### App runtime (frontend)

1. `src/main.tsx` boots TanStack Router with one route → `Dashboard`.
2. `src/components/Dashboard.tsx` delegates state to `useDashboardData` and renders controls + 4 charts.
3. `src/hooks/useDashboardData.ts` owns selected ticker, source, date range, and triggers parallel fetches of bubble JSON + regular-price JSON.
4. `src/utils/dataLoader.ts` is the runtime data boundary — it picks WRDS-vs-Yahoo, fetches, and transforms via `transformDataForChart` and `calculatePriceDifferences`.
5. `src/types/bubbleData.ts` defines the JSON contract and the canonical `STOCK_LIST` driving the ticker dropdown.

### Offline pipeline (GitHub Actions, `.github/workflows/main.yml`)

Two sequential jobs run nightly at 20:59 UTC:

1. **`update-csvs`** → `scripts/yf_data_scraper.py` scrapes Yahoo prices, FRED 1-mo Treasury, and option chains; uploads CSVs to Blob; uploads them as workflow artifacts.
2. **`generate-mat-json`** → downloads CSV artifacts, runs `sbub_run.py` (CSV → `.mat` via `sbub_lp_easy` + `sbub_split`), then `bubble_estimator.py` (`.mat` → `public/data/*.json`), then `update-blob-urls.ts` to upload changed JSONs and regenerate `blob_mapping.json`. Triggers a Vercel redeploy hook **only if blob content changed**.

`update-blob-urls.ts` keeps a `blob_hash_manifest.json` of SHA-256s in Blob to skip uploads when JSON content is unchanged. Filenames follow `bubble_data_<STOCK>_splitadj_<years>.json` and the script extracts the stock code via regex — preserve that filename pattern.

`sbub_run.py` prefers local CSV artifacts and falls back to Blob, which lets you run it standalone without re-scraping.

## Data quirks worth knowing

- **META → TWTR filename**: historical WRDS files for META are stored as `bubble_data_TWTR_*` and `TWTR_data.json`. The mapping in `dataLoader.ts` (`META: ".../TWTR_..."`) is intentional, not a bug. README still references `TWTR` in places — the UI uses `META`.
- **`public/data/*.json`** are generated outputs. The deployed app does **not** read them — it reads from Blob. Editing them locally has no production effect unless you also upload to Blob.
- **`blob_mapping.json`** at the repo root is a local debugging copy written by `update-blob-urls.ts`. The runtime mapping lives in Blob.
- **`src/routeTree.gen.ts`** is auto-generated by the TanStack Router Vite plugin. Never edit by hand; Biome already ignores it.
- **`src/components/BubbleChart.tsx`** is an unused ECharts implementation; the live charts use `PlotlyBubbleChart.tsx`.

## Tooling notes

- **Biome** (`biome.json`) handles lint + format. Tab indent, double quotes. Only scans `src/*`, `.vscode/*`, `index.html`, `vite.config.js`. Run `bun run check` before committing.
- **Vite alias**: `@` → `./src` (`vite.config.ts`).
- **Vitest** is configured (`environment: 'jsdom'`, `globals: true`) but there are no test files — any refactor is effectively untested.
- **Env vars**: `BLOB_READ_WRITE_TOKEN`, `BLOB_BASE_URL` (Blob upload base, e.g. the public domain of the store), `FRED_API_KEY` (Python scrape only). Loaded from `.env.local` locally; from GitHub secrets in CI.

## Known stale / drifted

- `BLOB_SETUP.md` describes a "fallback to local files" path and a manual `BLOB_URLS` edit workflow that no longer exist in `dataLoader.ts`. Trust code over docs for blob mechanics.
- `scripts/get-blob-urls.ts` and `scripts/upload-to-blob.ts` predate `update-blob-urls.ts` and the hash-manifest incremental flow; the CI uses `update-blob-urls.ts`.
- `data/csv/migrate_csvs_to_blob.py` is empty; `migrate_csvs_to_blob.ts` at repo root is the working CSV migration helper.
- README references a `docs/` directory that does not exist.

## When making changes

- UI/product changes: start in `src/components/Dashboard.tsx`, `DashboardControls.tsx`, `PlotlyBubbleChart.tsx`, `PriceDifferenceChart.tsx`.
- Data-loading behavior: `src/hooks/useDashboardData.ts`, `src/utils/dataLoader.ts`, `src/types/bubbleData.ts`.
- Pipeline changes: validate against `.github/workflows/main.yml` — it's the most reliable description of the actual production data path.
- Adding a ticker: update `STOCK_LIST` in `src/types/bubbleData.ts`, add entries to both `WRDS_BLOB_URLS` and `REGULAR_PRICE_URLS` (if WRDS history exists), and add to `stockcodelist` in `scripts/sbub_run.py` for Yahoo updates.
