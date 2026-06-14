import type { SynergyMatrix } from '@/lib/types';

type Props = {
  synergy: SynergyMatrix;
};

// Map value ∈ [-5, +10] to a discrete bg color. Green for positive, red for negative,
// dim for near zero. Diagonal cells use a deep blue to indicate self-pair (no synergy).
function colorFor(value: number, isDiag: boolean): string {
  if (isDiag) return '#1c2030';
  if (value >= 8) return '#2c4e3e';
  if (value >= 5) return '#264438';
  if (value >= 2) return '#244232';
  if (value >= -1) return '#1c1c1c';
  if (value >= -3) return '#3a2828';
  return '#3a2222';
}

export function SynergyHeatmap({ synergy }: Props) {
  const { players, cells } = synergy;
  const grid: Record<string, number> = {};
  for (const c of cells) {
    grid[`${c.player_a}::${c.player_b}`] = c.value;
  }
  return (
    <div className="flex flex-col gap-3">
      <div
        className="grid gap-px"
        style={{ gridTemplateColumns: `120px repeat(${players.length}, minmax(0, 1fr))` }}
      >
        <div />
        {players.map((p) => (
          <div key={`col-${p}`} className="mono text-[9px] text-fg-faint text-center pb-1 uppercase tracking-wide">
            {p.slice(0, 4)}
          </div>
        ))}
        {players.map((rowP) => (
          <Row
            key={`row-${rowP}`}
            rowP={rowP}
            players={players}
            grid={grid}
          />
        ))}
      </div>
      <div className="flex gap-4 text-[10px] text-fg-faint mono">
        <span><Swatch color="#3a2222" /> −5</span>
        <span><Swatch color="#1c1c1c" /> 0</span>
        <span><Swatch color="#2c4e3e" /> +10</span>
      </div>
    </div>
  );
}

function Row({
  rowP,
  players,
  grid,
}: {
  rowP: string;
  players: ReadonlyArray<string>;
  grid: Record<string, number>;
}) {
  return (
    <>
      <div className="mono text-[10px] text-fg-faint pr-2 flex items-center justify-end uppercase tracking-wide">
        {rowP}
      </div>
      {players.map((colP) => {
        const v = grid[`${rowP}::${colP}`] ?? 0;
        const isDiag = rowP === colP;
        return (
          <div
            key={`${rowP}::${colP}`}
            className="aspect-square rounded-sm flex items-center justify-center text-[9px] text-white/90 mono"
            style={{ background: colorFor(v, isDiag) }}
          >
            {!isDiag && (v >= 0 ? `+${Math.round(v)}` : Math.round(v))}
          </div>
        );
      })}
    </>
  );
}

function Swatch({ color }: { color: string }) {
  return (
    <span className="inline-block w-2 h-2 rounded-sm align-middle mr-1.5" style={{ background: color }} />
  );
}
