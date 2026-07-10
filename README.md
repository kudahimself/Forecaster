# Forecaster — Quant Research Tracker

Local-first experiment tracking platform for cross-sectional equity
strategies. Each research run — fired from a Jupyter notebook or the CLI —
logs its params, metrics, feature importances, and permutation-test
diagnostics to a single SQLite warehouse. A Django + React dashboard sorts
runs by p-value / Sharpe / realised return, overlays cumulative-return
curves, and surfaces overfitting signals across configurations.

## Why

Cross-sectional quant research tends to generate a mess of notebooks with
scattered CSVs and half-copied results. This project wraps one specific
strategy (Random Forest walk-forward on US equities with a within-date
permutation test, ported from my personal research) into a proper
tracking platform so that *which config beat the null* is a single query,
not a screenshot grep.

The strategy is a plug-in; the platform is the product.

## What's in it

**Pipeline** (SQL tables in parentheses)
1. **Ingest** — yfinance OHLCV + Ken French Fama-French 5-factor daily
   (`raw_prices`, `raw_factors`, `dim_symbols`).
2. **Data quality** — pandera schemas + freshness + null% + duplicate +
   suspicious returns + universe coverage (`dq_runs`, `dq_checks`).
3. **Features** — monthly aggregation of daily technicals (RSI, Bollinger,
   ATR, MACD, Garman-Klass), multi-horizon returns, 24m rolling Fama-French
   betas, `target_1m` forward shift (`fct_features`).
4. **Tracker core** — experiments, runs, params, metrics, tags, artifacts,
   feature importance (`experiment`, `run`, `run_param`, `run_metric`,
   `run_tag`, `run_artifact`, `run_feature_importance`).
5. **RF strategy** — walk-forward Random Forest, long-only or long-short
   (`--top-k-short N`), optional per-sector cap (`--max-per-sector N`)
   (`rf_predictions`, `rf_picks` with `direction ±1`).
6. **Portfolio backtest** — PyPortfolioOpt max-Sharpe per leg, dollar-
   neutral combination in long-short mode, configurable entry delay and
   holding period (`rf_portfolio_returns`, `rf_portfolio_weights`).
7. **Permutation test** — within-date shuffle of `target_1m`, N reruns of
   the full RF pipeline, empirical p-values + parquet artifact of the full
   distribution (`perm_summary`).

**Dashboard** (Django + React, Recharts for plots)
- **Runs leaderboard** — sortable table across all runs: params, metrics,
  p_two_sided, tags. The overfit-detector page.
- **Run detail** — param/metric key-value grids + **cumulative return
  chart** + **permutation histogram** with baseline and median markers +
  feature importance table + artifact list.
- **Compare** — pick 2+ runs from the leaderboard, overlay equity curves,
  side-by-side param table with diffs highlighted amber.
- **Features** — per-feature aggregation across all runs (mean, median,
  std, avg rank, best/worst rank) with inline importance bars.
- **Data quality** — freshness card + per-check status pills + details
  JSON peek for the currently selected DQ run.
- **Ingest status** — warehouse freshness card + per-symbol coverage table.
- **Schedules** — history of scheduled ingest jobs (who ran, when, for how
  long, how many rows landed, any errors).

## Quick start

### Option A — Docker (single command)

```bash
docker compose up --build
# open http://localhost:5173
```

Backend auto-migrates on first boot; warehouse persists in a named Docker
volume. nginx in the frontend container serves the built React app and
proxies `/api/*` to Django. To seed data inside the running container:

```bash
docker compose exec backend python manage.py run_scheduled_ingest --job all
docker compose exec backend python manage.py build_features
docker compose exec backend python manage.py run_full_pipeline \
    --min-train-rows 20 --top-k 2 --n-permutations 20 --name demo
```

### Option B — Native (local venv + npm)

```bash
make setup       # venv + install + migrate + npm install (one-shot)
make demo        # end-to-end 3-ticker smoke (~3-5 minutes)
make backend     # terminal 1 → http://127.0.0.1:8000
make frontend    # terminal 2 → http://127.0.0.1:5173
```

After `make demo` you'll have: ingested OHLCV + FF, 10 DQ checks, 19
monthly features per symbol, one RF run, a backtest, and a 20-permutation
test — all visible in the dashboard.

For the real research run on ~100 tickers:

```bash
make demo-full   # ~20-40 minutes (depends on yfinance speed)
```

## Automated ingestion

Every ingestion job (yfinance prices, Fama-French factors) is wrapped in a
small tracker so each execution produces one row in `ingest_runs`:
start/end timestamps, status, rows inserted, error text on failure. The
`/schedules` page reads that history.

```bash
make scheduled-ingest                       # runs all registered jobs
make scheduled-ingest JOB=yfinance_prices   # run a single job
```

To recur on a schedule:

- **Linux/macOS cron**: `0 6 * * * /path/to/.venv/bin/python /path/to/backend/manage.py run_scheduled_ingest --job all`
- **Windows Task Scheduler**: Create a task that runs the same command.
- **Docker**: add a sidecar service running the management command in a
  loop (see docker-compose.yml for a starting point; APScheduler is an
  easy in-process swap-in if you prefer).

## CI

GitHub Actions (`.github/workflows/tests.yml`) runs on every push:
1. **Backend** — Django system check + full test suite (49 tests).
2. **Frontend** — `npm run build` (TypeScript type-check + Vite build).

## Running tests

```bash
make test-backend   # 49 Django tests, no network required
# E2E (needs seeded data and brings up both servers):
make e2e-seed
make test-e2e
```

## Stack

| Layer | Tech |
|---|---|
| Ingest | yfinance 1.3, pandas-datareader 0.10 |
| Storage | SQLite (single `data/warehouse.db`) |
| ML | scikit-learn 1.7 (Random Forest), statsmodels 0.14 (RollingOLS for betas) |
| Portfolio | PyPortfolioOpt 1.6 (EfficientFrontier max-Sharpe) |
| DQ | pandera 0.31 |
| Backend | Django 5.2, Django REST Framework 3.17 |
| Frontend | React 19, Vite 5 (pinned — see caveats), Recharts, React Router 7 |
| SDK | stdlib `sqlite3` only (no ORM dep in Jupyter) |

## Layout

```
backend/
  config/                 Django project settings + URLs
  tracker_core/           Experiment, Run, RunParam, RunMetric, RunTag,
                          RunArtifact, RunFeatureImportance ORM models
  ingest/                 yfinance client, Fama-French loader, universe + sector YAMLs
  quality/                pandera schemas, DQ check runner, dq_runs + dq_checks
  features/               daily technicals, monthly rollup, returns, betas
  models_rf/              walk-forward RF strategy, rf_predictions + rf_picks
  portfolio/              optimiser port, backtest (long-only or long-short),
                          rf_portfolio_returns + rf_portfolio_weights
  permutation/            within-date shuffle + N-perm runner, perm_summary
  api/                    DRF viewsets over all of the above
frontend/
  src/pages/              Leaderboard / RunDetail / Compare / FeatureImportance
                          / DqDashboard / IngestStatus
  src/components/         EquityCurve, PermHistogram (Recharts wrappers)
  src/lib/api.ts          typed fetch helpers
sdk/
  tracker/                notebook-facing SDK (zero Django dep)
data/                     warehouse.db + artifacts/ + raw_cache/ (all gitignored)
notebooks/                example notebooks using the SDK
Makefile                  every command the project supports
```

## Using the SDK from a notebook

```python
import tracker

with tracker.run(
    experiment="rf_crosssectional_us",
    params={"top_k": 15, "window_months": 12, "seed": 42},
    tags=["baseline"],
) as r:
    # ... your training code ...
    r.log_metric("oos_sharpe", 1.21)
    r.log_metric("p_two_sided", 0.032)
    r.log_importance({"rsi": 0.12, "return_12m": 0.18})
    r.log_artifact("equity_curve", "path/to/plot.png", kind="plot")
```

The SDK auto-discovers `<repo>/data/warehouse.db` by walking up from the
notebook's working directory. Override with `FORECASTER_DB_PATH`.

Use `tracker.attach(run_id)` to append metrics to an already-finished
run (that's how the portfolio backtest logs `portfolio_*` metrics back
onto the RF run that produced its picks).

## Common workflows

```bash
# One off:
make populate-sectors                      # map 106 tickers to GICS sectors
make ingest                                # full 100-ticker universe, 2018-today
make validate                              # run DQ checks
make build-features                        # build fct_features

# Run RF strategies with different configurations:
make rf-run                                # long-only, top_k=15
$(MANAGE) rf_run --top-k 15 --top-k-short 15 --max-per-sector 2 --name ls_diversified

# Backtest + permutation test a specific run:
make portfolio-backtest RUN=<uuid>
make permutation-test RUN=<uuid> N=100

# Or fire the whole thing in one go:
$(MANAGE) run_full_pipeline --top-k 15 --max-per-sector 2 --n-permutations 100 \
    --name "baseline_sector2"
```

Every config lands as a separate row on the leaderboard with its own
p-value — compare them side by side to see the OOS cost of, say, adding
sector diversity or enabling shorts.

## Known caveats

- **yfinance is survivorship-biased.** Delisted names aren't in the
  universe, so backtest returns are systematically overstated. Not fixable
  at the backtest layer.
- **Backtest frictions not modelled.** No transaction costs, slippage,
  borrow fees, or tax. Treat `portfolio_ann_sharpe` as an upper bound.
- **Entry delay and holding period are parameters.** Default is T+1 entry,
  hold until next month-end close — the standard monthly-rebalance
  convention. The source research used `MonthEnd(0)` with month-end
  rebalance dates, which collapsed the hold to a single day; set
  `--entry-delay-bdays 0 --holding 1` to reproduce that.
- **Garman-Klass volatility** — the source notebook's formula reads as
  typo'd (produces values ~10 vs canonical ~1e-4 for daily vol). Ported
  as-is with a code comment; don't read too much into that feature's rank.
- **Node 20.16 / Vite 5 pin.** Default `npm create vite` installs Vite 8
  which crashes on Node < 20.19 (rolldown native binding). Frontend is
  pinned to `vite@^5.4.10` + `@vitejs/plugin-react@^4.3.4`. Bump after
  upgrading Node.
- **Vite binds IPv4 explicitly.** `server.host = '127.0.0.1'` in
  `vite.config.ts` — default `localhost` binding was IPv6-only on Windows
  and that broke the `/api` proxy to Django.

## License

MIT — use, fork, do whatever. No warranty on the research itself; the
permutation test is there precisely because a pretty Sharpe number
shouldn't be trusted without one.
