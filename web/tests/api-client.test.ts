import {
  ApiProblemError,
  activeTransport,
  annotatedBlob,
  detectEndpoint,
  detectImage,
} from "@/lib/api";

import { detectResponse, fileOf } from "./helpers";

function jsonResponse(body: unknown, init: ResponseInit = {}): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "content-type": "application/json" },
    ...init,
  });
}

describe("transport", () => {
  it("uses the same-origin proxy when no API origin is configured", () => {
    expect(activeTransport()).toBe("proxy");
    expect(detectEndpoint("proxy")).toBe("/api/detect");
  });

  it("addresses the API directly, with no double slash, when one is", () => {
    expect(detectEndpoint("direct", "https://api.example.com")).toBe(
      "https://api.example.com/v1/detect",
    );
  });
});

describe("detectImage", () => {
  it("sends one multipart request with the chosen thresholds", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(detectResponse));
    vi.stubGlobal("fetch", fetchMock);

    const file = fileOf("portrait.png");
    const outcome = await detectImage({
      file,
      confidence: 0.4,
      iou: 0.6,
      includeAnnotated: false,
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/detect");
    const body = init.body as FormData;
    expect(body.get("file")).toBeInstanceOf(File);
    expect(body.get("confidence")).toBe("0.4");
    expect(body.get("iou")).toBe("0.6");
    expect(body.get("include_annotated")).toBe("false");
    expect(outcome.result.count).toBe(detectResponse.count);
    expect(outcome.meta.clientMs).toBeGreaterThanOrEqual(0);

    vi.unstubAllGlobals();
  });

  it("turns a problem document into a typed error with its retry hint", async () => {
    const problem = {
      type: "rate_limited",
      title: "Too many requests",
      status: 429,
      detail: "The limit is 30 analyses per minute on this instance.",
      request_id: "req-429",
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(problem), {
          status: 429,
          headers: { "content-type": "application/problem+json", "retry-after": "60" },
        }),
      ),
    );

    const error = await detectImage({
      file: fileOf("a.png"),
      confidence: 0.25,
      iou: 0.45,
      includeAnnotated: true,
    }).catch((caught: unknown) => caught);

    expect(error).toBeInstanceOf(ApiProblemError);
    const problemError = error as ApiProblemError;
    expect(problemError.problem.type).toBe("rate_limited");
    expect(problemError.meta.retryAfterSeconds).toBe(60);
    expect(problemError.meta.requestId).toBe("req-429");

    vi.unstubAllGlobals();
  });

  it("explains a host-level 413 that never reached the service", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("Too large", { status: 413, headers: { "content-type": "text/plain" } })),
    );

    const error = (await detectImage({
      file: fileOf("a.png"),
      confidence: 0.25,
      iou: 0.45,
      includeAnnotated: true,
    }).catch((caught: unknown) => caught)) as ApiProblemError;

    expect(error.problem.type).toBe("payload_too_large");
    expect(error.problem.detail).toContain("4.5 MB");

    vi.unstubAllGlobals();
  });

  it("reports an unreachable service in words a person can act on", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    const error = (await detectImage({
      file: fileOf("a.png"),
      confidence: 0.25,
      iou: 0.45,
      includeAnnotated: true,
    }).catch((caught: unknown) => caught)) as ApiProblemError;

    expect(error.problem.status).toBe(0);
    expect(error.problem.detail).toContain("could not be reached");

    vi.unstubAllGlobals();
  });

  it("lets an abort through untouched", async () => {
    const abortError = new DOMException("aborted", "AbortError");
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(abortError));

    await expect(
      detectImage({ file: fileOf("a.png"), confidence: 0.25, iou: 0.45, includeAnnotated: true }),
    ).rejects.toBe(abortError);

    vi.unstubAllGlobals();
  });
});

describe("annotation helpers", () => {
  it("decodes base64 into a PNG blob", async () => {
    const blob = annotatedBlob("aGVsbG8=");
    expect(blob.type).toBe("image/png");
    expect(await blob.text()).toBe("hello");
  });
});
