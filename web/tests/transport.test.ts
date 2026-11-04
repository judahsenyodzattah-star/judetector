/**
 * The approved production transport: detection goes straight from the browser
 * to the API; the same-origin proxy is a local-development convenience.
 */

import { fileOf, detectResponse } from "./helpers";

const API = "https://api.judetector.example";

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}

async function freshApi() {
  vi.resetModules();
  return import("@/lib/api");
}

beforeEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.resetModules();
});

describe("production transport", () => {
  it("addresses the API directly when an origin is configured", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", API);
    const api = await freshApi();

    expect(api.activeTransport()).toBe("direct");
    expect(api.detectEndpoint()).toBe(`${API}/v1/detect`);
  });

  it("never routes a detection upload through the web host", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", API);
    const api = await freshApi();

    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(detectResponse));
    vi.stubGlobal("fetch", fetchMock);

    await api.detectImage({
      file: fileOf("portrait.png"),
      confidence: 0.25,
      iou: 0.45,
      includeAnnotated: true,
    });

    const [url] = fetchMock.mock.calls[0];
    expect(url).toBe(`${API}/v1/detect`);
    expect(url).not.toContain("/api/detect");
  });

  it("tolerates a trailing slash on the configured origin", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", `${API}/`);
    const api = await freshApi();
    expect(api.detectEndpoint()).toBe(`${API}/v1/detect`);
  });

  it("uses the local proxy when no origin is configured", async () => {
    const api = await freshApi();
    expect(api.activeTransport()).toBe("proxy");
    expect(api.detectEndpoint()).toBe("/api/detect");
  });

  it("lets local development force the proxy even with an origin set", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", API);
    vi.stubEnv("NEXT_PUBLIC_DETECT_TRANSPORT", "proxy");
    const api = await freshApi();

    expect(api.activeTransport()).toBe("proxy");
    expect(api.detectEndpoint()).toBe("/api/detect");
  });

  it("does not add headers that would force a preflight", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", API);
    const api = await freshApi();

    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(detectResponse));
    vi.stubGlobal("fetch", fetchMock);

    await api.detectImage({
      file: fileOf("portrait.png"),
      confidence: 0.25,
      iou: 0.45,
      includeAnnotated: true,
    });

    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers).toBeUndefined();
    expect(init.body).toBeInstanceOf(FormData);
    expect(init.credentials).toBeUndefined();
  });
});
