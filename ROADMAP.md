# Roadmap

> Auto-generated from GitHub Issues. Run `/roadmap` to refresh.

**Vision:** Palantir for pro / semi-pro sports — an all-in-one data ops + advanced analytics platform that lets front offices money-ball the NBA (and beyond).

---

## Milestones

### v0.1 — Foundation Hardening

Make the platform tenant-safe, observable, and ops-ready before adding more features.

- [ ] #1 feat: Supabase Auth + multi-tenant RLS enforcement _(needs plan)_
- [ ] #2 feat: migrate run store SQLite -> Supabase Postgres
- [ ] #3 feat: platform observability (logs, metrics, traces) _(needs plan)_
- [ ] #4 feat: admin UI with role-based access and audit log
- [ ] #5 feat: CI/CD pipeline + 80% test coverage gate

### v0.2 — Live NBA Data

Always-fresh NBA data ops: scheduled ingestion, backfill, paid feeds, lineage.

- [ ] #6 feat: Dagster schedules + sensors for live NBA refresh
- [ ] #7 feat: incremental ingestion pipeline (no full reloads)
- [ ] #8 feat: historical NBA backfill (10+ seasons, full PBP + shots)
- [ ] #9 feat: paid feed adapter framework (Synergy, Second Spectrum, Sportradar) _(needs plan)_
- [ ] #10 feat: data lineage and freshness UI

### v0.3 — NBA Analytics Suite

Expand the moneyball toolkit: trades, aging, draft, cap, roster, matchups.

- [ ] #11 feat: trade analyzer app (cap + on-court fit) _(needs plan)_
- [ ] #12 feat: player aging-curve projection model _(needs plan)_
- [ ] #13 feat: NCAA draft prospect translation (complete scaffold)
- [ ] #14 feat: salary cap and contract valuation model
- [ ] #15 feat: roster construction optimizer _(needs plan)_
- [ ] #16 feat: opponent-adjusted matchup analyzer

### v0.4 — Analyst Workbench

Empower team analysts: code workbooks, custom apps, dashboards, experiment tracking.

- [ ] #17 feat: Code Workbooks - Jupyter-style analyst SDK _(needs plan)_
- [ ] #18 feat: custom app builder UI _(needs plan)_
- [ ] #19 feat: saved queries and dashboards
- [ ] #20 feat: notebook -> app promotion flow
- [ ] #21 feat: versioned model artifacts and experiment tracking

### v0.5 — Sport Expansion

Multi-sport platform: NCAA hoops, NFL, MLB, WNBA/G-League, cross-sport ontology.

- [ ] #22 feat: NCAA basketball plugin (complete)
- [ ] #23 feat: NFL plugin (EPA + drive model) _(needs plan)_
- [ ] #24 feat: MLB plugin (Statcast-driven) _(needs plan)_
- [ ] #25 feat: WNBA and G-League plugins
- [ ] #26 feat: cross-sport ontology refinements _(needs plan)_

### v1.0 — GTM & Launch

Sellable product: onboarding, billing, docs, demo tenants, SOC2, SLAs.

- [ ] #27 feat: tenant onboarding and provisioning flow
- [ ] #28 feat: Stripe billing and subscription management
- [ ] #29 feat: public docs site
- [ ] #30 feat: demo tenants and sandbox environments
- [ ] #31 feat: SOC2 prep and compliance tooling _(needs plan)_
- [ ] #32 feat: SLAs, support tooling, public status page

---

## Labels

| Category | Labels                                                                                |
| -------- | ------------------------------------------------------------------------------------- |
| Type     | type:feature, type:bug, type:refactor, type:research, type:chore                      |
| Priority | priority:high, priority:medium, priority:low                                          |
| Status   | status:needs-plan, status:in-progress, status:blocked, status:ready                   |
| Area     | area:api, area:core, area:sports, area:workbench, area:dagster, area:infra, area:docs |
