import { listDatasets } from "@/lib/api";
import { Table, THead, TBody, TR, TH, TD } from "@/components/ui/table";
import { formatNumber, formatRelative } from "@/lib/utils";

export default async function DatasetsPage() {
  const datasets = await listDatasets();
  return (
    <div className="p-6">
      <h1 className="section-header mb-4">Datasets</h1>
      <div className="panel overflow-hidden">
        <Table>
          <THead>
            <TR>
              <TH>Name</TH>
              <TH className="text-right">Rows</TH>
              <TH className="text-right">Updated</TH>
            </TR>
          </THead>
          <TBody>
            {datasets.map((d) => (
              <TR key={d.id}>
                <TD>{d.name}</TD>
                <TD className="text-right text-fg-muted">{formatNumber(d.rows)}</TD>
                <TD className="text-right text-fg-faint">{formatRelative(d.last_updated)}</TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </div>
    </div>
  );
}
