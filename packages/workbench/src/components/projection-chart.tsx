import type { LineupRow } from '@/lib/types';

type Props = {
  rows: ReadonlyArray<LineupRow>;
};

// Renders observed vs shrunk-projection per lineup, sorted by sample size (high → low).
// Observed = colored stick from y=baseline up/down to value. Projection = blue dot.
export function ProjectionChart({ rows }: Props) {
  const sorted = [...rows].sort((a, b) => b.sample_n - a.sample_n);

  const VB_W = 600;
  const VB_H = 120;
  const PAD_X = 18;
  const PAD_Y = 18;
  const baselineY = VB_H / 2;
  const colWidth = sorted.length > 0 ? (VB_W - PAD_X * 2) / sorted.length : 0;

  // Find max absolute net for scaling. Cap at 18.
  const maxAbs = Math.max(
    8,
    ...sorted.map((r) => Math.max(Math.abs(r.observed_net), Math.abs(r.projected_net))),
  );
  const scale = (VB_H / 2 - PAD_Y) / maxAbs;

  function yFor(value: number): number {
    return baselineY - value * scale;
  }

  return (
    <div className="flex flex-col gap-3">
      <svg viewBox={`0 0 ${VB_W} ${VB_H}`} className="w-full h-32 block">
        <line x1={0} y1={baselineY} x2={VB_W} y2={baselineY} stroke="#1f1f1f" />
        {sorted.map((row, i) => {
          const cx = PAD_X + colWidth * (i + 0.5);
          const obsColor = row.observed_net >= 0 ? '#5a8' : '#c74';
          return (
            <g key={row.lineup_id}>
              <line
                x1={cx}
                x2={cx}
                y1={yFor(row.observed_net)}
                y2={baselineY}
                stroke={obsColor}
                strokeWidth={2}
              />
              <circle cx={cx} cy={yFor(row.projected_net)} r={2.5} fill="#9ad" />
            </g>
          );
        })}
        <text x={PAD_X} y={VB_H - 4} fill="#666" fontSize={9} className="mono">
          high sample
        </text>
        <text x={VB_W - PAD_X} y={VB_H - 4} fill="#666" fontSize={9} textAnchor="end" className="mono">
          low sample
        </text>
      </svg>
      <div className="flex gap-4 text-[10px] text-fg-faint mono">
        <span>
          <span className="inline-block w-2 h-2 align-middle mr-1.5" style={{ background: '#5a8' }} />
          observed net (raw)
        </span>
        <span>
          <span className="inline-block w-2 h-2 rounded-full align-middle mr-1.5" style={{ background: '#9ad' }} />
          model projection (shrunk)
        </span>
      </div>
    </div>
  );
}
