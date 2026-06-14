import type { Metadata } from 'next';
import './globals.css';
import { WorkbenchShell } from '@/components/shell/workbench-shell';

export const metadata: Metadata = {
  title: 'sportsml — Workbench',
  description: 'Foundry-style sports analytics platform',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body>
        <WorkbenchShell>{children}</WorkbenchShell>
      </body>
    </html>
  );
}
