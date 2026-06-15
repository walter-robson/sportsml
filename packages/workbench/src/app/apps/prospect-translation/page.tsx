import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function ProspectTranslationPage() {
  return (
    <div className="p-6 max-w-3xl">
      <h1 className="section-header mb-4">Prospect Translation</h1>
      <Card>
        <CardHeader>
          <CardTitle>basketball.nba.prospect_translation</CardTitle>
          <Badge tone="magenta">v0.5</Badge>
        </CardHeader>
        <CardContent>
          <p className="text-fg-muted text-[12.5px] mb-3">
            NCAA per-40 stats translated to projected NBA per-36 lines with confidence bands.
            Comparable players surfaced from historical draft cohorts.
          </p>
          <div className="mono text-[10.5px] text-fg-faint italic">
            Coming in v0.5 — slider UI wired, functional table output deferred.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
