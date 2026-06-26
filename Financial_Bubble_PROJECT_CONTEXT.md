# PROJECT_CONTEXT

## Project Overview

This repo is a single-page React dashboard for viewing precomputed financial bubble estimates by ticker, option type, and date range. The live app is not a general analytics platform or API; it is a frontend that fetches JSON datasets from Vercel Blob and renders four charts on one page (`src/main.tsx:1`, `src/routes/index.tsx:1`, `src/components/Dashboard.tsx:9`).

The problem it solves is narrow: expose historical WRDS-based bubble series and newer Yahoo-derived bubble series in an interactive UI. The core statistical work does not happen in the browser. It happens offline in Python scripts and a GitHub Actions pipeline (`.github/workflows/main.yml:1`).

Current maturity/status:
- Frontend: implemented, simple, and tightly scoped.
- Data pipeline: implemented, but script quality is uneven and some docs are stale.
- Tests: configured in `package.json`, but no test files are present.

This is best described as an app repo with an attached research/data-generation pipeline, not a reusable library.

## Repo Scope

Inside this repo:
- A Vite + React + TypeScript dashboard app (`src/`, `index.html`, `vite.config.ts`).
- Python scripts that scrape Yahoo Finance/FRED data, run bubble estimation, generate `.mat` files, then export dashboard JSON (`scripts/yf_data_scraper.py:1`, `scripts/sbub_run.py:42`, `scripts/bubble_estimator.py:63`).
- Blob upload/update helpers for JSON and CSV artifacts (`scripts/update-blob-urls.ts:17`, `migrate_csvs_to_blob.ts:1`).
- Checked-in generated data samples under `public/data/` and `data/csv/`.

Not inside this repo:
- No backend service, API server, or database schema.
- No raw WRDS extraction code for the historical 1996-2023 JSONs; the app only references their blob URLs (`src/utils/dataLoader.ts:14`).
- No source for Vercel Blob contents besides the local/generated files and upload scripts.
- No deployment IaC beyond minimal `vercel.json`.

Caveats:
- The frontend depends on external Vercel Blob URLs at runtime; local `public/data/*.json` are not the primary read path for the app (`src/utils/dataLoader.ts:14`, `src/utils/dataLoader.ts:80`, `src/utils/dataLoader.ts:107`).
- Several docs describe behavior that the current code no longer uses, including fallback-to-local-file logic and manual `BLOB_URLS` editing (`BLOB_SETUP.md:44`, `BLOB_SETUP.md:59`).
- Some generated/local artifacts are committed and should be treated as outputs, not hand-edited source.

## Directory Tree

```text
.
├── .github/workflows/main.yml          # nightly Yahoo pipeline + blob upload
├── data/
│   └── csv/                            # local/staged CSV option data per ticker
├── public/
│   ├── data/                           # generated Yahoo JSON outputs checked in
│   └── favicon/logo assets
├── scripts/
│   ├── yf_data_scraper.py              # scrape Yahoo/FRED data into CSVs
│   ├── sbub_run.py                     # CSV -> MAT bubble estimation
│   ├── bubble_estimator.py             # MAT -> JSON + plot images
│   ├── update-blob-urls.ts             # upload JSON outputs + blob_mapping.json
│   ├── upload-to-blob.ts               # older bulk JSON upload helper
│   ├── get-blob-urls.ts                # older mapping/updater script, appears stale
│   └── supporting math scripts         # sbub_lp_easy.py, sbub_split.py, etc.
├── src/
│   ├── components/                     # dashboard UI + charts
│   ├── hooks/useDashboardData.ts       # app state and data loading
│   ├── routes/                         # TanStack Router route files
│   ├── types/bubbleData.ts             # data contracts + ticker list
│   └── utils/dataLoader.ts             # runtime fetch + transform logic
├── BLOB_SETUP.md
├── README.md
├── blob_mapping.json                   # local copy of latest Yahoo blob mapping
├── migrate_csvs_to_blob.ts             # CSV upload helper
├── package.json
├── vercel.json
└── vite.config.ts
```

## Architecture

### App runtime

The browser app boots a TanStack Router instance and renders a single route whose component is `Dashboard` (`src/main.tsx:12`, `src/routes/index.tsx:4`). `Dashboard` delegates all state and data loading to `useDashboardData`, then renders:
- controls
- 3 Plotly bubble charts
- 1 price comparison chart

Source of truth: `src/components/Dashboard.tsx:9`.

### Data flow in the app

1. `useDashboardData` tracks selected ticker, source (`WRDS` or `Yahoo Finance`), and date range (`src/hooks/useDashboardData.ts:19`).
2. On ticker/source change, it loads bubble JSON and regular price JSON in parallel (`src/hooks/useDashboardData.ts:45`).
3. `loadBubbleData` selects either:
   - hardcoded historical WRDS blob URLs, or
   - a Yahoo blob URL looked up from remote `blob_mapping.json`
   (`src/utils/dataLoader.ts:14`, `src/utils/dataLoader.ts:80`, `src/utils/dataLoader.ts:107`).
4. The hook transforms the loaded JSON into chart-friendly series and computes aligned raw-vs-adjusted price comparisons (`src/hooks/useDashboardData.ts:170`, `src/utils/dataLoader.ts:150`, `src/utils/dataLoader.ts:283`).
5. Plotly components render the final charts (`src/components/PlotlyBubbleChart.tsx:1`, `src/components/PriceDifferenceChart.tsx:1`).

### Offline / scheduled data pipeline

The nightly GitHub Action runs two jobs (`.github/workflows/main.yml:8`):

1. `yf_data_scraper.py`
   - pulls historical prices from Yahoo Finance
   - pulls 1-month Treasury data from FRED
   - scrapes option chains up to 365 days out
   - filters/aggregates the options data
   - uploads CSVs to Vercel Blob
   (`scripts/yf_data_scraper.py:128` and surrounding logic)

2. `sbub_run.py` + `bubble_estimator.py`
   - downloads per-ticker CSVs from Blob (`scripts/sbub_run.py:70`)
   - runs `sbub_lp_easy` and `sbub_split` to generate `.mat` outputs (`scripts/sbub_run.py:84`)
   - converts `.mat` results into JSON for the dashboard and also emits plot images (`scripts/bubble_estimator.py:287`, `scripts/bubble_estimator.py:367`, `scripts/bubble_estimator.py:430`)
   - uploads the JSON files and regenerates `blob_mapping.json` (`scripts/update-blob-urls.ts:21`, `.github/workflows/main.yml:80`)

The frontend only consumes the final JSON artifacts; it does not execute any estimation logic itself.

## Key Files

- `package.json`  
  Runtime/tooling entrypoint. Shows the app is Vite-based and that blob helper scripts exist, but there are no app-specific build steps beyond `vite build && tsc` (`package.json:5`).

- `src/main.tsx`  
  Browser entrypoint. Confirms a client-rendered React app with TanStack Router and a theme provider (`src/main.tsx:1`).

- `src/components/Dashboard.tsx`  
  The real UI composition. If a future agent wants to change what the user sees, start here (`src/components/Dashboard.tsx:45`).

- `src/hooks/useDashboardData.ts`  
  State machine for loading, source switching, default date handling, and chart data accessors (`src/hooks/useDashboardData.ts:30`).

- `src/utils/dataLoader.ts`  
  Most important runtime data file. Contains hardcoded WRDS blob URLs, remote Yahoo mapping lookup, JSON parsing assumptions, and price-difference computation (`src/utils/dataLoader.ts:14`, `src/utils/dataLoader.ts:107`, `src/utils/dataLoader.ts:232`).

- `src/types/bubbleData.ts`  
  Defines the JSON contract expected by the frontend and the canonical ticker list shown in the UI (`src/types/bubbleData.ts:30`, `src/types/bubbleData.ts:74`).

- `.github/workflows/main.yml`  
  Canonical description of the automated data-refresh pipeline. More reliable than README prose (`.github/workflows/main.yml:1`).

- `scripts/yf_data_scraper.py`, `scripts/sbub_run.py`, `scripts/bubble_estimator.py`  
  These are the real data-production path for the Yahoo side (`scripts/yf_data_scraper.py:128`, `scripts/sbub_run.py:42`, `scripts/bubble_estimator.py:450`).

- `scripts/update-blob-urls.ts`  
  Current blob update mechanism. Important because it replaced older "edit source code with new URLs" workflows (`scripts/update-blob-urls.ts:62`).

## Core Logic

- `useDashboardData()` in `src/hooks/useDashboardData.ts:30`  
  Owns selected stock/source/date state, triggers data fetches, sets default date ranges, and memoizes transformed chart series.

- `loadBubbleData()` in `src/utils/dataLoader.ts:107`  
  Decides whether to use fixed WRDS blob URLs or the current Yahoo mapping from blob storage. This is the main runtime dependency boundary.

- `transformDataForChart()` in `src/utils/dataLoader.ts:150`  
  Converts raw JSON into three tau-series plus stock price for a given option type.

- `loadRegularPriceData()` in `src/utils/dataLoader.ts:232`  
  Loads raw-price data from separate blob JSON files. It accepts multiple possible shapes, which suggests inconsistent upstream outputs.

- `calculatePriceDifferences()` in `src/utils/dataLoader.ts:283`  
  Aligns bubble-data dates with raw-price dates and builds the dataset for the fourth chart.

- `process_stock()` in `scripts/bubble_estimator.py:63`  
  Reads `.mat` outputs, computes grouped/rolling bubble estimates, writes the JSON shape consumed by the frontend, and saves images.

- `main()` in `scripts/sbub_run.py:42`  
  Drives per-ticker CSV download from Blob and bubble estimation into local `.mat` outputs.

## Technical Stack

- Languages: TypeScript, React JSX/TSX, Python.
- Frontend: React 19, TanStack Router, Plotly, Radix UI, Tailwind CSS v4 (`package.json:18`).
- Build/dev: Vite, TypeScript, Biome, Vitest config present (`package.json:5`, `vite.config.ts:1`, `biome.json:1`).
- Data/storage dependencies:
  - Vercel Blob for runtime JSON and CSV artifacts.
  - Yahoo Finance via `yfinance`.
  - FRED via `fredapi`.
  - NumPy/Pandas/SciPy/Matplotlib for offline processing.
- Hosting/deployment: looks intended for Vercel static hosting with a deploy hook and blob-backed data refresh (`vercel.json:1`, `.github/workflows/main.yml:87`).

## Current Features

Actually implemented in the app:
- Single dashboard page with ticker selector, source selector, start/end date pickers, and theme switcher (`src/components/DashboardControls.tsx:29`).
- Three bubble charts: put, call, combined (`src/components/Dashboard.tsx:61`).
- One adjusted-vs-raw price comparison chart (`src/components/Dashboard.tsx:93`).
- Runtime switching between static WRDS history and newer Yahoo-derived data (`src/hooks/useDashboardData.ts:55`, `src/utils/dataLoader.ts:114`).
- Error state and loading state for data fetches (`src/components/Dashboard.tsx:27`, chart components).

Implemented outside the app:
- Nightly Yahoo/FRED scrape, bubble estimation, JSON generation, blob upload, and redeploy trigger (`.github/workflows/main.yml:3`).

Not evidenced as implemented in the app:
- No separate "recent estimates" dashboard section despite README language (`README.md:44`).
- No local-file fallback path in current runtime loader despite `BLOB_SETUP.md` claims (`BLOB_SETUP.md:59`).
- No tests, no API, no auth, no persistence layer beyond blob-hosted files.

## Known Gaps or Risks

- README and setup docs overstate or misstate current behavior.
  - README mentions a `docs/` directory that is not present (`README.md:143`).
  - README lists `TWTR`, while the code/UI uses `META`; some historical blob mappings still point `META` to `TWTR` filenames (`README.md:169`, `src/types/bubbleData.ts:88`, `src/utils/dataLoader.ts:37`, `src/utils/dataLoader.ts:69`).
  - `BLOB_SETUP.md` describes updating `BLOB_URLS` in source and a fallback strategy that no longer matches `dataLoader.ts` (`BLOB_SETUP.md:44`, `BLOB_SETUP.md:59`).

- The frontend has external hard dependencies on remote blob URLs. If blob contents or mappings are missing, the app fails to load data (`src/utils/dataLoader.ts:94`, `src/utils/dataLoader.ts:124`).

- Some scripts appear stale:
  - `scripts/get-blob-urls.ts` still assumes an older `BLOB_URLS` source-edit workflow and a different filename pattern.
  - `src/components/BubbleChart.tsx` is an unused ECharts implementation; the active app uses `PlotlyBubbleChart`.
  - `data/csv/migrate_csvs_to_blob.py` is an empty file.

- `public/data/` contains generated outputs, but the app does not primarily read from them. Editing these files alone will not change production unless blob upload/mapping is also updated.

- Test tooling exists, but there are no test files. Any refactor is effectively untested by default.

## How To Work In This Repo

- Safest files for UI/product changes:
  - `src/components/Dashboard.tsx`
  - `src/components/DashboardControls.tsx`
  - `src/components/PlotlyBubbleChart.tsx`
  - `src/components/PriceDifferenceChart.tsx`

- Safest files for data-loading behavior:
  - `src/hooks/useDashboardData.ts`
  - `src/utils/dataLoader.ts`
  - `src/types/bubbleData.ts`

- Treat these as generated or output-oriented:
  - `src/routeTree.gen.ts`
  - `public/data/*.json`
  - `blob_mapping.json`
  - anything under `data/img/` or `data/mat/` if regenerated locally

- Preserve current patterns:
  - Single-route dashboard architecture.
  - Runtime source switching via `DataSource`.
  - Blob-backed data access rather than committing URL changes into app code for Yahoo data.
  - TypeScript interfaces in `src/types/bubbleData.ts` as the frontend contract.

- Be skeptical of docs before changing pipeline code. Prefer workflow files and actual script behavior over README/setup prose.

## Quick Start For Future Agents

If you need to onboard fast:

1. This is a client-side dashboard, not a backend service. Start at `src/components/Dashboard.tsx` and `src/hooks/useDashboardData.ts`.
2. The app fetches data from Vercel Blob, not from local files in normal operation. `src/utils/dataLoader.ts` is the runtime source of truth.
3. There are really two datasets:
   - WRDS historical: fixed blob URLs.
   - Yahoo recent: blob URL mapping fetched from remote `blob_mapping.json`.
4. The Python scripts matter only if you are changing data production. The GitHub Actions workflow is the clearest description of that path.
5. Expect doc drift. Validate claims in code before relying on them.
