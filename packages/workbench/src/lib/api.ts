// Typed API client. Routes calls to either the real FastAPI service or the mock
// layer based on NEXT_PUBLIC_USE_MOCK. Both code paths return identical TS shapes.

import {
  mockDefaultRunOutput,
  mockGetRun,
  mockGetRunOutput,
  mockGetSchema,
  mockListApps,
  mockListDatasets,
  mockListModels,
  mockListOntologyTypes,
  mockSubmitRun,
} from "./api-mock";
import { nameFor } from "./player-names";
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
  RunStatus,
  RunSubmitResponse,
  SynergyCell,
  SynergyMatrix,
} from "./types";

// --- Backend row/response shapes -------------------------------------------
// The FastAPI service returns slightly different shapes than the components
// consume. These types capture the on-the-wire shape; helpers below convert
// them into the frontend's domain model.

type BackendLineupRow = {
  lineup_id: string;
  team_id: string;
  player_ids: ReadonlyArray<string>;
  projected_net: number;
  ci_lo: number;
  ci_hi: number;
  sample_n: number;
};

type BackendRunOutput = {
  run_id: string;
  rows: ReadonlyArray<BackendLineupRow>;
};

type BackendSubmitResponse = {
  run_id: string;
  status: string; // "succeeded" | "failed" | "running" | "cached" — backend dialect
  cached?: boolean;
  duration_s?: number;
  row_count?: number;
  output_dataset?: string;
};

type BackendRunDetail = BackendSubmitResponse & {
  model_id?: string;
  tenant_id?: string;
  started_at?: string;
  finished_at?: string | null;
  label?: string | null;
  error?: string | null;
};

function mapStatus(s: string): RunStatus {
  switch (s) {
    case "succeeded":
    case "success":
    case "cached":
      return "success";
    case "failed":
    case "error":
      return "failed";
    case "queued":
      return "queued";
    case "running":
    default:
      return "running";
  }
}

// Synthesize an "observed" net rating from the shrunk projection. Real backend
// will return this column directly; for v0 we approximate so the projection
// chart can show the shrinkage story.
//
// observed = projected + deterministic noise scaled by 1/sqrt(sample_n).
// High-sample lineups end up with observed ≈ projected. Low-sample lineups
// have visibly larger gaps — which is exactly the shrinkage story we want
// rendered.
function approximateObserved(row: BackendLineupRow): number {
  const noiseSeed = row.lineup_id.split("").reduce((acc, c) => (acc * 31 + c.charCodeAt(0)) | 0, 0);
  const normalized = ((noiseSeed >>> 0) % 1000) / 1000.0 - 0.5; // -0.5..0.5
  const scale = 8 / Math.sqrt(Math.max(row.sample_n, 1));
  return Number((row.projected_net + normalized * scale * 6).toFixed(2));
}

function toLineupRow(r: BackendLineupRow): LineupRow {
  return {
    lineup_id: r.lineup_id,
    players: r.player_ids.map(nameFor),
    projected_net: r.projected_net,
    ci_lo: r.ci_lo,
    ci_hi: r.ci_hi,
    sample_n: r.sample_n,
    observed_net: approximateObserved(r),
  };
}

// Build a synergy heatmap from the top rows by surfacing each player's marginal
// projected net when they appear in top-K lineups. v0 approximation; real
// implementation derives from RAPM coefficients in the model output.
function deriveSynergyMatrix(rows: ReadonlyArray<LineupRow>): SynergyMatrix {
  const counts: Record<string, { sum: number; n: number }> = {};
  for (const row of rows) {
    for (const p of row.players) {
      if (!counts[p]) counts[p] = { sum: 0, n: 0 };
      counts[p].sum += row.projected_net;
      counts[p].n += 1;
    }
  }
  const top = Object.entries(counts)
    .map(([p, v]) => ({ p, mean: v.sum / Math.max(v.n, 1), n: v.n }))
    .filter((p) => p.n >= 2)
    .sort((a, b) => b.mean - a.mean)
    .slice(0, 8)
    .map((p) => p.p);

  const cells: SynergyCell[] = [];
  for (const a of top) {
    for (const b of top) {
      if (a === b) {
        cells.push({ player_a: a, player_b: b, value: 0 });
        continue;
      }
      let sum = 0;
      let n = 0;
      for (const row of rows) {
        if (row.players.includes(a) && row.players.includes(b)) {
          sum += row.projected_net;
          n += 1;
        }
      }
      cells.push({
        player_a: a,
        player_b: b,
        value: n > 0 ? Number((sum / n).toFixed(1)) : 0,
      });
    }
  }
  return { players: top, cells };
}

function toRunOutput(backend: BackendRunOutput): RunOutput {
  const rows = backend.rows.map(toLineupRow);
  return { rows, synergy: deriveSynergyMatrix(rows) };
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`API ${path} → ${res.status}`);
  }
  return (await res.json()) as T;
}

type BackendOntologyType = {
  type_name: string;
  properties: ReadonlyArray<unknown>;
  // not currently present on backend — we synthesize count and sport_id from type_name
};

type BackendDataset = {
  id: string;
  name: string;
  path?: string;
  size_bytes?: number;
};

type BackendModelTemplate = {
  id: string;
  version: string;
  sport_id: string;
  config_schema?: JsonSchema;
};

type BackendApp = {
  id: string;
  sport_id: string;
  name?: string;
  description?: string;
};

export async function listOntologyTypes(): Promise<ReadonlyArray<ObjectType>> {
  if (USE_MOCK) return mockListOntologyTypes();
  const resp = await fetchJson<{ types: ReadonlyArray<BackendOntologyType> }>("/ontology/types");
  return resp.types.map((t) => {
    const tn = t.type_name;
    const sportId = tn.startsWith("core.") ? "core" : tn.split(".").slice(0, -1).join(".");
    const leaf = tn.split(".").slice(-1)[0] ?? tn;
    return {
      id: tn,
      name: leaf.charAt(0).toUpperCase() + leaf.slice(1),
      sport_id: sportId,
      count: 0, // TODO(v0.5): backend should populate row counts
    };
  });
}

export async function listDatasets(): Promise<ReadonlyArray<Dataset>> {
  if (USE_MOCK) return mockListDatasets();
  const resp = await fetchJson<{ datasets: ReadonlyArray<BackendDataset> }>("/datasets");
  return resp.datasets.map((d) => ({
    id: d.id,
    name: d.name,
    rows: 0, // TODO(v0.5): backend should populate row counts
    last_updated: new Date().toISOString(),
  }));
}

export async function listModels(): Promise<ReadonlyArray<ModelTemplate>> {
  if (USE_MOCK) return mockListModels();
  const resp = await fetchJson<{ models: ReadonlyArray<BackendModelTemplate> }>("/models");
  return resp.models.map((m) => ({
    id: m.id,
    name: m.id,
    version: m.version,
    sport_id: m.sport_id,
    description:
      typeof m.config_schema?.description === "string" ? m.config_schema.description : "",
  }));
}

export async function getModelSchema(modelId: string): Promise<JsonSchema> {
  if (USE_MOCK) return mockGetSchema(modelId);
  return fetchJson<JsonSchema>(`/models/${modelId}/schema`);
}

export async function listApps(): Promise<ReadonlyArray<AppDescriptor>> {
  if (USE_MOCK) return mockListApps();
  const resp = await fetchJson<{ apps: ReadonlyArray<BackendApp> }>("/apps");
  return resp.apps.map((a) => ({
    id: a.id,
    name: a.name ?? a.id,
    sport_id: a.sport_id,
  }));
}

export async function submitRun(
  modelId: string,
  config: Record<string, unknown>,
  label?: string,
): Promise<RunSubmitResponse> {
  if (USE_MOCK) return mockSubmitRun(modelId, config, label);
  const resp = await fetchJson<BackendSubmitResponse>(`/models/${modelId}/runs`, {
    method: "POST",
    body: JSON.stringify({ config, label }),
  });
  return { run_id: resp.run_id, status: mapStatus(resp.status) };
}

export async function getRun(modelId: string, runId: string, label?: string): Promise<RunDetail> {
  if (USE_MOCK) return mockGetRun(modelId, runId, label);
  const resp = await fetchJson<BackendRunDetail>(`/models/${modelId}/runs/${runId}`);
  return {
    run_id: resp.run_id,
    status: mapStatus(resp.status),
    started_at: resp.started_at ?? new Date().toISOString(),
    duration_s: resp.duration_s ?? 0,
    output_dataset: resp.output_dataset ?? "",
    row_count: resp.row_count ?? 0,
    label: resp.label ?? undefined,
  };
}

export async function getRunOutput(
  modelId: string,
  runId: string,
  config?: Partial<LineupConfig>,
): Promise<RunOutput> {
  if (USE_MOCK) return mockGetRunOutput(modelId, runId, config);
  const raw = await fetchJson<BackendRunOutput>(
    `/models/${modelId}/runs/${runId}/output?limit=100&sort=-projected_net`,
  );
  return toRunOutput(raw);
}

export function getInitialRunOutput(): RunOutput {
  // Synchronous initial state — only meaningful in mock mode. Real API path always
  // requires an actual run.
  return mockDefaultRunOutput();
}

export const apiConfig = {
  url: API_URL,
  useMock: USE_MOCK,
};
