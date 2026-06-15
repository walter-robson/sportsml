"use client";

import * as React from "react";
import * as SliderPrimitive from "@radix-ui/react-slider";
import { cn } from "@/lib/utils";

export const Slider = React.forwardRef<
  React.ElementRef<typeof SliderPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SliderPrimitive.Root>
>(function Slider({ className, ...props }, ref) {
  return (
    <SliderPrimitive.Root
      ref={ref}
      className={cn("relative flex w-full touch-none select-none items-center", className)}
      {...props}
    >
      <SliderPrimitive.Track className="relative h-1 w-full grow overflow-hidden rounded bg-[#1a1a1a]">
        <SliderPrimitive.Range className="absolute h-full bg-accent-blue" />
      </SliderPrimitive.Track>
      <SliderPrimitive.Thumb className="block h-3 w-3 rounded-full border border-accent-blue bg-bg ring-0 transition-colors hover:bg-accent-blue focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-blue/40" />
    </SliderPrimitive.Root>
  );
});
