# CI Pipeline Stability Runbook

## Contract

The Yahoo production pipeline is all-or-nothing. All 25 configured tickers are required. A run may retry transient upstream failures, but it must not publish stale, partial, or structurally invalid output. A market holiday with no new option rows is valid only when Yahoo option requests succeed and the existing history passes every staging check.

The required scraper-to-estimator handoff is:

- `data/csv/optout_{ticker}.csv` — accumulated option observations.
- `data/csv/optout_{ticker}_count.csv` — derived row counts by option date.
- `data/prices/{ticker}.csv` — canonical Yahoo closes with `date,regular,adjusted` columns.
- `data/pipeline-status.json` — non-secret CSV staging/publication state, row counts, newest dates, and retry counts. Its `scope` field deliberately does not claim end-to-end MAT/JSON deployment success.

The JSON schema and dashboard runtime API are unchanged.

## Observed failure history

The investigation snapshot covered 58 production workflow runs: 23 succeeded and 35 failed. Failures grouped into two operational clusters:

1. Yahoo returned empty or malformed history/option responses. The scraper accessed `Close` immediately, skipped failed expirations, or skipped an empty ticker and still exited successfully. Downstream jobs then operated on incomplete artifacts.
2. CSV Blob reads or writes failed because of transient HTTP failures or a token/base-URL store mismatch. One historical workaround treated Blob authorization errors as warnings, allowing the workflow to continue without publishing the required CSV state.

The root causes were unbounded/uncoordinated network behavior, network calls during module import and JSON conversion, FRED being fetched once per ticker, missing whole-batch validation, and batch loops that caught exceptions but returned exit code zero. The action-runtime deprecation warning seen in the same runs is tracked but is not causal; action-major upgrades are intentionally deferred.

The GitHub log endpoint used during the original investigation may require repository authentication. The durable evidence is therefore the 23/35 snapshot above, the workflow run/job URLs retained in GitHub Actions, and the deterministic reproductions below.

## Retry and validation behavior

Yahoo history, expiration lists, every option chain, FRED DGS1MO, and Blob CSV downloads receive four total attempts. Delays after the first three failures are 2, 4, and 8 seconds plus zero-to-one second jitter. Empty data, missing `Close`, missing call/put chain data, malformed dates, non-200 Blob responses, and empty Blob CSVs count as failed attempts.

FRED DGS1MO is fetched once at the beginning of a run and reused for all tickers. The scraper fetches canonical prices and stages every option/count/price file locally. Before the first CSV upload, validation checks:

- all 75 required files exist and contain rows;
- option and price schemas are complete;
- option and expiration dates parse;
- every option date has calls and puts;
- strikes, underlying prices, option prices, regular closes, and adjusted closes are finite;
- count files exactly describe option rows; and
- every option date has a canonical price date.

Any failure writes `pipeline-status.json`, prints the ticker, operation, total attempts, and final exception where applicable, and exits nonzero. CSV uploads begin only after all tickers pass. Blob storage is not transactional, so a write failure after earlier writes cannot roll those writes back; downstream publication still stops and the next successful run reconciles the complete set.

## Deterministic reproductions

Run the fixture-based regression suite without production secrets or network access:

```bash
python -m unittest discover
```

The tests cover retry recovery and exhaustion, empty/malformed Yahoo history, failed option chains, one FRED request per run, missing canonical dates, holiday/no-new-row merging, offline JSON price loading, and aggregate nonzero batch status.

To reproduce configuration gates manually:

```bash
env -u FRED_API_KEY python scripts/yf_data_scraper.py
python scripts/validate_pipeline_staging.py
```

The first command must fail before ticker work and still emit a failed status artifact. The second must list every missing or invalid ticker and return nonzero. JSON generation can be proven offline by blocking outbound networking and running `python scripts/bubble_estimator.py`; it reads only staged prices and MAT files.

## Operator commands

```bash
# Local verification
python -m unittest discover
npm test
npm run check
npm run build

# Inspect recent production runs
gh run list --workflow "Daily Yahoo Finance Bubble Update" --limit 20
gh run view <run-id> --log-failed

# Download diagnostic artifacts
gh run download <run-id> -n pipeline-status
gh run download <run-id> -n yahoo-staging
gh run download <run-id> -n bubble-json-files

# Start a controlled production run
gh workflow run "Daily Yahoo Finance Bubble Update"
```

The schedule is `0 23 * * 1-5` (23:00 UTC on weekdays), consistently after the regular US market close. Production runs share a non-cancelling concurrency group, so a later run waits instead of interrupting a publication in progress.

## Failure triage

1. Open the failed step and download `pipeline-status`.
2. Find tickers whose state is `failed`; inspect `error` and `retry_counts`.
3. If the operation is Yahoo or FRED, confirm the provider response independently and wait for recovery. Do not substitute old files.
4. If it is a Blob download, verify `BLOB_BASE_URL` addresses the same store as `BLOB_READ_WRITE_TOKEN` and that the historical `csv/optout_{ticker}.csv` exists.
5. If it is a Blob upload, rotate/fix the token or store URL before retrying. Authorization failures are fatal.
6. If staging validation fails, inspect the named CSV and compare option dates to `data/prices/{ticker}.csv`. Do not bypass the gate.
7. If MAT/JSON fails, retain all staging artifacts, reproduce locally, and fix the deterministic computation before dispatching again.

## Recovery procedure

1. Correct the upstream availability, secret, or code problem.
2. Re-run all local verification commands.
3. Manually dispatch one production workflow.
4. Confirm all 25 ticker states are successful, all staged artifacts exist, JSON validation passes, the Blob mapping contains exactly the expected tickers, and the deployment summary reports the intended upload count.
5. Confirm the live dashboard resolves the updated mapping and representative tickers.
6. Observe five consecutive weekday scheduled successes before declaring the incident closed.

A genuine upstream outage is an expected hard failure: it must terminate within the configured job timeout and identify the ticker and operation. Never recover by deploying a partial dataset or copying stale output into the current run.

## Remediation checklist

- [x] Import-safe Python entry points.
- [x] Shared deterministic retry helper.
- [x] One FRED request per run.
- [x] Canonical price artifact and offline JSON conversion.
- [x] Whole-batch staging validation before CSV publication and MAT computation.
- [x] Aggregate nonzero batch exits.
- [x] Non-secret pipeline status artifact.
- [x] Exact Python dependency pins.
- [x] Pinned runner, timeouts, concurrency, and post-close weekday schedule.
- [x] Separate push/pull-request CI from production scraping.
- [x] Mocked failure-path coverage for stale sessions, malformed responses, aggregate failures, and upload cutoff.
- [ ] Manually dispatch and verify one production run with repository secrets.
- [ ] Record five consecutive successful weekday schedules.
- [ ] Evaluate action-major upgrades separately from this incident.
