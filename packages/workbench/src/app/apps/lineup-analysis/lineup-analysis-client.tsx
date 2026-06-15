"use client";

import * as React from "react";
import { ModelConfigForm } from "@/components/model-config-form";
import { ResultsPanel } from "@/components/results-panel";
import { Badge } from "@/components/ui/badge";
import { submitRun, getRun, getRunOutput } from "@/lib/api";
import type { JsonSchema, LineupConfig, RunDetail, RunOutput } from "@/lib/types";

type Props = {
  modelId: string;
  schema: JsonSchema;
  initialOutput: RunOutput;
};

type ActiveRun = {
  run_id: string;
  label?: string;
  detail?: RunDetail;
};

export function LineupAnalysisClient({ modelId, schema, initialOutput }: Props) {
  const [output, setOutput] = React.useState<RunOutput>(initialOutput);
  const [submitting, setSubmitting] = React.useState(false);
  const [activeRun, setActiveRun] = React.useState<ActiveRun | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const handleSubmit = React.useCallback(
    async (values: Record<string, unknown>) => {
      setSubmitting(true);
      setError(null);
      try {
        const submitted = await submitRun(modelId, values);
        const detail = await getRun(modelId, submitted.run_id, "custom v3");
        // Tiny artificial delay so the loading state is perceivable in mock mode.
        await new Promise((r) => setTimeout(r, 350));
        const next = await getRunOutput(modelId, submitted.run_id, values as Partial<LineupConfig>);
        setActiveRun({ run_id: submitted.run_id, label: "custom v3", detail });
        setOutput(next);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Run failed");
      } finally {
        setSubmitting(false);
      }
    },
    [modelId],
  );

  return (
    <div className="grid grid-cols-[280px_1fr] h-full">
      <aside className="bg-bg-surface border-r border-border p-4 overflow-y-auto">
        <div className="mb-1 mono uppercase text-[11px] tracking-widerlabel text-white">
          Model Config
        </div>
        <div className="mono text-[10px] text-fg-faint mb-4">basketball.nba.{modelId} · v0.1.0</div>
        <ModelConfigForm
          schema={schema}
          onSubmit={handleSubmit}
          submitting={submitting}
          submitLabel="Run Model"
          hint="~12s on 270K possessions"
        />
        {error && <div className="mt-3 text-[10px] text-accent-orange mono">{error}</div>}
      </aside>
      <section className="p-4 overflow-y-auto flex flex-col gap-3">
        <div className="flex items-center gap-2">
          {activeRun ? (
            <Badge tone="blue">
              run_id: {activeRun.run_id}
              {activeRun.label ? ` · "${activeRun.label}"` : ""}
            </Badge>
          ) : (
            <Badge tone="neutral">no active run · showing defaults</Badge>
          )}
          {activeRun?.detail && (
            <span className="mono text-[10px] text-fg-faint">
              {activeRun.detail.row_count} rows · {activeRun.detail.duration_s.toFixed(1)}s
            </span>
          )}
        </div>
        <ResultsPanel output={output} loading={submitting} />
      </section>
    </div>
  );
}
