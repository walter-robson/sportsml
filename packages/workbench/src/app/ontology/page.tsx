import { listOntologyTypes } from '@/lib/api';
import { Table, THead, TBody, TR, TH, TD } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { formatNumber } from '@/lib/utils';

export default async function OntologyPage() {
  const types = await listOntologyTypes();
  return (
    <div className="p-6">
      <h1 className="section-header mb-4">Ontology</h1>
      <div className="panel overflow-hidden">
        <Table>
          <THead>
            <TR>
              <TH>Type</TH>
              <TH>Sport</TH>
              <TH className="text-right">Rows</TH>
              <TH>ID</TH>
            </TR>
          </THead>
          <TBody>
            {types.map((t) => (
              <TR key={t.id}>
                <TD className="font-sans text-fg text-[12px]">{t.name}</TD>
                <TD>
                  <Badge tone="neutral">{t.sport_id}</Badge>
                </TD>
                <TD className="text-right text-fg-muted">{formatNumber(t.count)}</TD>
                <TD className="text-fg-faint">{t.id}</TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </div>
    </div>
  );
}
