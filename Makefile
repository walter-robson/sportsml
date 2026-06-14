.PHONY: help install api dagster workbench demo ingest seed test lint clean

PY ?= python3.12
PIP ?= $(PY) -m pip

help:
	@echo "sportsml — common targets"
	@echo "  make install       install python + node deps"
	@echo "  make ingest        run dagster ingestion (one season, NBA)"
	@echo "  make seed          alias for ingest"
	@echo "  make api           run FastAPI service on :8000"
	@echo "  make dagster       run dagster webserver on :3001"
	@echo "  make workbench     run Next.js dev server on :3000"
	@echo "  make demo          ingest + start all services (foreground via docker compose)"
	@echo "  make test          run pytest"
	@echo "  make lint          run ruff"

install:
	$(PY) -m venv .venv || true
	. .venv/bin/activate && $(PIP) install -e ".[dev]"
	# Multiple wheel sources share the `sportsml/` namespace; hatch's editable
	# install only registers one path, so we drop a .pth file with all of them.
	. .venv/bin/activate && $(PY) scripts/install_dev_paths.py
	cd packages/workbench && pnpm install || npm install

ingest:
	. .venv/bin/activate && DAGSTER_HOME=$$(pwd)/.dagster_home \
	  dagster asset materialize --select '*' -m sportsml_dagster

seed: ingest

api:
	. .venv/bin/activate && uvicorn sportsml_api.main:app --host 0.0.0.0 --port 8000 --reload

dagster:
	. .venv/bin/activate && DAGSTER_HOME=$$(pwd)/.dagster_home \
	  dagster dev -m sportsml_dagster -p 3001

workbench:
	cd packages/workbench && pnpm dev || npm run dev

demo:
	docker compose up --build

test:
	. .venv/bin/activate && pytest -q

lint:
	. .venv/bin/activate && ruff check . && ruff format --check .

clean:
	rm -rf .venv data/*.parquet data/sportsml.duckdb .dagster_home
	find . -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
