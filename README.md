# Financial Bubble Detection Dashboard

Financial Bubble Detection Dashboard is a React and TypeScript application for exploring option-implied bubble estimates across major equities and the S&P 500. It visualizes put, call, and combined estimates with confidence bands, compares split-adjusted and raw prices, and supports both the historical WRDS research dataset and a newer Yahoo Finance pipeline backed by Vercel Blob storage.

## What It Shows

- Bubble estimates for put options, call options, and combined option chains.
- Three tau groups that represent short, medium, and longer option horizons.
- Confidence intervals for each estimate series.
- Price comparison charts for adjusted versus raw market prices.
- Data-source switching between historical WRDS output and Yahoo Finance updates.

## Tech Stack

- React 19, TypeScript, Vite, and TanStack Router
- Plotly.js for interactive charts
- Tailwind CSS, Radix UI primitives, and shadcn-style components
- Biome for linting and formatting
- Python and TypeScript scripts for the Yahoo Finance data pipeline
- Vercel Blob for generated Yahoo CSV and JSON artifacts

## Setup

Use Node.js 20 or newer. The repository includes both `package-lock.json` and `bun.lock`; the commands below use npm because the package lock is present and works with the existing scripts.

```bash
git clone <repository-url>
cd financial-bubble-detection-dashboard
npm install
npm run dev
```

Open `http://localhost:3000`.

You can also use Bun:

```bash
bun install
bun run dev
```

## Useful Commands

```bash
npm run dev       # Start Vite on port 3000
npm run build     # Build the app and run TypeScript checks
npm run lint      # Run Biome lint rules
npm run format    # Format files with Biome
npm run check     # Run Biome checks
npm run test      # Run Vitest, if tests are present
```

## Usage

1. Start the app with `npm run dev`.
2. Select a data source: `WRDS` for the historical research dataset or `Yahoo Finance` for the Blob-backed update pipeline.
3. Choose a ticker such as `SPX`, `AAPL`, `MSFT`, `NVDA`, or `TSLA`.
4. Adjust the date range to inspect how bubble estimates move across time.
5. Compare the put, call, combined, and price-difference charts for the same selected asset.

## Data Pipeline

The dashboard consumes generated JSON files that contain daily stock prices and option-derived bubble estimates. Historical WRDS data is treated as static research output. The Yahoo Finance workflow refreshes option-chain CSVs, rebuilds derived count files, runs the estimator, publishes runtime JSON to Vercel Blob, and updates the dashboard through a Blob-hosted mapping file.

Local Blob-writing scripts require secrets in `.env.local`:

```bash
BLOB_READ_WRITE_TOKEN=your_vercel_blob_token
BLOB_BASE_URL=https://your-public-blob-store.example
FRED_API_KEY=your_fred_api_key
```

Do not commit `.env.local` or real tokens. GitHub Actions reads production values from repository secrets.

## Architecture Notes

- `src/components/Dashboard.tsx` coordinates the main dashboard view.
- `src/hooks/useDashboardData.ts` owns selected ticker, source, date range, loading state, and chart transformations.
- `src/utils/dataLoader.ts` loads Blob mappings, fetches generated JSON, and converts raw records into chart-ready series.
- `src/components/PlotlyBubbleChart.tsx` renders the primary bubble-estimate charts.
- `src/components/PriceDifferenceChart.tsx` renders adjusted-versus-raw price comparisons.
- `scripts/` contains the Yahoo Finance ingestion, estimator, Blob upload, reconciliation, and validation utilities.
- `.github/workflows/` automates nightly and manual data publication.

## Repository Status

This repository has an intentionally real project history with generated data churn from earlier pipeline iterations. Current generated Yahoo CSVs and JSONs are expected to live in Blob storage or workflow artifacts, not as committed source files. Before sharing or deploying with write access, rotate any previously exposed Blob token and keep all future credentials in GitHub/Vercel secrets.

