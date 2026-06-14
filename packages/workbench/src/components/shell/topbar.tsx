'use client';

import { usePathname } from 'next/navigation';
import { Badge } from '@/components/ui/badge';

const CRUMBS: Record<string, { section: string; page: string }> = {
  '/apps/lineup-analysis': { section: 'Apps', page: 'Lineup Analysis' },
  '/apps/prospect-translation': { section: 'Apps', page: 'Prospect Translation' },
  '/apps': { section: 'Apps', page: 'All' },
  '/ontology': { section: 'Data', page: 'Ontology' },
  '/datasets': { section: 'Data', page: 'Datasets' },
  '/models': { section: 'Data', page: 'Models' },
  '/admin': { section: 'Admin', page: 'Settings' },
};

function crumbsFor(pathname: string): { section: string; page: string } {
  if (CRUMBS[pathname]) return CRUMBS[pathname]!;
  if (pathname.startsWith('/models/')) return { section: 'Data', page: 'Model Detail' };
  return { section: '—', page: '—' };
}

type TopbarProps = {
  activeRun?: { run_id: string; label?: string } | null;
};

export function Topbar({ activeRun }: TopbarProps) {
  const pathname = usePathname() ?? '/';
  const { section, page } = crumbsFor(pathname);
  return (
    <header className="flex items-center gap-3 px-4 py-2.5 bg-bg-panel border-b border-border">
      <div className="text-[12px] text-fg-faint">
        {section} / <span className="text-fg-muted">{page}</span>
      </div>
      {activeRun && (
        <Badge tone="blue" className="ml-2">
          run_id: {activeRun.run_id}
          {activeRun.label ? ` · "${activeRun.label}"` : ''}
        </Badge>
      )}
      <Badge tone="neutral" className="ml-auto">
        tenant: demo
      </Badge>
    </header>
  );
}
