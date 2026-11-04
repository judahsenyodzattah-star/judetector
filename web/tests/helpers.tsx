import { render, type RenderOptions } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";

import type { DetectResponse, HealthResponse, ModelCard, ModelInfo } from "@/lib/contracts";
import { SessionProvider } from "@/lib/session";

import cardFixture from "./fixtures/model-card.json";
import detectFixture from "./fixtures/detect-response.json";
import healthFixture from "./fixtures/health.json";

/** Captured from the real API by `tests/test_web_contract.py`'s fixture run. */
export const detectResponse = detectFixture as unknown as DetectResponse;
export const card = cardFixture as unknown as ModelCard;
export const health = healthFixture as unknown as HealthResponse;

export function modelInfo(overrides: Partial<ModelInfo> = {}): ModelInfo {
  return { health, card, serviceReachable: true, ...overrides };
}

export function modelInfoDegraded(): ModelInfo {
  return {
    health: {
      ...health,
      status: "degraded",
      model: { ...health.model!, available: false, loaded: false },
    },
    card: { ...card, available: false },
    serviceReachable: true,
  };
}

export function modelInfoUnknown(): ModelInfo {
  return { health: null, card: null, serviceReachable: false };
}

function Wrapper({ children }: { children: ReactNode }) {
  return <SessionProvider>{children}</SessionProvider>;
}

export function renderWithSession(ui: ReactElement, options?: Omit<RenderOptions, "wrapper">) {
  return render(ui, { wrapper: Wrapper, ...options });
}

export interface FileOptions {
  size?: number;
  type?: string;
}

export function fileOf(name: string, { size = 2048, type = "image/png" }: FileOptions = {}): File {
  const file = new File([new Uint8Array(8)], name, { type });
  Object.defineProperty(file, "size", { value: size });
  return file;
}

/** jsdom has no layout: breakpoints are simulated through matchMedia. */
export function mockViewport(width: number): void {
  window.matchMedia = ((query: string) => {
    const min = Number(query.match(/min-width:\s*(\d+)px/)?.[1] ?? 0);
    return {
      matches: width >= min,
      media: query,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    } as unknown as MediaQueryList;
  }) as typeof window.matchMedia;
}

/** Capture `<a download>` activations without navigating. */
export function captureDownloads(): Array<{ href: string; download: string }> {
  const captured: Array<{ href: string; download: string }> = [];
  HTMLAnchorElement.prototype.click = function click(this: HTMLAnchorElement) {
    captured.push({ href: this.href, download: this.download });
  };
  return captured;
}
