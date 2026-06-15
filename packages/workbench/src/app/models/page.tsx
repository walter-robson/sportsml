import Link from "next/link";
import { listModels } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default async function ModelsPage() {
  const models = await listModels();
  return (
    <div className="p-6">
      <h1 className="section-header mb-4">Models</h1>
      <div className="grid grid-cols-2 gap-3 max-w-4xl">
        {models.map((m) => (
          <Link key={m.id} href={`/models/${m.id}`}>
            <Card className="hover:border-border-strong transition-colors cursor-pointer h-full">
              <CardHeader>
                <CardTitle>{m.name}</CardTitle>
                <div className="flex gap-1.5">
                  <Badge tone="magenta">v{m.version}</Badge>
                  <Badge tone="neutral">{m.sport_id}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-fg-muted text-[12px] leading-relaxed">{m.description}</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
