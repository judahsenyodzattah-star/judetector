/**
 * Same-origin proxy for `POST /v1/detect`.
 *
 * Works on any host that allows a large request body — a laptop, a container,
 * a Node server. It is **not** usable for a 25 MB upload on Vercel: Vercel
 * Functions cap a request body at 4.5 MB (`FUNCTION_PAYLOAD_TOO_LARGE`), so a
 * deployment there must set `NEXT_PUBLIC_API_BASE_URL` and send the file
 * directly to the API (see `docs/WEB.md`). When this route runs on Vercel and
 * the body is above that limit, it says so instead of failing opaquely.
 */

import type { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const API_BASE = (
  process.env.API_INTERNAL_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000"
).replace(/\/+$/, "");

/** Vercel's documented Function request-body limit. It cannot be raised. */
const VERCEL_BODY_LIMIT = 4.5 * 1024 * 1024;

const PASS_THROUGH_HEADERS = [
  "content-type",
  "x-request-id",
  "ratelimit-limit",
  "ratelimit-remaining",
  "ratelimit-reset",
  "ratelimit-scope",
  "retry-after",
  "server-timing",
  "cache-control",
  "x-content-type-options",
];

function problem(status: number, type: string, title: string, detail: string): Response {
  return new Response(
    JSON.stringify({
      type,
      title,
      status,
      detail,
      request_id: "",
    }),
    {
      status,
      headers: {
        "content-type": "application/problem+json",
        "cache-control": "no-store",
        "x-content-type-options": "nosniff",
      },
    },
  );
}

export async function POST(request: NextRequest): Promise<Response> {
  const declared = Number(request.headers.get("content-length") ?? "0");

  if (process.env.VERCEL && declared > VERCEL_BODY_LIMIT) {
    return problem(
      413,
      "upload_over_proxy_limit",
      "This upload cannot pass through the web host",
      "Vercel Functions accept at most 4.5 MB per request, so a 25 MB image cannot be proxied. Send the file directly to the analysis service.",
    );
  }

  if (!request.body) {
    return problem(422, "invalid_request", "No image was received", "The request body was empty.");
  }

  const upstreamHeaders = new Headers();
  for (const name of ["content-type", "x-request-id"]) {
    const value = request.headers.get(name);
    if (value) upstreamHeaders.set(name, value);
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${API_BASE}/v1/detect`, {
      method: "POST",
      headers: upstreamHeaders,
      body: request.body,
      cache: "no-store",
      // Required when forwarding a stream as the request body.
      duplex: "half",
    } as RequestInit & { duplex: "half" });
  } catch {
    return problem(
      502,
      "upstream_unreachable",
      "The analysis service could not be reached",
      "The web app is running, but it could not contact the inference service.",
    );
  }

  const headers = new Headers();
  for (const name of PASS_THROUGH_HEADERS) {
    const value = upstream.headers.get(name);
    if (value) headers.set(name, value);
  }

  return new Response(upstream.body, { status: upstream.status, headers });
}
