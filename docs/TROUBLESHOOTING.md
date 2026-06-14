# Troubleshooting

Common issues for v0 local development.

## Setup

### `make install` fails on Python deps
- Confirm Python 3.12+: `python3.12 --version`
- If macOS missing 3.12: `brew install python@3.12`
- Some deps (scipy, pyarrow) need build tools: `xcode-select --install` on macOS

### `pnpm` not found
- Frontend works with either pnpm or npm; the Makefile falls back to npm
- Install pnpm globally for speed: `npm i -g pnpm`

## Ingestion

### `nba_api` HTTP 429 / rate-limited / `ReadTimeoutError`
- stats.nba.com throttles aggressively and is unreachable from many networks
- Set `NBA_API_DELAY_S=1.5`, `NBA_API_TIMEOUT=90`, `NBA_API_RETRIES=8` in `.env` if you keep hitting limits
- Use smoke mode (`SPORTSML_INGEST_MODE=smoke`) for faster iteration — only ingests ~50 games
- **If ingest is fully blocked**: run `python scripts/seed_synthetic_data.py` instead. It writes ~2,800 stints of synthetic 6-team data into `data/features/nba/on_off_stints.parquet` in the same schema the Dagster pipeline would produce. The model layer falls back to this file when DuckDB has no `features.nba.on_off_stints` table.

### `nba_api` returns empty responses
- stats.nba.com occasionally returns 200 with empty payloads; the adapter retries
- If persistent, try VPN — some IP ranges get throttled harder

### Dagster asset materialization hangs
- Check `dagster dev` logs at `:3001`
- If stuck on a single asset, kill and re-run with `--select` for just that asset
- Verify `DAGSTER_HOME` is set (defaults to `./.dagster_home`)

## API

### `uvicorn` fails to import sportsml_api
- Check that `pyproject.toml` packages array includes all package paths
- Run from repo root: `uvicorn sportsml_api.main:app`
- Ensure `.venv` is activated: `source .venv/bin/activate`

### `GET /datasets` returns empty
- You haven't ingested data yet. Run `make ingest`.
- Or check `data/sportsml.duckdb` exists and has tables: `duckdb data/sportsml.duckdb "SHOW TABLES;"`

### `POST /models/lineup_net_rating/runs` returns 500
- Most common cause: features assets not materialized. Run `make ingest`.
- Check API logs for the actual exception
- Verify `features.nba.on_off_stints` exists in DuckDB

## Workbench

### Page is blank / hydration error
- Check browser console for the actual error
- Verify `NEXT_PUBLIC_API_URL` matches the running API (default `http://localhost:8000`)
- Hard reload (`cmd+shift+R`) — Next.js dev cache can stick

### Sliders render but Run does nothing
- Check Network tab: is `POST /models/lineup_net_rating/runs` hitting the API?
- CORS issue? FastAPI service allows `localhost:3000` by default; if you changed ports, add to API's `allow_origins`

### Frontend shows mock data even when API is up
- Check that `NEXT_PUBLIC_USE_MOCK` is not set to `true` in `.env.local`
- Restart `pnpm dev` after env changes

## Demo loop

### Run completes but table doesn't update
- The active run pill in the top bar should change after a successful run
- Check that `GET /models/lineup_net_rating/runs/{run_id}` returns `status: "succeeded"`
- If the model returned no rows, the table will be empty — check ingestion completed

### Run is too slow (>30s)
- Reduce `min_possessions` to a smaller value? No — that makes it slower
- Check that you're running smoke-mode ingest (1 month of games)
- Profile the model: `python -m cProfile -o run.prof ...`

## Reset everything

```bash
make clean
make install
make ingest
```

This wipes `.venv`, `data/`, and `.dagster_home`. Use when in doubt.
