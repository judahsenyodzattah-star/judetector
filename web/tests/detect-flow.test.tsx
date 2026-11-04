import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DetectView } from "@/components/detect-view";
import { ApiProblemError, detectImage } from "@/lib/api";
import type { Problem } from "@/lib/contracts";
import { formatConfidence, formatMs } from "@/lib/format";

import {
  captureDownloads,
  detectResponse,
  fileOf,
  modelInfo,
  modelInfoDegraded,
  renderWithSession,
} from "./helpers";

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return { ...actual, detectImage: vi.fn() };
});

const detectMock = vi.mocked(detectImage);

function stage(name = "portrait.png") {
  fireEvent.change(screen.getByLabelText("Choose an image file"), {
    target: { files: [fileOf(name)] },
  });
}

function analyseButton(): HTMLButtonElement {
  return screen.getByRole("button", { name: /analyse/i }) as HTMLButtonElement;
}

function problem(overrides: Partial<Problem>): Problem {
  return {
    type: "invalid_image",
    title: "Image could not be read",
    status: 422,
    detail: "That file could not be decoded as an image.",
    request_id: "req-1",
    ...overrides,
  };
}

beforeEach(() => {
  detectMock.mockReset();
});

describe("explicit analysis", () => {
  it("stages an image without analysing it, and waits for the button", async () => {
    renderWithSession(<DetectView modelInfo={modelInfo()} />);
    stage();

    expect(detectMock).not.toHaveBeenCalled();
    expect(analyseButton()).toBeEnabled();

    await userEvent.click(analyseButton());

    expect(detectMock).toHaveBeenCalledTimes(1);
    const sent = detectMock.mock.calls[0][0];
    expect(sent.file.name).toBe("portrait.png");
    expect(sent.confidence).toBe(0.25);
    expect(sent.iou).toBe(0.45);
    expect(sent.includeAnnotated).toBe(true);
  });

  it("does not run when a threshold changes", async () => {
    renderWithSession(<DetectView modelInfo={modelInfo()} />);
    stage();

    const slider = screen.getByLabelText("Confidence threshold");
    fireEvent.change(slider, { target: { value: "0.6" } });

    expect(detectMock).not.toHaveBeenCalled();
    expect(screen.getByText("0.60")).toBeInTheDocument();
  });

  it("cannot analyse before an image is chosen", () => {
    renderWithSession(<DetectView modelInfo={modelInfo()} />);
    expect(analyseButton()).toBeDisabled();
    expect(screen.getByText("Choose an image first.")).toBeInTheDocument();
  });

  it("shows progress and sends the current thresholds", async () => {
    let resolve: (value: Awaited<ReturnType<typeof detectImage>>) => void = () => {};
    detectMock.mockImplementation(
      () => new Promise((done) => { resolve = done; }),
    );

    renderWithSession(<DetectView modelInfo={modelInfo()} />);
    stage();
    fireEvent.change(screen.getByLabelText("Overlap threshold (IoU)"), { target: { value: "0.7" } });

    await userEvent.click(analyseButton());

    expect(screen.getByRole("button", { name: /analysing/i })).toBeDisabled();
    expect(detectMock.mock.calls[0][0].iou).toBeCloseTo(0.7);

    resolve({
      result: detectResponse,
      meta: { requestId: detectResponse.request_id, retryAfterSeconds: null, clientMs: 812.4 },
    });
    await waitFor(() => expect(analyseButton()).toBeEnabled());
  });
});

describe("results", () => {
  async function analyseWithFixture() {
    detectMock.mockResolvedValue({
      result: detectResponse,
      meta: { requestId: detectResponse.request_id, retryAfterSeconds: null, clientMs: 812.4 },
    });
    renderWithSession(<DetectView modelInfo={modelInfo()} />);
    stage();
    await userEvent.click(analyseButton());
    await screen.findByRole("heading", { name: "Result" });
  }

  it("reports the count, confidences and measured timings verbatim", async () => {
    await analyseWithFixture();

    expect(screen.getByText(String(detectResponse.count))).toBeInTheDocument();
    expect(screen.getByText(formatMs(detectResponse.timing.inference_ms))).toBeInTheDocument();
    expect(screen.getByText(formatMs(detectResponse.timing.total_ms))).toBeInTheDocument();
    expect(screen.getByText(formatMs(812.4))).toBeInTheDocument(); // browser round trip
    for (const detection of detectResponse.detections) {
      expect(screen.getAllByText(formatConfidence(detection.confidence)).length).toBeGreaterThan(0);
    }
  });

  it("draws one box per detection over the staged image", async () => {
    await analyseWithFixture();
    const overlay = screen.getByTestId("detection-overlay");
    expect(overlay.querySelectorAll("rect")).toHaveLength(detectResponse.detections.length);
  });

  it("offers the service's annotated PNG and downloads it", async () => {
    const downloads = captureDownloads();
    await analyseWithFixture();

    await userEvent.click(screen.getByRole("button", { name: "Annotated PNG" }));
    const image = screen.getByAltText(/annotated copy/i) as HTMLImageElement;
    expect(image.src.startsWith("data:image/png;base64,")).toBe(true);

    await userEvent.click(screen.getByRole("button", { name: /download annotated png/i }));
    expect(downloads.at(-1)?.download).toBe("portrait-annotated.png");
  });

  it("downloads the detections as JSON", async () => {
    const downloads = captureDownloads();
    await analyseWithFixture();

    await userEvent.click(screen.getByRole("button", { name: /download detections/i }));
    expect(downloads.at(-1)?.download).toBe("portrait-result.json");
    expect(downloads.at(-1)?.href).toContain("blob:");
  });
});

describe("errors", () => {
  async function failWith(problemDoc: Problem, retryAfterSeconds: number | null = null) {
    detectMock.mockRejectedValue(
      new ApiProblemError(problemDoc, { requestId: problemDoc.request_id, retryAfterSeconds }),
    );
    renderWithSession(<DetectView modelInfo={modelInfo()} />);
    stage();
    await userEvent.click(analyseButton());
    return screen.findByRole("alert");
  }

  it("explains an unavailable model without inventing a result", async () => {
    const alert = await failWith(
      problem({
        type: "model_unavailable",
        title: "Analysis is unavailable",
        status: 503,
        detail: "This service cannot run the configured model right now.",
      }),
    );

    expect(alert).toHaveTextContent("Analysis is unavailable");
    expect(alert).toHaveTextContent("the model is not loaded");
    expect(alert).toHaveTextContent("Nothing was invented");
    expect(screen.queryByRole("heading", { name: "Result" })).not.toBeInTheDocument();
  });

  it("says how long to wait when the limit is reached", async () => {
    const alert = await failWith(
      problem({
        type: "rate_limited",
        title: "Too many requests",
        status: 429,
        detail: "The limit is 30 analyses per minute on this instance.",
      }),
      42,
    );

    expect(alert).toHaveTextContent("Try again in 42 seconds");
  });

  it("explains an oversized upload", async () => {
    const alert = await failWith(
      problem({
        type: "payload_too_large",
        title: "Request is too large",
        status: 413,
        detail: "Requests must be at most 25 MB plus multipart overhead.",
      }),
    );

    expect(alert).toHaveTextContent("That image is too large");
    expect(alert).toHaveTextContent("Resize or export a smaller copy");
  });

  it("explains an unreadable image and keeps the reference", async () => {
    const alert = await failWith(problem({ request_id: "abc123" }));
    expect(alert).toHaveTextContent("That image could not be read");
    expect(alert).toHaveTextContent("Reference abc123");
  });
});

describe("model availability", () => {
  it("stops analysis and says why when the model is not loaded", () => {
    renderWithSession(<DetectView modelInfo={modelInfoDegraded()} />);
    stage();

    expect(analyseButton()).toBeDisabled();
    expect(screen.getByText("Analysis is unavailable")).toBeInTheDocument();
    expect(
      screen.getByText("Analysis is unavailable while the model is not loaded."),
    ).toBeInTheDocument();
  });

  it("still allows an attempt when the status could not be read", () => {
    renderWithSession(<DetectView modelInfo={{ health: null, card: null, serviceReachable: false }} />);
    stage();
    expect(analyseButton()).toBeEnabled();
    expect(screen.getByText("The analysis service could not be reached")).toBeInTheDocument();
  });
});
