import { getModelSchema, listModels } from '@/lib/api';
import { notFound } from 'next/navigation';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

type Props = { params: { id: string } };

export default async function ModelDetailPage({ params }: Props) {
  const [models, schema] = await Promise.all([listModels(), getModelSchema(params.id)]);
  const model = models.find((m) => m.id === params.id);
  if (!model) notFound();

  const fields = Object.entries(schema.properties);

  return (
    <div className="p-6 max-w-4xl flex flex-col gap-4">
      <div className="flex items-baseline gap-3">
        <h1 className="section-header">{model.name}</h1>
        <Badge tone="magenta">v{model.version}</Badge>
        <Badge tone="neutral">{model.sport_id}</Badge>
      </div>
      <p className="text-fg-muted text-[12.5px] max-w-2xl">{model.description}</p>

      <Card>
        <CardHeader>
          <CardTitle>Config Schema</CardTitle>
          <Badge tone="neutral">{fields.length} fields</Badge>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col divide-y divide-border-subtle">
            {fields.map(([key, field]) => (
              <div key={key} className="py-2 grid grid-cols-[180px_1fr] gap-3 items-baseline">
                <div className="mono text-[11px] text-fg-muted">{key}</div>
                <div className="flex flex-col gap-1">
                  <div className="mono text-[10.5px] text-accent-blue">
                    {field.type}
                    {field.minimum !== undefined && field.maximum !== undefined && (
                      <span className="text-fg-faint"> · [{field.minimum} … {field.maximum}]</span>
                    )}
                    {field.default !== undefined && (
                      <span className="text-fg-faint"> · default {JSON.stringify(field.default)}</span>
                    )}
                  </div>
                  {field.description && (
                    <div className="text-[11px] text-fg-faint italic">{field.description}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent Runs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="mono text-[10.5px] text-fg-faint italic">
            No runs yet — submit one from the corresponding app to populate this list.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
