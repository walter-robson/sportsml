import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { apiConfig } from "@/lib/api";

export default function AdminPage() {
  return (
    <div className="p-6 max-w-3xl flex flex-col gap-3">
      <h1 className="section-header mb-2">Admin · Settings</h1>
      <Card>
        <CardHeader>
          <CardTitle>API</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="mono text-[11px] flex flex-col gap-1">
            <div>
              <span className="text-fg-faint">url:</span>{" "}
              <span className="text-accent-blue">{apiConfig.url}</span>
            </div>
            <div>
              <span className="text-fg-faint">mode:</span>{" "}
              <span className="text-accent-magenta">{apiConfig.useMock ? "mock" : "live"}</span>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Tenant</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="mono text-[11px] text-fg-muted">demo (hard-coded for POC)</div>
        </CardContent>
      </Card>
    </div>
  );
}
