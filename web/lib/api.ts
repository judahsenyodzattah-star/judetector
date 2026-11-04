/**
 * The browser's only route to the inference service.
 *
 * Transport choice is a deployment decision, not a detail. Vercel Functions
 * cap a request body at 4.5 MB, which a 25 MB upload cannot pass through, so
 * production sends the file **directly** to the API (CORS) while local
 * development and non-Vercel hosts may use the same-origin proxy at
 * `/api/detect`. See `docs/WEB.md`.
 */

import type { DetectResponse, HealthResponse, ModelCard, Problem } from "./contracts";

export type Transport = "direct" | "proxy";

export interface DetectParams {
  file: File;
  confidence: number;
  iou: number;
  includeAnnotated: boolean;
  signal?: AbortSignal;
}

export interface DetectMeta {
  requestId: string | null;
  retryAfterSeconds: number | null;
  /** Round-trip time measured by this browser, not by the server. */
  clientMs: number;
}

export interface DetectOutcome {
  result: DetectResponse;
  meta: DetectMeta;
}

export class ApiProblemError extends Error {
  readonly problem: Problem;
  readonly meta: { requestId: string | null; retryAfterSeconds: number | null };

  constructor(problem: Problem, meta: { requestId: string | null; retryAfterSeconds: number | null }) {
    super(problem.title);
    this.name = "ApiProblemError";
    this.problem = problem;
    this.meta = meta;
  }
}

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "").replace(/\/+$/, "");

/**
 * `direct` when an API origin is configured; the proxy otherwise. A deployment
 * on Vercel must set `NEXT_PUBLIC_API_BASE_URL`, because 25 MB cannot cross a
 * Function's 4.5 MB body limit.
 */
export function activeTransport(): Transport {
  const configured = process.env.NEXT_PUBLIC_DETECT_TRANSPORT;
  if (configured === "proxy") return "proxy";
  if (configured === "direct") return "direct";
  return API_BASE ? "direct" : "proxy";
}

export function detectEndpoint(
  transport: Transport = activeTransport(),
  base: string = API_BASE,
): string {
  return transport === "direct" ? `${base}/v1/detect` : "/api/detect";
}

interface ResponseMeta {
  requestId: string | null;
  retryAfterSeconds: number | null;
}

function readMeta(response: Response, body: Problem | null): ResponseMeta {
  const headerId = response.headers.get("x-request-id");
  const retryHeader = response.headers.get("retry-after");
  const retry = retryHeader && Number.isFinite(Number(retryHeader)) ? Number(retryHeader) : null;
  return { requestId: body?.request_id ?? headerId, retryAfterSeconds: retry };
}

function fallbackProblem(status: number, detail: string): Problem {
  return {
    type: "unexpected_response",
    title: status === 0 ? "Could not reach the service" : "The request failed",
    status,
    detail,
    request_id: "",
  };
}

async function problemFrom(response: Response): Promise<Problem> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/problem+json")) {
    try {
      return (await response.json()) as Problem;
    } catch {
      return fallbackProblem(response.status, "The service returned an unreadable error.");
    }
  }
  if (response.status === 413) {
    return {
      type: "payload_too_large",
      title: "The upload was rejected as too large",
      status: 413,
      detail:
        "The file did not reach the analysis service. If this app is hosted on Vercel, uploads over 4.5 MB must go directly to the API.",
      request_id: "",
    };
  }
  return fallbackProblem(
    response.status,
    `The service answered with status ${response.status}.`,
  );
}

export async function detectImage(params: DetectParams): Promise<DetectOutcome> {
  const body = new FormData();
  body.append("file", params.file, params.file.name);
  body.append("confidence", String(params.confidence));
  body.append("iou", String(params.iou));
  body.append("include_annotated", String(params.includeAnnotated));

  const startedAt = performance.now();
  let response: Response;
  try {
    response = await fetch(detectEndpoint(), {
      method: "POST",
      body,
      signal: params.signal,
      // No custom headers: multipart/form-data posts are CORS-simple, so the
      // direct transport needs no preflight round trip.
      cache: "no-store",
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiProblemError(
      fallbackProblem(
        0,
        "The analysis service could not be reached. Check your connection and try again.",
      ),
      { requestId: null, retryAfterSeconds: null },
    );
  }

  const clientMs = performance.now() - startedAt;

  if (!response.ok) {
    const problem = await problemFrom(response);
    throw new ApiProblemError(problem, readMeta(response, problem));
  }

  const result = (await response.json()) as DetectResponse;
  return { result, meta: { ...readMeta(response, null), clientMs } };
}

export function decodeAnnotated(data: string): string {
  return `data:image/png;base64,${data}`;
}

export function annotatedBlob(data: string): Blob {
  const binary = atob(data);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return new Blob([bytes], { type: "image/png" });
}

export function resultJsonBlob(result: DetectResponse): Blob {
  return new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
}

export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/v1/health`, { cache: "no-store", signal });
  if (!response.ok) throw new Error(`health ${response.status}`);
  return (await response.json()) as HealthResponse;
}

export async function fetchModelCard(signal?: AbortSignal): Promise<ModelCard> {
  const response = await fetch(`${API_BASE}/v1/model`, { cache: "no-store", signal });
  if (!response.ok) throw new Error(`model ${response.status}`);
  return (await response.json()) as ModelCard;
}
