'use client';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LineupsTable } from '@/components/lineups-table';
import { SynergyHeatmap } from '@/components/synergy-heatmap';
import { ProjectionChart } from '@/components/projection-chart';
import type { RunOutput } from '@/lib/types';
import { cn } from '@/lib/utils';

type Props = {
  output: RunOutput;
  loading: boolean;
};

export function ResultsPanel({ output, loading }: Props) {
  return (
    <div className={cn('relative transition-opacity', loading && 'opacity-60')}>
      {loading && (
        <div className="absolute right-0 top-0 mono text-[10px] text-accent-blue uppercase tracking-widerlabel">
          Running…
        </div>
      )}
      <Tabs defaultValue="top">
        <TabsList>
          <TabsTrigger value="top">Top Lineups</TabsTrigger>
          <TabsTrigger value="synergy">Synergy Heatmap</TabsTrigger>
          <TabsTrigger value="projection">Projection Bands</TabsTrigger>
        </TabsList>
        <TabsContent value="top">
          <section className="panel p-4">
            <h5 className="section-header mb-3">Top Projected 5-Man Lineups</h5>
            <LineupsTable rows={output.rows} />
          </section>
        </TabsContent>
        <TabsContent value="synergy">
          <section className="panel p-4">
            <h5 className="section-header mb-3">2-Man Synergy · vs Team Avg</h5>
            {output.synergy && <SynergyHeatmap synergy={output.synergy} />}
          </section>
        </TabsContent>
        <TabsContent value="projection">
          <section className="panel p-4">
            <h5 className="section-header mb-3">Projection vs. Observed (sorted by sample size)</h5>
            <ProjectionChart rows={output.rows} />
          </section>
        </TabsContent>
      </Tabs>
    </div>
  );
}
