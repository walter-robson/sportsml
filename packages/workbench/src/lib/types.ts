// Shared TypeScript types mirroring the FastAPI service contract (spec section 2.2).

export type HealthStatus = { status: "ok" };

export type ObjectType = {
  id: string;
  name: string;
  sport_id: string;
  count: number;
};

export type Dataset = {
  id: string;
  name: string;
  rows: number;
  last_updated: string; // ISO timestamp
};

export type ModelTemplate = {
  id: string;
  name: string;
  version: string;
  sport_id: string;
  description: string;
};

// RJSF-compatible JSONSchema. Loose-typed by design — the backend owns the canonical
// schema; we render whatever shape it returns.
export type JsonSchema = {
  $schema?: string;
  type: "object";
  title?: string;
  description?: string;
  properties: Record<string, JsonSchemaField>;
  required?: string[];
};

export type JsonSchemaField = {
  type: "string" | "number" | "integer" | "boolean" | "array";
  title?: string;
  description?: string;
  default?: unknown;
  minimum?: number;
  maximum?: number;
  multipleOf?: number;
  enum?: ReadonlyArray<string | number>;
  items?: { type: "string" | "number"; enum?: ReadonlyArray<string | number> };
  uniqueItems?: boolean;
};

export type RunStatus = "queued" | "running" | "success" | "failed";

export type RunSubmitResponse = {
  run_id: string;
  status: RunStatus;
};

export type RunDetail = {
  run_id: string;
  status: RunStatus;
  started_at: string;
  duration_s: number;
  output_dataset: string;
  row_count: number;
  label?: string;
};

export type LineupRow = {
  lineup_id: string;
  players: ReadonlyArray<string>;
  projected_net: number;
  ci_lo: number;
  ci_hi: number;
  sample_n: number;
  observed_net: number;
};

export type SynergyCell = {
  player_a: string;
  player_b: string;
  value: number;
};

export type SynergyMatrix = {
  players: ReadonlyArray<string>;
  cells: ReadonlyArray<SynergyCell>;
};

export type RunOutput = {
  rows: ReadonlyArray<LineupRow>;
  synergy?: SynergyMatrix;
};

export type AppDescriptor = {
  id: string;
  name: string;
  sport_id: string;
};

export type LineupConfig = {
  seasons: ReadonlyArray<string>;
  min_possessions: number;
  rapm_lambda: number;
  prior_weight: number;
  three_point_emphasis: number;
  matchup_adjusted: boolean;
  position_constraints: boolean;
};
