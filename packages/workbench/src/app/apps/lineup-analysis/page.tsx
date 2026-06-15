import { getModelSchema, getInitialRunOutput } from "@/lib/api";
import { LineupAnalysisClient } from "./lineup-analysis-client";

const MODEL_ID = "lineup_net_rating";

export default async function LineupAnalysisPage() {
  const [schema, initialOutput] = await Promise.all([
    getModelSchema(MODEL_ID),
    Promise.resolve(getInitialRunOutput()),
  ]);

  return <LineupAnalysisClient modelId={MODEL_ID} schema={schema} initialOutput={initialOutput} />;
}
