// Mock API layer — returns realistic-looking fake data so the UI works without the
// FastAPI backend. Must obey the same TypeScript contract as `api.ts`.

import type {
  AppDescriptor,
  Dataset,
  JsonSchema,
  LineupConfig,
  LineupRow,
  ModelTemplate,
  ObjectType,
  RunDetail,
  RunOutput,
  RunSubmitResponse,
  SynergyCell,
  SynergyMatrix,
} from './types';

const PLAYERS_BOS = [
  'Tatum',
  'Brown',
  'Holiday',
  'White',
  'Porzingis',
  'Horford',
  'Pritchard',
  'Hauser',
  'Kornet',
  'Brissett',
] as const;

// Deterministic seed-ish pseudo-random based on string config so the table changes
// on each run in a predictable, demo-able way.
function hash(input: string): number {
  let h = 2166136261;
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function rand(seed: number): () => number {
  let s = seed || 1;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 0xffffffff;
  };
}

const BASE_LINEUPS: ReadonlyArray<ReadonlyArray<string>> = [
  ['Tatum', 'Brown', 'Holiday', 'White', 'Porzingis'],
  ['Tatum', 'Brown', 'Holiday', 'White', 'Horford'],
  ['Tatum', 'Brown', 'Pritchard', 'White', 'Porzingis'],
  ['Tatum', 'Brown', 'Holiday', 'Hauser', 'Porzingis'],
  ['Tatum', 'Brown', 'Holiday', 'White', 'Kornet'],
  ['Tatum', 'Pritchard', 'Holiday', 'Hauser', 'Horford'],
  ['Tatum', 'Brown', 'Pritchard', 'Hauser', 'Kornet'],
  ['Brown', 'Holiday', 'White', 'Hauser', 'Porzingis'],
  ['Tatum', 'Brown', 'Pritchard', 'White', 'Horford'],
  ['Tatum', 'Holiday', 'White', 'Hauser', 'Porzingis'],
  ['Tatum', 'Brown', 'Holiday', 'Brissett', 'Porzingis'],
  ['Brown', 'Pritchard', 'White', 'Hauser', 'Horford'],
  ['Tatum', 'Pritchard', 'White', 'Hauser', 'Kornet'],
  ['Brown', 'Holiday', 'Pritchard', 'Brissett', 'Kornet'],
];

const BASE_OBSERVED = [16.2, 13.1, 9.4, 7.8, 5.0, 2.1, -2.8, 8.4, 6.2, 4.1, 3.5, 0.4, -1.2, -4.0];
const BASE_SAMPLE_N = [1247, 892, 318, 241, 156, 89, 67, 540, 412, 220, 184, 130, 72, 50];

export function mockListOntologyTypes(): ReadonlyArray<ObjectType> {
  return [
    { id: 'core.player', name: 'Player', sport_id: 'core', count: 4823 },
    { id: 'core.team', name: 'Team', sport_id: 'core', count: 30 },
    { id: 'core.game', name: 'Game', sport_id: 'core', count: 6150 },
    { id: 'basketball.nba.possession', name: 'Possession', sport_id: 'basketball.nba', count: 1318472 },
    { id: 'basketball.nba.shot', name: 'Shot', sport_id: 'basketball.nba', count: 1102845 },
    { id: 'basketball.nba.lineup', name: 'Lineup', sport_id: 'basketball.nba', count: 28940 },
    { id: 'basketball.nba.lineup_stint', name: 'LineupStint', sport_id: 'basketball.nba', count: 184320 },
    { id: 'basketball.nba.draft_prospect', name: 'DraftProspect', sport_id: 'basketball.nba', count: 138 },
    { id: 'basketball.ncaa.player_season', name: 'NCAAPlayerSeason', sport_id: 'basketball.ncaa', count: 4912 },
    { id: 'basketball.ncaa.team_season', name: 'NCAATeamSeason', sport_id: 'basketball.ncaa', count: 363 },
  ];
}

export function mockListDatasets(): ReadonlyArray<Dataset> {
  const now = Date.now();
  const hoursAgo = (h: number): string => new Date(now - h * 3600_000).toISOString();
  return [
    { id: 'basketball.nba.possessions', name: 'basketball.nba.possessions', rows: 1318472, last_updated: hoursAgo(6) },
    { id: 'basketball.nba.shots', name: 'basketball.nba.shots', rows: 1102845, last_updated: hoursAgo(6) },
    { id: 'basketball.nba.lineup_stints', name: 'basketball.nba.lineup_stints', rows: 184320, last_updated: hoursAgo(6) },
    { id: 'features.nba.player_season_stats', name: 'features.nba.player_season_stats', rows: 2740, last_updated: hoursAgo(2) },
    { id: 'features.nba.lineup_season_stats', name: 'features.nba.lineup_season_stats', rows: 28940, last_updated: hoursAgo(2) },
    { id: 'features.nba.on_off_stints', name: 'features.nba.on_off_stints', rows: 184320, last_updated: hoursAgo(2) },
    { id: 'features.nba.shot_quality', name: 'features.nba.shot_quality', rows: 320, last_updated: hoursAgo(2) },
    { id: 'features.nba.prospect_features', name: 'features.nba.prospect_features', rows: 138, last_updated: hoursAgo(12) },
    { id: 'basketball.ncaa.player_seasons', name: 'basketball.ncaa.player_seasons', rows: 4912, last_updated: hoursAgo(18) },
  ];
}

export function mockListModels(): ReadonlyArray<ModelTemplate> {
  return [
    {
      id: 'lineup_net_rating',
      name: 'lineup_net_rating',
      version: '0.1.0',
      sport_id: 'basketball.nba',
      description: 'Bayesian-shrunk RAPM with matchup adjustment. Scores observed 5-man lineups and projects unseen ones with confidence bands.',
    },
    {
      id: 'prospect_translation',
      name: 'prospect_translation',
      version: '0.1.0',
      sport_id: 'basketball.nba',
      description: 'NCAA per-40 → projected NBA per-36 with confidence bands. Trained on historical draft cohorts.',
    },
  ];
}

export function mockListApps(): ReadonlyArray<AppDescriptor> {
  return [
    { id: 'lineup_analysis', name: 'Lineup Analysis', sport_id: 'basketball.nba' },
    { id: 'prospect_translation', name: 'Prospect Translation', sport_id: 'basketball.nba' },
  ];
}

export function mockGetSchema(modelId: string): JsonSchema {
  if (modelId !== 'lineup_net_rating') {
    return {
      type: 'object',
      title: modelId,
      properties: {},
    };
  }
  return {
    type: 'object',
    title: 'LineupNetRatingConfig',
    properties: {
      seasons: {
        type: 'array',
        title: 'seasons',
        description: 'training seasons',
        items: {
          type: 'string',
          enum: ['2019-20', '2020-21', '2021-22', '2022-23', '2023-24'],
        },
        uniqueItems: true,
        default: ['2021-22', '2022-23', '2023-24'],
      },
      min_possessions: {
        type: 'integer',
        title: 'min_possessions',
        description: 'drop lineups below this sample',
        minimum: 50,
        maximum: 2000,
        default: 200,
      },
      rapm_lambda: {
        type: 'number',
        title: 'rapm_lambda',
        description: 'higher = more shrinkage',
        minimum: 10,
        maximum: 2000,
        default: 200,
        multipleOf: 1,
      },
      prior_weight: {
        type: 'number',
        title: 'prior_weight',
        description: 'blend toward team prior',
        minimum: 0,
        maximum: 1,
        default: 0.5,
        multipleOf: 0.05,
      },
      three_point_emphasis: {
        type: 'number',
        title: 'three_point_emphasis',
        description: 'feature weight multiplier',
        minimum: 0.5,
        maximum: 3,
        default: 1.0,
        multipleOf: 0.05,
      },
      matchup_adjusted: {
        type: 'boolean',
        title: 'matchup_adjusted',
        default: true,
      },
      position_constraints: {
        type: 'boolean',
        title: 'position_constraints',
        description: 'enforce 1xPG, ≥1xbig',
        default: false,
      },
    },
    required: [
      'seasons',
      'min_possessions',
      'rapm_lambda',
      'prior_weight',
      'three_point_emphasis',
      'matchup_adjusted',
      'position_constraints',
    ],
  };
}

let RUN_COUNTER = 0;

export function mockSubmitRun(modelId: string, _config: Record<string, unknown>, _label?: string): RunSubmitResponse {
  RUN_COUNTER += 1;
  const idHex = (Date.now().toString(16).slice(-4) + RUN_COUNTER.toString(16)).slice(-4);
  return { run_id: `${idHex}`, status: 'success' };
}

export function mockGetRun(modelId: string, runId: string, label?: string): RunDetail {
  return {
    run_id: runId,
    status: 'success',
    started_at: new Date().toISOString(),
    duration_s: 11.4,
    output_dataset: `tenant_demo.${modelId}`,
    row_count: BASE_LINEUPS.length,
    label,
  };
}

function buildLineupRows(config: Partial<LineupConfig> | undefined): ReadonlyArray<LineupRow> {
  const c: LineupConfig = {
    seasons: config?.seasons ?? ['2021-22', '2022-23', '2023-24'],
    min_possessions: config?.min_possessions ?? 50,
    rapm_lambda: config?.rapm_lambda ?? 200,
    prior_weight: config?.prior_weight ?? 0.5,
    three_point_emphasis: config?.three_point_emphasis ?? 1.0,
    matchup_adjusted: config?.matchup_adjusted ?? true,
    position_constraints: config?.position_constraints ?? false,
  };

  const seed = hash(JSON.stringify(c));
  const r = rand(seed);

  // Shrinkage strength: higher lambda → smaller spread. Prior weight pulls toward 0.
  const shrinkFactor = 1 / (1 + c.rapm_lambda / 200);
  const priorPull = 1 - c.prior_weight * 0.5;
  // 3pt emphasis nudges certain lineups (Pritchard/Hauser-heavy small-ball) upward.
  const threePtSmallBallNames = new Set(['Pritchard', 'Hauser', 'White']);

  const rows: LineupRow[] = BASE_LINEUPS.map((players, i) => {
    const observed = BASE_OBSERVED[i] ?? 0;
    const sampleN = BASE_SAMPLE_N[i] ?? 50;
    const smallBallCount = players.filter((p) => threePtSmallBallNames.has(p)).length;
    const threePtBoost = (c.three_point_emphasis - 1.0) * smallBallCount * 1.6;
    const jitter = (r() - 0.5) * 1.2;
    const projected = observed * shrinkFactor * priorPull + threePtBoost + jitter;
    // CI tightens with sample size: width ∝ 1/sqrt(n).
    const halfCi = Math.max(1.0, 35 / Math.sqrt(sampleN));
    return {
      lineup_id: `lineup_${i + 1}`,
      players,
      projected_net: Math.round(projected * 10) / 10,
      observed_net: observed,
      ci_lo: Math.round((projected - halfCi) * 10) / 10,
      ci_hi: Math.round((projected + halfCi) * 10) / 10,
      sample_n: sampleN,
    };
  }).filter((row) => row.sample_n >= c.min_possessions);

  // Sort descending by projected net rating — that's the demo payoff.
  return [...rows].sort((a, b) => b.projected_net - a.projected_net);
}

function buildSynergy(config: Partial<LineupConfig> | undefined): SynergyMatrix {
  const seed = hash('synergy_' + JSON.stringify(config ?? {}));
  const r = rand(seed);
  const players = PLAYERS_BOS.slice(0, 8);
  const cells: SynergyCell[] = [];
  for (let i = 0; i < players.length; i++) {
    for (let j = 0; j < players.length; j++) {
      const a = players[i];
      const b = players[j];
      if (a === undefined || b === undefined) continue;
      const v = i === j ? 0 : Math.round((r() * 16 - 4) * 10) / 10;
      cells.push({ player_a: a, player_b: b, value: v });
    }
  }
  return { players, cells };
}

export function mockGetRunOutput(
  _modelId: string,
  _runId: string,
  config: Partial<LineupConfig> | undefined,
): RunOutput {
  return {
    rows: buildLineupRows(config),
    synergy: buildSynergy(config),
  };
}

// Synergy and lineup rows for the initial page load (no submitted run yet).
export function mockDefaultRunOutput(): RunOutput {
  return mockGetRunOutput('lineup_net_rating', 'default', undefined);
}
