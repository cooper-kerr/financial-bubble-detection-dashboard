# CSV Data Display Investigation Report

Investigation date: 2026-06-25 local workspace time

## Executive Summary

The CSV files in `data/csv/` are not displayed or calculated directly by the deployed Vercel website because the frontend never reads those files. The deployed app reads precomputed JSON from Vercel Blob. CSV files are only inputs to the offline GitHub Actions pipeline that generates MAT files, converts them to dashboard JSON, uploads that JSON to Blob, and then optionally triggers a Vercel redeploy.

The immediate production blocker is that Yahoo Finance data loading is pointed at the wrong Blob store. `src/utils/dataLoader.ts` fetches `blob_mapping.json` from the WRDS Blob store, where that file does not exist. The live Yahoo assets do exist in a different Blob store.

There is also a separate calculation issue for the price comparison chart: even after Yahoo bubble JSON loads, `loadRegularPriceData()` still fetches WRDS-era regular-price JSON ending in 2023, while the Yahoo bubble series starts in 2026. Because `calculatePriceDifferences()` only emits rows for matching dates, the Yahoo price comparison chart will be empty.

## How Data Is Supposed To Flow

The app is not a browser-side CSV calculator.

1. `scripts/yf_data_scraper.py` scrapes current Yahoo/FRED/options data and writes CSVs to `data/csv/`.
2. `.github/workflows/main.yml` uploads those CSVs as workflow artifacts.
3. `scripts/sbub_run.py` consumes the CSV artifacts and writes MAT files.
4. `scripts/bubble_estimator.py` converts MAT files into `public/data/bubble_data_*_splitadj_*.json`.
5. `scripts/update-blob-urls.ts` uploads those JSON files to Vercel Blob and updates `blob_mapping.json`.
6. The deployed React app fetches Blob JSON, not repo CSVs.

Relevant code:

- `.github/workflows/main.yml:28-39` runs the CSV scraper and uploads CSV artifacts.
- `.github/workflows/main.yml:61-79` downloads CSV artifacts, runs MAT generation, and converts MAT output into JSON.
- `.github/workflows/main.yml:97-109` uploads JSON to Blob and triggers a Vercel redeploy only when Blob JSON changed.
- `src/utils/dataLoader.ts:80-123` fetches the Yahoo `blob_mapping.json` and selects a JSON URL from that mapping.

## Findings

### 1. GitHub CSV files are not web assets

`data/csv/` is outside `public/`, and the frontend has no code that fetches `/data/csv/*.csv`. On Vercel, files outside the static output are not automatically exposed as browser-fetchable assets in this Vite app.

The README currently says `data/csv/` holds local YF CSV copies, which matches the code. It does not mean the deployed browser reads those files.

Local snapshot check:

- `data/csv/optout_SPX.csv`: 17 unique dates, `26Jan2026` through `19Feb2026`.
- `public/data/bubble_data_SPX_splitadj_2025to2026.json`: 17 points, `2026-01-26` through `2026-02-19`.

So committed CSV/JSON files are local snapshots, not the production source of truth.

### 2. Yahoo runtime mapping points at the wrong Blob store

The app uses this runtime mapping URL:

```ts
const BLOB_MAPPING_URL =
  "https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/blob_mapping.json";
```

Observed live responses:

- `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/blob_mapping.json` returns `404 Blob not found`.
- `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/csv/optout_SPX.csv` returns `404 Blob not found`.
- `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_SPX_splitadj_2025to2026.json` returns `404 Blob not found`.

But the Yahoo assets exist here:

- `https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/blob_mapping.json` returns `200`.
- That mapping contains 25 tickers and maps `SPX`, `AAPL`, and `META` to `bubble_data_*_splitadj_2025to2026.json`.
- `https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/bubble_data_SPX_splitadj_2025to2026.json` returns `200`.
- `https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/csv/optout_SPX.csv` returns `200`.

Impact: selecting `Yahoo Finance` in the deployed app fails before chart data can render, because the first fetch for `blob_mapping.json` returns 404.

### 3. WRDS data is on the old Blob store and still responds

The same `kpjvwsj...` store does still host the WRDS assets:

- `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/bubble_data_SPX_splitadj_1996to2023.json` returns `200`.
- `https://kpjvwsjhhmtk0pdx.public.blob.vercel-storage.com/SPX_data.json` returns `200`.

That explains why the default WRDS view can work while Yahoo data does not.

### 4. Price comparison calculation is mismatched for Yahoo

`useDashboardData()` always loads `loadRegularPriceData(state.selectedStock)` alongside the selected bubble source. It does not pass the data source into the regular-price loader.

`loadRegularPriceData()` uses `REGULAR_PRICE_URLS`, which are hardcoded to the WRDS Blob store. For SPX, that regular-price JSON contains dates from `1996-01-04` through `2023-08-31`.

Yahoo bubble JSON dates are in 2026. `calculatePriceDifferences()` builds a map of regular prices by date and only pushes rows when a bubble date is present in that map. With 2026 Yahoo bubble dates and 1996-2023 regular price dates, there are no matches.

Impact: after the Yahoo Blob mapping is fixed, the three bubble charts should be able to render, but the price comparison chart will still show "No price difference data available" unless Yahoo-period regular/raw price data is provided or the calculation uses data already embedded in the Yahoo output.

Relevant code:

- `src/hooks/useDashboardData.ts:55-58`
- `src/utils/dataLoader.ts:46-73`
- `src/utils/dataLoader.ts:232-280`
- `src/utils/dataLoader.ts:283-326`
- `src/components/PriceDifferenceChart.tsx:21-24` and `src/components/PriceDifferenceChart.tsx:173-180`

### 5. Checked-in `blob_mapping.json` is stale and misleading

The repo root `blob_mapping.json` points at `https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/*_data.json`, not the live `bubble_data_*_splitadj_2025to2026.json` mapping used by the current Yahoo pipeline.

Example from the checked-in file:

```json
"SPX": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/SPX_data.json"
```

But the live `fposl6.../blob_mapping.json` maps:

```json
"SPX": "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/bubble_data_SPX_splitadj_2025to2026.json"
```

Impact: local debugging from the checked-in mapping file can lead to the wrong conclusion. The runtime mapping lives in Blob.

### 6. Live Yahoo CSV and JSON are not fully consistent

The live `fposl6.../csv/optout_SPX.csv` has 25 unique dates ending `03Mar2026`.

The live `fposl6.../bubble_data_SPX_splitadj_2025to2026.json` has 26 dates:

- `2026-01-26` through `2026-03-03`
- plus `2026-05-08`

This does not cause the current deployed display failure, but it is a data integrity concern. The generated JSON appears to contain a point not present in the live SPX CSV checked during this investigation.

## Root Cause

Primary root cause:

The deployed frontend is configured to fetch Yahoo `blob_mapping.json` from the WRDS Blob store (`kpjvwsj...`), but the Yahoo mapping and Yahoo CSV/JSON assets live in the Yahoo Blob store (`fposl6...`). The mapping fetch returns 404, so Yahoo bubble data never reaches the React charts.

Secondary root cause:

The price comparison calculation does not have Yahoo-period regular price data. It always fetches WRDS-era regular price files, so there is no date overlap with Yahoo bubble JSON.

Design clarification:

The GitHub CSV files are not meant to be displayed directly by the deployed app in the current architecture. They must be converted into JSON and uploaded to Blob first.

## Recommended Fixes

### Immediate fix

Update `BLOB_MAPPING_URL` in `src/utils/dataLoader.ts` to the live Yahoo mapping store:

```ts
const BLOB_MAPPING_URL =
  "https://fposl6nafeqvtwpj.public.blob.vercel-storage.com/blob_mapping.json";
```

This should unblock Yahoo bubble chart loading.

### Better fix

Do not hardcode the Yahoo Blob mapping store in source code. Put it behind a Vite environment variable, for example:

```ts
const BLOB_MAPPING_URL = import.meta.env.VITE_YAHOO_BLOB_MAPPING_URL;
```

Then set `VITE_YAHOO_BLOB_MAPPING_URL` in Vercel to the active mapping URL. This prevents future Blob-store migrations from silently breaking production.

### Price comparison fix

Choose one of these:

1. Generate and upload Yahoo-period regular/raw price JSON files, then select regular-price URLs based on `dataSource`.
2. Embed raw and split-adjusted prices directly in the Yahoo bubble JSON and compute the chart from the selected bubble dataset.
3. Hide the price comparison chart for Yahoo until matching raw-price data exists.

The current implementation should not show a blank calculation without explaining that no matching price series is available.

### Pipeline/data integrity fix

Add a CI smoke test after `update-blob-urls.ts` that checks:

- `blob_mapping.json` is reachable at the same URL the frontend uses.
- Every `STOCK_LIST` ticker used by the UI exists in the mapping for Yahoo, excluding intentionally unsupported legacy tickers.
- Each mapped URL returns JSON with `metadata.stockcode` and non-empty `time_series_data`.
- For a sample ticker, the latest generated JSON date is present in the source CSV dates or has an explicitly documented reason not to be.

### Documentation cleanup

Update docs to state clearly:

- `data/csv/` is pipeline input/staging data, not frontend runtime data.
- `public/data/` is generated output, but production runtime uses Blob.
- Root `blob_mapping.json` is only a local debugging copy and should not be treated as production truth.

## Validation Notes

Build validation could not be completed in this workspace because local dependency installation is missing Rollup's optional native package:

```text
Cannot find module @rollup/rollup-darwin-arm64
```

This appears to be npm/Rollup optional-dependency installation behavior in the local environment. Vercel uses `bun install` and `bun run build` per `vercel.json`, so this local build failure should be treated separately from the data-loading findings above.

