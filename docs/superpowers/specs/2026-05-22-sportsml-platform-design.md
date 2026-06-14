# sportsml — Platform Design

> Date: 2026-05-22
> Status: Approved design; ready for implementation plan
> Scope: POC covering subsystems #1 (Data Foundation / Ontology) and #2 (Player Evaluation Engine)

## 0. Premise

A platform — not a service — that gives professional and college sports organizations a Foundry-style data substrate plus tunable evaluation tooling. Teams bring their own IP (model configs, philosophies, custom transforms); the platform provides the rails: ingestion, typed object layer, declarative transforms, model templates, dashboards, governance.

Positioned to compete in the same conceptual space as Palantir Foundry, Snowflake, and Databricks — but verticalized for sports analytics. White-glove implementation up front; self-serve as customer technical maturity grows.

POC focuses on the NBA. Architecture is sport-agnostic from day one to preserve the full TAM (NFL, MLB, NHL, MLS, NCAA football/basketball, EuroLeague, G-League).

## 1. Constraints & Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Data scope | 5 NBA seasons (2019-20 → 2023-24) + current NCAA D1 season | Min depth for credible RAPM + prospect translation training |
| Data sources | API-only; no scrapes | `nba_api` (stats.nba.com), CollegeBasketballData.com API |
| Deployment model | Multi-tenant architecture, single-tenant POC deploy | Lets us claim both deployment stories; doesn't force BYOC work yet |
| Modeling UX | Templates + auto-generated slider UI (path to full SDK later) | Non-technical first wave; technical staff later |
| Tech stack | Python + FastAPI + DuckDB → MotherDuck + Supabase (Postgres) + Next.js/TS + shadcn/ui + Dagster | DuckDB for analytics, Supabase for app state, Dagster for canonical data |
| Architectural style | Foundry-faithful backbone, Palantir-flavored UI vocabulary | "Data product by nerds"; no sport-themed cute names |
| Sport-pluggable abstraction | First-class from day one | ~10% structural cost now, pays back at sport #2 |
| Transaction Modeling | **Cut from POC** | No free contracts API; revisit once paid feed integrated |

## 2. Architecture (6 layers)

```
[1] Workbench  (Next.js + TS + shadcn)
       │  HTTP / JSON
       ▼
[2] Platform API  (FastAPI, Python)
       │  imports
       ▼
[3] Core  (Python: sportsml.core)
       │  imports
       ▼
[4] Sport Plugins  (Python: sportsml.sports.basketball.nba, .ncaa)
       │
       ▼
[5] Storage  (DuckDB + Parquet · Supabase/Postgres)
       │
       ▼
[6] Ingestion  (Dagster assets per source)
```

Cross-cutting on every row, every API call, every model config:
- `tenant_id` — multi-tenancy (RLS in Postgres; per-tenant DuckDB schemas)
- `sport_id` — sport-pluggable dimension (`basketball.nba`, `basketball.ncaa`, ...)

### 2.1 Workbench (Layer 1)

Next.js 14 + TypeScript + Tailwind + shadcn/ui. Dark theme by default. Left-rail navigation:

```
Data
  Ontology
  Datasets
  Models
Apps
  Lineup Analysis      ← POC hero
  Prospect Translation ← POC secondary
Admin
  Tenants
  Audit
  Settings
```

Sport-specific vocabulary appears only inside data (Object Type names like `Possession`, `Shot`), never in chrome.

### 2.2 Platform API (Layer 2)

FastAPI, Python 3.12. Pydantic schemas mirror Ontology types. Every request carries a tenant-scoped JWT (issued by Supabase Auth). OpenAPI spec drives auto-generated TypeScript client for the Workbench.

Endpoints:
- `GET /ontology/types` — list Object Types for current sport
- `GET /ontology/{type}/{id}` — fetch instance + links
- `GET /datasets` — list materialized assets with freshness
- `GET /datasets/{id}/sample` — paged sample rows
- `GET /models` — list ModelTemplates
- `GET /models/{id}/schema` — JSONSchema for config UI
- `POST /models/{id}/runs` — submit a run with config
- `GET /models/{id}/runs/{run_id}` — run status + output dataset pointer
- `GET /models/{id}/runs/{run_id}/output` — paged output rows

### 2.3 Core (Layer 3) — `sportsml.core`

Sport-agnostic abstractions. The TAM-defining package.

```
sportsml/core/
  ontology/        # ObjectType, Link, Property — base classes
  transforms/      # Wrapper around Dagster @asset patterns (mostly thin)
  models/          # ModelTemplate ABC, ConfigSchema, ModelRun, TenantContext
  apps/            # App ABC, AppSpec, BoardSpec, PanelSpec
  tenancy/         # TenantContext, sport+tenant scoping, output router
```

### 2.4 Sport Plugins (Layer 4)

Each sport plugin is a self-contained Python package that exports:
- Object Types (extending `core.ontology` base classes)
- Dagster `Definitions` (its assets, partitions, IO managers)
- Pydantic config schemas
- `ModelTemplate` subclasses
- `App` subclasses (AppSpecs)

POC builds out fully:
- `sportsml.sports.basketball.nba`
- `sportsml.sports.basketball.ncaa` (subset — only what prospect translation needs)

Stubs (interface declared, implementation empty):
- `sportsml.sports.basketball.euroleague`
- `sportsml.sports.football.nfl`
- `sportsml.sports.baseball.mlb`
- `sportsml.sports.hockey.nhl`

### 2.5 Storage (Layer 5)

Two databases, one direction of sync.

**DuckDB (→ MotherDuck for cloud / multi-tenant)** — analytics workload.
- Hive-partitioned Parquet files on disk
- DuckDB views register the Parquet trees as queryable tables
- Same code runs against embedded DuckDB in dev and MotherDuck in cloud

Directory layout:
```
data/
  core/
    leagues/*.parquet
    seasons/*.parquet
    teams/*.parquet
    players/*.parquet
    games/sport=basketball/league=nba/season=2023-24/*.parquet
    games/sport=basketball/league=ncaa/season=2023-24/*.parquet
  basketball/
    nba/
      possessions/season=2023-24/*.parquet
      shots/season=2023-24/*.parquet
      lineups/season=2023-24/*.parquet
      lineup_stints/season=2023-24/*.parquet
      draft_prospects/draft_year=2024/*.parquet
    ncaa/
      player_seasons/season=2023-24/*.parquet
      team_seasons/season=2023-24/*.parquet
```

**Supabase / Postgres** — application state. RLS-enforced tenant isolation.
- `tenants`, `users` (extends `auth.users`)
- `model_configs` (user-saved configs, content-hashed)
- `model_runs` (run_id, config_hash, started_at, status, duration_s, row_count, output_dataset)
- `app_states` (saved views per app per user)
- `audit_log`

Tenant model:
- Canonical public data lives in DuckDB without `tenant_id` (shared across all tenants — it's the same NBA data)
- Per-tenant data: model configs in Postgres; model run outputs in DuckDB under `tenant_{id}.<dataset>` schemas
- RLS policy on every Postgres table: `tenant_id = auth.jwt()->>'tenant_id'`

### 2.6 Ingestion (Layer 6) — Dagster

All ingestion + ontology + feature transforms are Dagster assets. Dagit is the internal admin/debug UI; not surfaced to Workbench users in the POC.

Source assets (API-only):
- `nba_api`: PBP, box scores, shot charts, team rosters, draft data
- `CollegeBasketballData`: NCAA D1 player & team season stats

Each sport plugin contributes a Dagster code location loaded into one Definitions tree.

## 3. Ontology

16 Object Types in POC. Sport-agnostic base in `core.ontology`; concrete extensions in sport plugins.

### 3.1 Core (sport-agnostic)

| ObjectType | Key properties | Notes |
|---|---|---|
| `League` | id, sport_id, name, country, level | e.g., NBA, NCAA-D1 |
| `Season` | id, league_id, name, start_date, end_date | |
| `Team` | id, league_id, name, abbreviation, city | |
| `Player` | id, sport_id, full_name, birth_date, height_cm, weight_kg, position | `position` is a free-form string; convention is sport-specific (NBA: PG/SG/SF/PF/C; NFL: QB/RB/WR/...). No schema change to add a sport. |
| `Game` | id, season_id, date, home_team_id, away_team_id, home_score, away_score | |
| `PlayerGame` | player_id, game_id, minutes, plus_minus | Minimal core columns; sport plugins add columns via plugin-owned sibling tables (e.g., `basketball.nba.player_game_box`) joined on `(player_id, game_id)`. Core remains stable; plugin owns its stats. |

### 3.2 Basketball NBA extensions

| ObjectType | Key properties |
|---|---|
| `Possession` (extends Event) | game_id, period, game_clock, offense_team_id, defense_team_id, outcome, points_scored, possession_seconds |
| `Shot` (extends Event) | possession_id, shooter_id, x, y, distance_ft, shot_type, made, shot_value, assisted_by_id |
| `Lineup` | team_id, player_ids[5] (canonical sorted hash) |
| `LineupStint` | game_id, lineup_id, start_time, end_time, possessions_played, points_for, points_against |
| `Substitution` (extends Event) | game_id, period, game_clock, player_in_id, player_out_id |
| `DraftProspect` | player_id, draft_year, last_league_id, last_team_id, mock_position?, scout_grade? | `mock_position` / `scout_grade` are optional, nullable; populated from tenant-owned seed data when available, not ingested from public APIs |

### 3.3 Basketball NCAA extensions

| ObjectType | Key properties |
|---|---|
| `NCAAGame` (extends Game) | + conference_id, neutral_site, tournament_id |
| `NCAAPlayerSeason` | player_id, season_id, team_id, gp, mpg, usage, ts%, ast%, trb%, stl%, blk% (and more) |
| `NCAATeamSeason` | team_id, season_id, conference, schedule_strength, kenpom_adjO?, kenpom_adjD? |

### 3.4 Links (relationships)

- `Player` belongs_to `Team` (current roster)
- `Player` has_many `PlayerGame`
- `Game` has_two `Team` (home + away)
- `Possession` belongs_to `Game`; has_many `Shot`
- `Shot` belongs_to `Possession`, `Player` (shooter), optional `Player` (assist)
- `Lineup` has_five `Player`
- `LineupStint` belongs_to `Lineup` and `Game`
- `DraftProspect` has_one `NCAAPlayerSeason` (current)

## 4. Transforms (Dagster DAG)

Four logical layers. All implemented as Dagster `@asset`s with `StaticPartitionsDefinition` by season (and `DynamicPartitionsDefinition` for per-run outputs).

### 4.1 Layer 0 — Raw (source assets)

Written by ingestion adapters; one source asset per endpoint.

- `raw.nba.play_by_play` (~1.3M rows / 5 seasons)
- `raw.nba.box_scores`
- `raw.nba.shot_chart`
- `raw.nba.team_roster`
- `raw.nba.draft_history`
- `raw.ncaa.player_seasons`
- `raw.ncaa.team_seasons`

### 4.2 Layer 1 — Ontology (typed assets)

Cleaned, deduped, schema-validated against Object Types. Materialized as Parquet.

- `core.players`, `core.teams`, `core.games`
- `basketball.nba.possessions`, `.shots`, `.substitutions`, `.lineups`, `.lineup_stints`
- `basketball.nba.draft_prospects`
- `basketball.ncaa.player_seasons`, `.team_seasons`

### 4.3 Layer 2 — Features (model inputs)

Aggregations and joins consumed by Models.

- `features.nba.player_season_stats` (per-36, advanced)
- `features.nba.lineup_season_stats` (net rating, sample counts)
- `features.nba.on_off_stints` (RAPM design matrix: one row per stint, player columns + outcome)
- `features.nba.shot_quality` (xPPS by location bin)
- `features.nba.prospect_features` (NCAA → projected NBA inputs)

### 4.4 Layer 3 — Outputs (per-tenant, model-written)

Written by FastAPI when a user triggers a Model run, **not** by Dagster.

- `tenant_{id}.lineup_net_rating` — one row per scored lineup per run
- `tenant_{id}.prospect_projections` — one row per prospect per run

### 4.5 Non-trivial transforms (flagged for risk)

1. `build_possessions` — segment PBP into possessions. Edge cases: quarter end, technical FTs, jump balls. Use `pbpstats` library where possible. Golden-record tests required.
2. `build_lineup_stints` — derive continuous spans of 5-player lineups from PBP + substitution events. Game-state machine. Subtle; golden-record tests covering OT, ejections, end-of-quarter sub patterns.
3. `build_on_off_stints` — convert stints to RAPM design matrix. DuckDB-built, scipy.sparse-friendly.

## 5. Models Framework

### 5.1 `ModelTemplate` ABC

```python
class ModelTemplate(ABC):
    name: str                       # "lineup_net_rating"
    version: str                    # semver; bumped on breaking config change
    sport_id: str                   # routing
    config_schema: type[BaseModel]  # drives auto-generated UI via JSONSchema
    output_schema: type[BaseModel]  # typed output rows

    @abstractmethod
    def run(self, config: BaseModel, ctx: TenantContext) -> ModelRunOutput:
        """Pure function: config + context -> output. No globals."""
```

### 5.2 Config → UI auto-generation

Pydantic field annotations map directly to UI controls. Frontend uses `@rjsf/core` with a custom shadcn theme. Adding a knob = adding a Pydantic `Field`; zero frontend code.

| Pydantic | UI control |
|---|---|
| `int` + `ge` + `le` | range slider |
| `float` + `ge` + `le` | range slider with decimals |
| `bool` | toggle |
| `list[str]` + enum | multi-select |
| `Literal[...]` | segmented control |
| `description=` | helper tooltip |

### 5.3 Models shipped in POC

#### Primary: `lineup_net_rating` (basketball.nba)

Bayesian-shrunk RAPM with matchup adjustment. Scores every observed 5-man lineup, projects unseen ones, returns confidence bands.

Tunable knobs (Pydantic config):
- `seasons: list[str]` — training seasons
- `min_possessions: int` (50–2000, default 200)
- `rapm_lambda: float` (10–2000, default 200) — L2 regularization strength
- `prior_weight: float` (0–1, default 0.5) — blend toward team prior
- `three_point_emphasis: float` (0.5–3, default 1.0) — feature weight multiplier
- `matchup_adjusted: bool` (default true)
- `position_constraints: bool` (default false) — enforce 1xPG, ≥1xbig

Output schema: `(lineup_id, projected_net, ci_lo, ci_hi, sample_n)`.

#### Secondary: `prospect_translation` (basketball.nba)

NCAA per-40 → projected NBA per-36 stats with confidence bands. Trained on historical draft cohorts via `nba_api` draft history.

Tunable knobs:
- `training_cohorts: list[int]` — which draft years to learn translation factors from
- `age_curve: Literal["young", "standard", "aggressive"]`
- `strength_of_schedule_weight: float` (0–1, default 0.5)
- `shooting_emphasis: float` (0.5–3, default 1.0)
- `min_minutes_threshold: int` (default 500)

Output schema: `(prospect_id, proj_per36_pts, proj_per36_reb, ..., ci_lo, ci_hi, comp_player_ids[])`.

### 5.4 Run lifecycle

```
POST /models/lineup_net_rating/runs
  body: { config: {...slider values...}, label: "custom v3" }
  → 202 Accepted, run_id

GET /models/lineup_net_rating/runs/{run_id}
  → { status, duration_s, output_dataset, row_count }

GET /models/lineup_net_rating/runs/{run_id}/output?limit=100&sort=-projected_net
  → rows from tenant_X.lineup_net_rating
```

Properties:
- Config validated server-side against schema before run queued
- Run record persisted in Postgres (run_id, config_hash, status, duration, output pointer)
- Output rows persisted in DuckDB under `tenant_{id}.<model_name>`
- Identical config_hash → returns the cached run_id (no recompute)

**Model composition** is expressed as a special Pydantic field type `RunRef[ModelName]` in a downstream config. When the platform resolves a `RunRef`, it looks up the referenced run's output dataset and exposes it to the dependent model's `run()` method via `ctx.runref(field_name)`. The POC framework supports this primitive but ships no cross-app UI that exercises it.

## 6. Apps

### 6.1 `App` ABC

```python
class App(ABC):
    id: str                  # "lineup_analysis"
    sport_id: str            # "basketball.nba"
    models_used: list[str]
    layout: AppLayout        # declarative panel grid
```

Each sport plugin exports its Apps. Workbench shell is generic — it renders whatever App is selected without sport-aware code.

### 6.2 Apps shipped in POC

#### Lineup Analysis (hero, polished)

Left config panel (auto-generated sliders for `LineupNetRatingConfig`) + tabbed result area:
- Top Lineups table (sorted by projected net rating, with sample sizes and CIs)
- 2-Man Synergy heatmap
- Projection vs Observed chart (shrinkage made visible)
- vs Opponent matchup tab

Demo moment: drag `three_point_emphasis` from 1.0 → 2.0, click Run, table re-sorts in ~12s.

#### Prospect Translation (functional)

Left config panel (auto-generated sliders for `ProspectTranslationConfig`) + result area:
- Current draft class table with projected NBA per-36 lines
- Per-prospect detail panel with comparables and CI bands
- "What if" toggle to re-project with different config

### 6.3 Cross-app composition (deferred surface)

Composition between models (e.g., prospect translation referencing a tuned Lineup model run for fit scoring) is supported by the framework via explicit `run_id` references in config schemas, but no cross-app UI is shipped in the POC. The single demonstrated composition story is comparing saved runs side-by-side within Lineup Analysis.

## 7. Tenant Model & Auth

- Supabase Auth: email/password for POC; `tenant_id` is injected into the JWT as a custom claim via a Supabase Auth Hook (or stored in `app_metadata` and surfaced via the JWT) — the user record in `public.users` carries `tenant_id`, and the hook writes it into the access token at sign-in
- Postgres tables RLS-policied on `tenant_id = (auth.jwt() ->> 'tenant_id')::uuid`
- DuckDB tenant-scoped outputs written to `tenant_{id}.<dataset>` schemas
- The FastAPI layer enforces tenant scoping for DuckDB calls (DuckDB has no built-in RLS) by deriving the schema prefix from the JWT's tenant_id on every request
- Canonical public data (NBA / NCAA) is shared across tenants — no `tenant_id` on those rows
- One demo tenant seeded for POC

## 8. POC Scope Summary

### In scope

- Monorepo at `/sportsml` with `core` + `sports/basketball/{nba,ncaa}` fully built; other sports as empty interface stubs
- Dagster project with all ingestion + ontology + feature assets, partitioned by season
- 5 NBA seasons ingested via `nba_api`
- Current NCAA D1 season via CollegeBasketballData API
- 2 model templates: `lineup_net_rating` (polished), `prospect_translation` (functional)
- 2 Apps: Lineup Analysis (polished), Prospect Translation (functional)
- Ontology browser + Datasets list in Workbench
- Multi-tenant schema with RLS; 1 demo tenant seeded
- Supabase auth + tenant_id JWT claim
- FastAPI service with OpenAPI spec; auto-generated TS client
- Local dev via docker-compose: dagster-webserver, dagster-daemon, fastapi, next.js, postgres
- `make demo` target that brings everything up and seeds data
- Recorded 5-min demo walkthrough

### Out of scope

- Transaction Modeling (no free contracts API; revisit post-POC)
- Code Workbooks / Jupyter SDK layer
- Pipeline Builder UI
- Workbench Lineage tab (use Dagit)
- Custom Object Type creation by users
- Python client SDK for tenants
- Production deployment
- Scheduled / live refresh (one-time backfill in POC)
- SSO / role hierarchies
- Tracking data ingestion (real or synthetic)
- EuroLeague / G-League adapters
- NFL / MLB / NHL implementations (empty stubs only)
- Audit log surfaces
- Cost tracking / observability dashboards

### Cut lines (drop in this order if time tight)

1. Prospect Translation app polish → keep functional, plain table output
2. Ontology browser → replace with schemas-as-JSON view
3. Datasets freshness indicators → plain list
4. Tenant switcher → hard-code single demo tenant
5. 5 seasons → 3 seasons
6. Auto-generated TS client → hand-write the ~8 API calls used

Hero (Lineup Analysis) and core data plumbing are never cut.

## 9. Success Criteria

1. Demo loop works end-to-end: open Lineup Analysis → drag `three_point_emphasis` from 1.0 → 2.0 → click Run → table re-sorts in <30s with updated projections
2. Prospect Translation produces credible per-36 projections for the current draft class with confidence bands
3. Ontology browser shows every Object Type with sample rows; clicking a Player surfaces all linked data (games, lineups)
4. Sport plugin pattern is real: adding a 4th model under `basketball.nba` requires no changes outside that package
5. Reproducibility: same config hash → identical output, cached, no recompute
6. Recorded 5-min demo video runnable on any laptop

## 10. Testing Strategy

- **Unit tests** for transforms — golden-record tests with small input fixtures (especially `build_possessions`, `build_lineup_stints`, `build_on_off_stints`)
- **Unit tests** for models — deterministic outputs given fixed random seeds
- **Integration tests** for ingestion — recorded API responses via VCR / pytest-recording
- **API contract tests** — validate FastAPI responses against OpenAPI spec
- **E2E test** — Playwright recording the slider → run → result flow
- **Coverage target**: 80% unit + integration combined

## 11. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| `nba_api` rate limiting | Backoff + cache all responses to local Parquet; one-time backfill, not live |
| Possession / lineup-stint edge cases | Lean on `pbpstats` library; ship golden-record tests covering OT, technical FTs, jump balls, ejections |
| RAPM compute on laptop | DuckDB-built design matrix + `scipy.sparse` regression; budget <30s per run on 270K rows |
| NCAA data quality / coverage | CollegeBasketballData API as primary; document fallback to manual seed file if API rate-limited |
| Auto-generated forms feeling generic | Custom slider + result panel polish for hero; secondary apps get RJSF defaults |
| Sport-pluggable abstraction overhead | Accept ~10% structural cost upfront; pays back at sport #2 |

## 12. Phasing (rough — solo builder)

| Phase | Scope | Duration |
|---|---|---|
| 1 | Data foundation — repo scaffold, Dagster project, NBA + NCAA ingestion adapters, raw → ontology transforms | ~2 wk |
| 2 | Features + Model framework — feature transforms, ModelTemplate base, `lineup_net_rating` with shrinkage RAPM | ~2 wk |
| 3 | API + Workbench shell — FastAPI service, Supabase auth, Next.js shell, Ontology/Datasets/Models pages | ~1.5 wk |
| 4 | Apps — Lineup Analysis hero (full polish), Prospect Translation (functional) | ~1.5 wk |
| 5 | Polish + demo — bug fixes, demo flow scripting, recorded walkthrough, README + setup docs | ~0.5 wk |

Total: roughly **7 weeks** of focused work for a solo builder. Phases 2-4 have parallel-able components.

## 13. Repository Layout (target)

```
sportsml/
  README.md
  Makefile                          # make demo, make ingest, make test
  docker-compose.yml
  pyproject.toml
  pnpm-workspace.yaml

  packages/
    core/                           # sportsml.core
      sportsml/core/
        ontology/
        transforms/
        models/
        apps/
        tenancy/
      tests/
    sports/
      basketball/
        nba/                        # sportsml.sports.basketball.nba
          sportsml/sports/basketball/nba/
            ontology/               # ObjectType extensions
            ingestion/              # Dagster source assets (nba_api)
            transforms/             # Dagster ontology + feature assets
            models/                 # lineup_net_rating, prospect_translation
            apps/                   # LineupAnalysisApp, ProspectTranslationApp
          tests/
        ncaa/                       # sportsml.sports.basketball.ncaa
          sportsml/sports/basketball/ncaa/
            ontology/
            ingestion/              # CollegeBasketballData adapter
            transforms/
          tests/
        euroleague/                 # stub
      football/
        nfl/                        # stub
      baseball/
        mlb/                        # stub
      hockey/
        nhl/                        # stub
    api/                            # FastAPI service
      sportsml_api/
      tests/
    workbench/                      # Next.js app
      app/
      components/
      lib/

  dagster/                          # Dagster project loader
    workspace.yaml                  # references each sport plugin code location
    sportsml_dagster/__init__.py

  data/                             # Hive-partitioned Parquet (gitignored)
    .gitkeep

  docs/
    superpowers/
      specs/
        2026-05-22-sportsml-platform-design.md   ← this doc
```

## 14. Open Questions Deferred to Implementation

- Exact RAPM regression library (statsmodels vs. scikit-learn `Ridge` vs. custom)
- Whether to use Polars or DuckDB-only for transforms (lean DuckDB-only)
- Specific shadcn slider customization vs. RJSF default
- Demo tenant seed strategy (one fictional team or one real team's roster for the screen recording)
- Exact directory layout under `data/` when MotherDuck-backed (does it change?)
