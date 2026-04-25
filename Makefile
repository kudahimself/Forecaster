# Run everything from the repo root. Django's manage.py handles its own
# sys.path so `python backend/manage.py …` works from anywhere — no need
# to cd into backend/ (which broke ezwinports make + cmd.exe on Windows
# because cmd doesn't accept `../path/to/exe` as a command).
PY := .venv/Scripts/python.exe
MANAGE := $(PY) backend/manage.py

.PHONY: help setup venv install install-sdk frontend-install migrate backend frontend dev check clean-db \
        ingest ingest-smoke validate build-features populate-sectors sdk-smoke \
        rf-run rf-smoke portfolio-backtest permutation-test \
        demo demo-full run-pipeline test test-backend test-e2e e2e-seed \
        docker-up docker-down docker-build scheduled-ingest

help:
	@echo "Setup:"
	@echo "  setup              - venv + install backend & sdk + frontend install (one-shot)"
	@echo "  venv               - create .venv/"
	@echo "  install            - install backend deps + SDK (editable)"
	@echo "  frontend-install   - npm install in frontend/"
	@echo "  migrate            - apply Django migrations"
	@echo ""
	@echo "Run:"
	@echo "  backend            - Django dev server on :8000"
	@echo "  frontend           - Vite dev server on :5173"
	@echo ""
	@echo "Demo / pipeline:"
	@echo "  demo               - end-to-end smoke pipeline (3 tickers, 8 years, ~3-5 min)"
	@echo "  demo-full          - end-to-end full pipeline (100 tickers, ~20-40 min)"
	@echo "  run-pipeline       - rf_run + backtest + permutation on current warehouse"
	@echo ""
	@echo "Steps individually:"
	@echo "  ingest             - full-universe ingest (use ingest-smoke for 3 tickers)"
	@echo "  populate-sectors   - seed dim_symbols.sector from config YAML"
	@echo "  validate           - run DQ checks"
	@echo "  build-features     - build fct_features (technicals + returns + betas + target)"
	@echo "  rf-run             - run RF strategy (use rf-smoke for tiny universe)"
	@echo "  portfolio-backtest - RUN=<uuid> [ENTRY=1 HOLDING=next_month]"
	@echo "  permutation-test   - RUN=<uuid> N=100"
	@echo ""
	@echo "Misc:"
	@echo "  check              - django system check"
	@echo "  clean-db           - delete warehouse.db (destructive)"
	@echo "  sdk-smoke          - verify tracker SDK wiring"

# ----------------- setup -----------------

setup: venv install frontend-install migrate
	@echo ""
	@echo "Setup complete. Next:"
	@echo "  make demo         # build a smoke warehouse end-to-end"
	@echo "  make backend      # terminal 1"
	@echo "  make frontend     # terminal 2"

venv:
	python -m venv .venv

install:
	$(PY) -m pip install -r requirements.txt
	$(PY) -m pip install -e ./sdk

install-sdk:
	$(PY) -m pip install -e ./sdk

frontend-install:
	cd frontend && npm install

migrate:
	$(MANAGE) migrate

# ----------------- run -----------------

backend:
	$(MANAGE) runserver 8000

frontend:
	cd frontend && npm run dev

check:
	$(MANAGE) check

clean-db:
	rm -f data/warehouse.db data/warehouse.db-journal

# ----------------- ingest / features / DQ -----------------

ingest:
	$(MANAGE) ingest --universe default --start 2018-01-01 --cache

ingest-smoke:
	$(MANAGE) ingest --universe smoke --start 2018-01-01

populate-sectors:
	$(MANAGE) populate_sectors

validate:
	$(MANAGE) validate

build-features:
	$(MANAGE) build_features

# ----------------- models -----------------

rf-run:
	$(MANAGE) rf_run

rf-smoke:
	$(MANAGE) rf_run --min-train-rows 20 --top-k 2 --name smoke_rf --tag smoke

# Usage: make portfolio-backtest RUN=<uuid> [ENTRY=1] [HOLDING=next_month]
ENTRY ?= 1
HOLDING ?= next_month
portfolio-backtest:
	$(MANAGE) portfolio_backtest --run-id $(RUN) --entry-delay-bdays $(ENTRY) --holding $(HOLDING)

# Usage: make permutation-test RUN=<uuid> N=100
N ?= 100
permutation-test:
	$(MANAGE) permutation_test --run-id $(RUN) --n-permutations $(N)

sdk-smoke:
	$(PY) -c "import tracker; \
with tracker.run(experiment='sdk_smoke', params={'seed': 0}, tags=['smoke']) as r: \
    r.log_metric('demo_metric', 3.14); r.log_importance({'f1': 0.5, 'f2': 0.3}); \
    print('ok, run_id=', r.run_id)"

# ----------------- demo pipeline -----------------

# End-to-end on 3-ticker smoke universe. Fast (~3-5 min). For first-look.
demo: migrate populate-sectors
	$(MANAGE) ingest --universe smoke --start 2018-01-01
	$(MANAGE) validate --universe smoke
	$(MANAGE) build_features
	$(MANAGE) run_full_pipeline --min-train-rows 20 --top-k 2 --n-permutations 20 --name demo --tag demo
	@echo ""
	@echo "Demo warehouse built. Start the dashboard:"
	@echo "  make backend    # terminal 1"
	@echo "  make frontend   # terminal 2"
	@echo "  open http://localhost:5173"

# End-to-end on the full ~100-ticker universe. Slower (~20-40 min).
demo-full: migrate populate-sectors
	$(MANAGE) ingest --universe default --start 2018-01-01 --cache
	$(MANAGE) validate
	$(MANAGE) build_features
	$(MANAGE) run_full_pipeline --n-permutations 100 --name demo_full --tag demo
	@echo ""
	@echo "Full pipeline complete. Open http://localhost:5173"

# Re-run just the modelling side against whatever is in the warehouse.
# Pass-throughs: TOPK, SHORTK, SECTOR, N, NAME
TOPK ?= 15
SHORTK ?= 0
SECTOR ?=
NAMESUFFIX ?= pipeline
run-pipeline:
	$(MANAGE) run_full_pipeline --top-k $(TOPK) --top-k-short $(SHORTK) \
		$(if $(SECTOR),--max-per-sector $(SECTOR),) \
		--n-permutations $(N) --name $(NAMESUFFIX)

# ----------------- tests -----------------

test: test-backend test-e2e

test-backend:
	$(MANAGE) test --verbosity 1

# Seeds a small but varied warehouse (2 runs, 1 long-only + 1 long-short)
# so the e2e tests have something to render. Additive — does not wipe.
e2e-seed: migrate populate-sectors
	$(MANAGE) ingest --universe smoke --start 2022-01-01
	$(MANAGE) build_features
	$(MANAGE) validate --universe smoke
	$(MANAGE) run_full_pipeline --min-train-rows 20 --top-k 2 --n-permutations 5 --name e2e_long_only
	$(MANAGE) run_full_pipeline --min-train-rows 20 --top-k 1 --top-k-short 1 --n-permutations 5 --name e2e_long_short

test-e2e:
	cd frontend && npm run e2e

# ----------------- docker -----------------

docker-build:
	docker compose build

docker-up:
	docker compose up --build

docker-down:
	docker compose down

# Dev mode: bind-mount source so edits hot-reload (Vite HMR + Django auto-reload).
docker-dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

docker-dev-down:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml down

# ----------------- scheduled ingestion -----------------

# Run all registered ingest jobs and log their history.
# Wire to cron / Windows Task Scheduler / Docker scheduler service.
# JOB=yfinance_prices|famafrench_factors|all  (default: all)
JOB ?= all
scheduled-ingest:
	$(MANAGE) run_scheduled_ingest --job $(JOB)
