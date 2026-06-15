# sportsml

[![CI](https://github.com/walter-robson/sportsml/actions/workflows/ci.yml/badge.svg)](https://github.com/walter-robson/sportsml/actions/workflows/ci.yml)
[![CodeQL](https://github.com/walter-robson/sportsml/actions/workflows/codeql.yml/badge.svg)](https://github.com/walter-robson/sportsml/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/gh/walter-robson/sportsml/branch/main/graph/badge.svg)](https://codecov.io/gh/walter-robson/sportsml)

> Foundry-style data platform for sports analytics. NBA-first, sport-agnostic architecture.

A platform — not a service — that gives sports organizations a typed data ontology, declarative transforms, tunable model templates, and an operational workbench. Teams bring their own IP (configs, philosophies, custom models); the platform provides the rails.

## v0 scope (what runs today)

- **One season** of NBA data (2023-24) ingested via [`nba_api`](https://github.com/swar/nba_api)
- **Ontology**: Player, Team, Game, Possession, Shot, Lineup, LineupStint, Substitution
- **One Model**: `lineup_net_rating` (Bayesian-shrunk RAPM) with tunable knobs
- **One App**: Lineup Analysis — auto-generated config sliders + projected lineup table
- **Local-only**: no auth; one demo tenant hard-coded
- **Sport-pluggable architecture**: `basketball.nba` wired; NCAA / EuroLeague / NFL / MLB / NHL packages stubbed

See [`docs/superpowers/specs/2026-05-22-sportsml-platform-design.md`](docs/superpowers/specs/2026-05-22-sportsml-platform-design.md) for the full design.

## Quick start

```bash
cp .env.example .env
make install                            # venv + node deps
python scripts/seed_synthetic_data.py   # synthetic on_off_stints (instant, no network)
make api &                              # FastAPI on :8000
make workbench                          # Next.js on :3000
```

Then open `http://localhost:3000` and navigate to **Apps → Lineup Analysis**.

### Optional: real NBA ingest

```bash
make ingest    # dagster materialize via nba_api — requires reachable stats.nba.com
```

stats.nba.com is rate-limited and often unreachable from many networks. If the ingest
fails, the synthetic seed above gives you a working demo against realistic
synthetic data — same schema as the real pipeline.

### Optional: Docker

```bash
make demo      # docker compose up --build
```

## Architecture

```
[1] Workbench       Next.js + TS + shadcn
[2] Platform API    FastAPI
[3] Core            sportsml.core — ontology, models, apps ABCs
[4] Sport plugins   sportsml.sports.basketball.nba (+ stubs)
[5] Storage         DuckDB (analytics) + Parquet on disk
[6] Ingestion       Dagster — nba_api source assets
```

Cross-cutting dimensions on every row, every call, every config:

- `tenant_id` — multi-tenant by design (POC = single demo tenant)
- `sport_id` — sport-pluggable from day one

## Repo layout

```
sportsml/
  packages/
    core/                    Python: sportsml.core
    api/                     Python: FastAPI service
    workbench/               Next.js app
    sports/
      basketball/{nba,ncaa,euroleague}/
      football/nfl/
      baseball/mlb/
      hockey/nhl/
  dagster_project/           Dagster code locations
  data/                      Hive-partitioned Parquet (gitignored)
  docker/                    Dockerfiles per service
  docs/                      Specs and design docs
```

## Development

```bash
make test                 # pytest
make test-cov             # pytest with coverage report
make lint                 # ruff lint + format check
make format               # auto-format
make typecheck            # mypy
make dagster              # open Dagit on :3001 for pipeline debugging

# One-time hook setup (recommended for contributors)
make precommit-install    # installs pre-commit git hooks
make precommit            # run all hooks against the full tree
```

### CI

Every PR runs (see `.github/workflows/ci.yml`):

- `ruff check` + `ruff format --check`
- `mypy` on `packages/core` and `packages/api`
- `pytest` with coverage; patch coverage gated at 80% via `diff-cover`
- `next lint`, `tsc --noEmit`, and `next build` for `packages/workbench`
- All pre-commit hooks (`gitleaks`, file hygiene, etc.)
- CodeQL security scanning (Python + TypeScript)

Coverage reports are uploaded to Codecov (set `CODECOV_TOKEN` repo secret to enable).

## Status

This is a v0 prototype. Production-grade hardening (auth, multi-tenant isolation enforcement, scheduled refresh, observability) is intentionally deferred. See spec §8 "Out of scope".
