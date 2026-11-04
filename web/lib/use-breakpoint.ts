"use client";

import { useEffect, useState } from "react";

export type Breakpoint = "mobile" | "tablet" | "desktop";

export const BREAKPOINTS = {
  tablet: "(min-width: 640px)",
  desktop: "(min-width: 1024px)",
} as const;

/**
 * Layout is CSS-first; this hook only decides which navigation form to render
 * so each breakpoint gets one correct, accessible nav rather than two.
 */
export function useBreakpoint(): Breakpoint {
  const [breakpoint, setBreakpoint] = useState<Breakpoint>("desktop");

  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return;
    const desktop = window.matchMedia(BREAKPOINTS.desktop);
    const tablet = window.matchMedia(BREAKPOINTS.tablet);

    const update = () => {
      setBreakpoint(desktop.matches ? "desktop" : tablet.matches ? "tablet" : "mobile");
    };

    update();
    desktop.addEventListener("change", update);
    tablet.addEventListener("change", update);
    return () => {
      desktop.removeEventListener("change", update);
      tablet.removeEventListener("change", update);
    };
  }, []);

  return breakpoint;
}
