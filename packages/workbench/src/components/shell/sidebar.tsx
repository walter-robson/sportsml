'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

type NavItem = { label: string; href: string };
type NavSection = { label: string; items: ReadonlyArray<NavItem>; pushDown?: boolean };

const SECTIONS: ReadonlyArray<NavSection> = [
  {
    label: 'Data',
    items: [
      { label: 'Ontology', href: '/ontology' },
      { label: 'Datasets', href: '/datasets' },
      { label: 'Models', href: '/models' },
    ],
  },
  {
    label: 'Apps',
    items: [
      { label: 'Lineup Analysis', href: '/apps/lineup-analysis' },
      { label: 'Prospect Translation', href: '/apps/prospect-translation' },
    ],
  },
  {
    label: 'Admin',
    pushDown: true,
    items: [{ label: 'Settings', href: '/admin' }],
  },
];

export function Sidebar() {
  const pathname = usePathname() ?? '/';
  return (
    <nav className="flex flex-col gap-px bg-bg-panel border-r border-border h-full w-[200px] py-3 px-2.5">
      <Link href="/apps/lineup-analysis" className="mono text-white font-semibold text-[13px] px-2 pt-1 pb-3 tracking-tight">
        sportsml<span className="text-accent-green">.</span>
      </Link>

      {SECTIONS.map((section) => (
        <div key={section.label} className={cn('flex flex-col gap-px', section.pushDown && 'mt-auto')}>
          <div className="px-2 pt-2.5 pb-1 mono uppercase text-[9.5px] tracking-widerlabel text-fg-fainter">
            {section.label}
          </div>
          {section.items.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + '/');
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'relative px-2.5 py-1.5 rounded text-[12.5px] transition-colors',
                  active ? 'bg-bg-active text-white' : 'text-[#bbb] hover:bg-bg-hover hover:text-white',
                )}
              >
                {active && (
                  <span className="absolute -left-[5px] top-1/2 -translate-y-1/2 h-3.5 w-[3px] rounded bg-accent-blue" />
                )}
                {item.label}
              </Link>
            );
          })}
        </div>
      ))}
    </nav>
  );
}
