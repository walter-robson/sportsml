import type { LineupRow } from '@/lib/types';
import { formatSigned, formatNumber } from '@/lib/utils';
import { Table, THead, TBody, TR, TH, TD } from '@/components/ui/table';
import { cn } from '@/lib/utils';

type Props = {
  rows: ReadonlyArray<LineupRow>;
};

export function LineupsTable({ rows }: Props) {
  return (
    <Table>
      <THead>
        <TR>
          <TH>Lineup</TH>
          <TH className="text-right">Net</TH>
          <TH className="text-right">Poss</TH>
          <TH className="text-right">±CI</TH>
        </TR>
      </THead>
      <TBody>
        {rows.map((row) => {
          const pos = row.projected_net >= 0;
          const halfCi = (row.ci_hi - row.ci_lo) / 2;
          return (
            <TR key={row.lineup_id}>
              <TD className="font-sans text-[11.5px] text-[#bbb]">{row.players.join(' · ')}</TD>
              <TD className={cn('text-right font-medium', pos ? 'text-accent-green' : 'text-accent-orange')}>
                {formatSigned(row.projected_net)}
              </TD>
              <TD className="text-right text-fg-muted">{formatNumber(row.sample_n)}</TD>
              <TD className="text-right text-fg-faint">±{halfCi.toFixed(1)}</TD>
            </TR>
          );
        })}
      </TBody>
    </Table>
  );
}
