import Link from 'next/link';
import { listApps } from '@/lib/api';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default async function AppsListPage() {
  const apps = await listApps();
  return (
    <div className="p-6">
      <h1 className="section-header mb-4">Apps</h1>
      <div className="grid grid-cols-2 gap-3 max-w-3xl">
        {apps.map((app) => (
          <Link key={app.id} href={`/apps/${app.id.replace(/_/g, '-')}`}>
            <Card className="hover:border-border-strong transition-colors cursor-pointer">
              <CardHeader>
                <CardTitle>{app.name}</CardTitle>
                <Badge tone="neutral">{app.sport_id}</Badge>
              </CardHeader>
              <CardContent>
                <div className="mono text-[10px] text-fg-faint">{app.id}</div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
