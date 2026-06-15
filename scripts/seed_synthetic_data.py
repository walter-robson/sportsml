"""Seed synthetic on_off_stints data so the demo loop works without nba_api.

The v0 demo depends on `features.nba.on_off_stints` being populated. The
real ingestion goes through Dagster + nba_api; when stats.nba.com is
unreachable (rate-limited, network blocked, etc.), this script writes a
plausible synthetic Parquet file in the schema the model expects.

This is the v0 escape hatch — production teams plug in their licensed
feeds; for local demos we fall back to synthetic.

Usage:
    python scripts/seed_synthetic_data.py
"""

from __future__ import annotations

import hashlib
import random
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
OUT_FILE = DATA_DIR / "features" / "nba" / "on_off_stints.parquet"

# Real 2023-24 NBA roster snapshots — used so player_ids resolve to real names
# downstream if the Workbench cross-references stats.nba.com later.
ROSTERS: dict[str, dict[str, list[str]]] = {
    "1610612738": {  # BOS Celtics
        "name": "BOS",
        "core": [
            "1628369",
            "1627759",
            "201950",
            "1628401",
            "204001",
        ],  # Tatum/Brown/Holiday/White/Porzingis
        "bench": [
            "1630202",
            "201143",
            "1630573",
            "1628378",
            "1629057",
        ],  # Pritchard/Horford/Hauser/Kornet/Brissett
    },
    "1610612744": {  # GSW Warriors
        "name": "GSW",
        "core": [
            "201939",
            "2738",
            "203952",
            "203110",
            "1626172",
        ],  # Curry/Thompson/Wiggins/Green/Looney
        "bench": ["1628395", "1628384", "1630228", "1641706", "1630225"],
    },
    "1610612747": {  # LAL Lakers
        "name": "LAL",
        "core": [
            "2544",
            "203076",
            "1627833",
            "1626156",
            "203497",
        ],  # LeBron/AD/Reaves/D'Angelo Russell/Rui
        "bench": ["1630559", "203944", "1630224", "1628401", "1629680"],
    },
    "1610612743": {  # DEN Nuggets
        "name": "DEN",
        "core": [
            "203999",
            "1627750",
            "1628378",
            "1628960",
            "203914",
        ],  # Jokic/Murray/MPJ/KCP/Aaron Gordon
        "bench": ["1630168", "1630174", "1629019", "1630268", "1629057"],
    },
    "1610612762": {  # OKC Thunder
        "name": "OKC",
        "core": [
            "1628983",
            "1628973",
            "1629029",
            "1641705",
            "1630167",
        ],  # SGA/Dort/Giddey/Holmgren/JDub
        "bench": ["1641709", "1630244", "1630238", "1628988", "1641710"],
    },
    "1610612749": {  # MIL Bucks
        "name": "MIL",
        "core": [
            "203507",
            "201142",
            "1628978",
            "203114",
            "1629680",
        ],  # Giannis/Dame/Brook Lopez/Khris/Beasley
        "bench": ["1630193", "1641754", "1630174", "204022", "203501"],
    },
}


def _hash_id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:12]


def _make_stint_row(
    rng: random.Random,
    game_id: str,
    stint_idx: int,
    off_team: str,
    def_team: str,
    off_players: list[str],
    def_players: list[str],
    season: str,
    quality_bias: float,
) -> dict[str, object]:
    """Generate one stint row.

    quality_bias shifts the expected margin in favor of the offense; we use it
    to encode team strength + lineup synergy so RAPM has signal to recover.
    """
    possessions = rng.randint(4, 16)
    expected_margin = quality_bias + rng.gauss(0.0, 12.0)
    pts_total = max(possessions + rng.randint(-2, 4), 0)
    pts_for = max(0, int(round(pts_total * 0.5 + expected_margin * possessions / 200.0)))
    pts_against = max(0, pts_total - pts_for)
    return {
        "stint_id": f"{game_id}_{stint_idx:02d}",
        "game_id": game_id,
        "off_team_id": off_team,
        "def_team_id": def_team,
        "off_player_ids": list(off_players),
        "def_player_ids": list(def_players),
        "possessions": possessions,
        "points_for": pts_for,
        "points_against": pts_against,
        "point_margin_per_100": (pts_for - pts_against) / max(possessions, 1) * 100.0,
        "season": season,
    }


def _pick_lineup(rng: random.Random, roster: dict[str, list[str]]) -> list[str]:
    """Pick a 5-player lineup biased toward the core 5 with bench rotation."""
    n_core = rng.choices([5, 4, 3, 2], weights=[5, 3, 2, 1])[0]
    bench_count = 5 - n_core
    return rng.sample(roster["core"], k=n_core) + rng.sample(roster["bench"], k=bench_count)


# Latent player strengths. The RAPM model should approximately recover these
# from the synthetic stints — that's how we know the demo loop is wired.
LATENT_STRENGTHS: dict[str, float] = {
    "1628369": 6.5,  # Tatum
    "1627759": 4.8,  # Brown
    "201950": 3.7,  # Holiday
    "1628401": 2.1,  # White
    "204001": 3.4,  # Porzingis
    "201939": 7.2,  # Curry
    "203507": 7.8,  # Giannis
    "203999": 8.1,  # Jokic
    "1628983": 6.9,  # SGA
    "2544": 5.6,  # LeBron
    "203076": 5.2,  # Davis
}


def _lineup_quality(players: list[str]) -> float:
    return sum(LATENT_STRENGTHS.get(p, 0.0) for p in players)


def generate(season: str = "2023-24", n_games_per_pair: int = 4, rng_seed: int = 7) -> pd.DataFrame:
    rng = random.Random(rng_seed)
    rows: list[dict[str, object]] = []
    team_ids = list(ROSTERS.keys())
    game_counter = 1
    for i, home in enumerate(team_ids):
        for j, away in enumerate(team_ids):
            if i == j:
                continue
            for _ in range(n_games_per_pair):
                game_id = f"00223{game_counter:05d}"
                game_counter += 1
                home_quality_total = 0.0
                # A typical game has ~22-26 distinct stints per team.
                n_stints = rng.randint(20, 28)
                for s in range(n_stints):
                    off_team = home if s % 2 == 0 else away
                    def_team = away if s % 2 == 0 else home
                    off_players = _pick_lineup(rng, ROSTERS[off_team])
                    def_players = _pick_lineup(rng, ROSTERS[def_team])
                    quality_bias = _lineup_quality(off_players) - _lineup_quality(def_players)
                    home_quality_total += quality_bias if off_team == home else -quality_bias
                    rows.append(
                        _make_stint_row(
                            rng,
                            game_id,
                            s,
                            off_team,
                            def_team,
                            off_players,
                            def_players,
                            season,
                            quality_bias,
                        )
                    )
    return pd.DataFrame(rows)


def main() -> None:
    df = generate()
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_FILE, index=False)
    print(f"Wrote {len(df):,} stints to {OUT_FILE}")
    print(f"  unique games: {df['game_id'].nunique()}")
    print(f"  unique teams: {df[['off_team_id']].nunique().iloc[0]}")
    n_unique_off_lineups = df.assign(_l=df["off_player_ids"].map(lambda x: "|".join(sorted(x))))[
        "_l"
    ].nunique()
    print(f"  unique offensive lineups: {n_unique_off_lineups}")


if __name__ == "__main__":
    main()
