# sportsml.sports.basketball.ncaa — stub

This package will provide:

- **Ontology extensions**: `NCAAGame` (adds conference_id, neutral_site, tournament_id), `NCAAPlayerSeason`, `NCAATeamSeason`.
- **Ingestion**: CollegeBasketballData.com API source assets — `raw_ncaa_player_seasons`, `raw_ncaa_team_seasons`.
- **Transforms**: clean + dedup feeds into typed `core.player_season`, `core.team_season` extensions.
- **Models**: `prospect_translation` (NCAA per-40 → NBA per-36 projections with confidence bands), trained on historical draft cohorts via `nba_api`.
- **Apps**: `prospect_translation` app — config sliders + draft-class projection table + per-prospect detail panel.

Not wired into the Dagster Definitions tree in v0; only the NBA plugin is loaded. To enable, add the package's ingestion and transforms modules to `SPORT_ASSET_MODULES` in `dagster_project/sportsml_dagster/__init__.py`, and import the package from `sportsml_api.main._register_sport_plugins`.
