import * as React from 'react';
import { cn } from '@/lib/utils';

type BadgeTone = 'neutral' | 'blue' | 'green' | 'orange' | 'magenta';

const TONE_CLASSES: Record<BadgeTone, string> = {
  neutral: 'bg-bg-active text-fg-muted border-border-strong',
  blue: 'bg-[#22303a] text-accent-blue border-[#27384a]',
  green: 'bg-[#1e2a23] text-accent-green border-[#264236]',
  orange: 'bg-[#2a201c] text-accent-orange border-[#3a2a22]',
  magenta: 'bg-[#2a1c2a] text-accent-magenta border-[#3a283a]',
};

export function Badge({
  tone = 'neutral',
  className,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { tone?: BadgeTone }) {
  return (
    <span
      className={cn('pill border inline-flex items-center gap-1.5', TONE_CLASSES[tone], className)}
      {...props}
    />
  );
}
