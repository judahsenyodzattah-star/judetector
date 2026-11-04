"use client";

import type { ReactNode } from "react";

import type { ModelInfo } from "@/lib/contracts";
import { useBreakpoint } from "@/lib/use-breakpoint";

import { ModelStatusLine } from "./model-status";
import { RailNav, TopNav } from "./nav";

export function AppShell({ modelInfo, children }: { modelInfo: ModelInfo; children: ReactNode }) {
  const breakpoint = useBreakpoint();
  const status = <ModelStatusLine info={modelInfo} />;

  return (
    <div className="app-shell" data-breakpoint={breakpoint}>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      {breakpoint === "desktop" ? <RailNav modelStatus={status} /> : null}
      {breakpoint !== "desktop" ? <TopNav modelStatus={status} /> : null}
      <main id="main" className="workspace">
        {children}
      </main>
    </div>
  );
}
