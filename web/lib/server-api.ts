/**
 * Server-side reads of the small, read-only endpoints.
 *
 * These never carry an image: the model card and health payload are a few
 * hundred bytes, so they are safe to fetch from the Next.js server even when
 * the deployment is on Vercel. Failures degrade to `serviceReachable: false`
 * rather than throwing a 500 at the visitor.
 */

import { cache } from "react";

import type { HealthResponse, ModelCard, ModelInfo } from "./contracts";

const SERVER_BASE = (
  process.env.API_INTERNAL_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000"
).replace(/\/+$/, "");

async function readJson<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(`${SERVER_BASE}${path}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(2500),
    });
    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

/** Memoised per request: the layout and the page share one pair of reads. */
export const loadModelInfo = cache(async (): Promise<ModelInfo> => {
  const [health, card] = await Promise.all([
    readJson<HealthResponse>("/v1/health"),
    readJson<ModelCard>("/v1/model"),
  ]);
  return { health, card, serviceReachable: health !== null };
});
