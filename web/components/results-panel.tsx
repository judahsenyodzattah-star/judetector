"use client";

import { useState } from "react";

import type { DetectResponse } from "@/lib/contracts";
import { annotatedBlob, decodeAnnotated, resultJsonBlob } from "@/lib/api";
import { downloadBlob, safeFileName } from "@/lib/download";
import {
  formatBytes,
  formatConfidence,
  formatDimensions,
  formatMegapixels,
  formatMs,
} from "@/lib/format";

import { DownloadIcon } from "./icons";

export interface ResultsPanelProps {
  result: DetectResponse;
  /** Round-trip time measured by the browser, if this result came from here. */
  clientMs: number | null;
  fileName: string;
}

export function ResultsPanel({ result, clientMs, fileName }: ResultsPanelProps) {
  const [annotation, setAnnotation] = useState<"overlay" | "server">("overlay");
  const base = safeFileName(fileName);

  return (
    <section className="results" aria-labelledby="results-heading">
      <div className="card">
        <div className="card__header">
          <h2 className="card__title" id="results-heading">
            Result
          </h2>
          <span className="tag">{result.model.display_name}</span>
        </div>

        <div className="results__summary">
          <div className="stat">
            <span className="stat__value tabular">{result.count}</span>
            <span className="stat__label">{result.count === 1 ? "detection" : "detections"}</span>
          </div>
          <div className="stat">
            <span className="stat__value tabular">{formatMs(result.timing.inference_ms)}</span>
            <span className="stat__label">Model inference</span>
          </div>
          <div className="stat">
            <span className="stat__value tabular">{formatMs(result.timing.total_ms)}</span>
            <span className="stat__label">Server, end to end</span>
          </div>
          <div className="stat">
            <span className="stat__value tabular">{formatMs(clientMs)}</span>
            <span className="stat__label">Round trip from this browser</span>
          </div>
        </div>

        {result.detections.length > 0 ? (
          <ul className="detection-list" aria-label="Detections">
            {result.detections.map((detection, index) => (
              <li className="detection" key={`${detection.label}-${index}`}>
                <span className="detection__label">{detection.label}</span>
                <span className="detection__box">
                  {Math.round(detection.box.x1)}, {Math.round(detection.box.y1)} →{" "}
                  {Math.round(detection.box.x2)}, {Math.round(detection.box.y2)} px
                </span>
                <span className="detection__confidence">
                  {formatConfidence(detection.confidence)}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">
            Nothing matched the model at these thresholds. That is a real answer, not an error —
            raise the confidence threshold to widen the search.
          </p>
        )}

        {result.warnings && result.warnings.length > 0 ? (
          <div className="stack stack--tight" style={{ marginTop: "var(--space-4)" }}>
            {result.warnings.map((warning) => (
              <div className="notice notice--warning" key={warning} role="status">
                <p className="notice__detail">{warning}</p>
              </div>
            ))}
          </div>
        ) : null}

        <hr className="section-rule" />

        <div className="actions">
          <button
            type="button"
            className="button button--quiet"
            onClick={() => downloadBlob(resultJsonBlob(result), `${base}-result.json`)}
          >
            <DownloadIcon /> Download detections (JSON)
          </button>
        </div>
        <p className="muted" style={{ marginTop: "var(--space-2)", fontSize: "var(--step-1)" }}>
          Request reference <span className="tabular">{result.request_id}</span>
        </p>
      </div>

      <div className="card">
        <div className="card__header">
          <h2 className="card__title">Image and annotation</h2>
          <div className="segmented" role="group" aria-label="Image view">
            <button
              type="button"
              aria-pressed={annotation === "overlay"}
              onClick={() => setAnnotation("overlay")}
            >
              Boxes in this app
            </button>
            <button
              type="button"
              aria-pressed={annotation === "server"}
              onClick={() => setAnnotation("server")}
              disabled={!result.annotated}
            >
              Annotated PNG
            </button>
          </div>
        </div>

        {annotation === "server" && result.annotated ? (
          <div className="stack stack--tight">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              className="stage__image"
              src={decodeAnnotated(result.annotated.data)}
              alt={`Annotated copy of ${fileName} with ${result.count} detection boxes drawn by the service`}
            />
            <div className="actions">
              <button
                type="button"
                className="button"
                onClick={() =>
                  downloadBlob(annotatedBlob(result.annotated!.data), `${base}-annotated.png`)
                }
              >
                <DownloadIcon /> Download annotated PNG
              </button>
              <span className="muted" style={{ fontSize: "var(--step-1)" }}>
                {formatBytes(result.annotated.bytes)} PNG, drawn by the service
              </span>
            </div>
          </div>
        ) : result.annotated ? (
          <p className="muted">
            Boxes are drawn in this tab from the coordinates the service returned, so they scale
            with the window. The service can also draw its own PNG — open the second view to see
            and download it.
          </p>
        ) : (
          <div className="notice notice--warning" role="status">
            <p className="notice__title">The annotated image was not returned</p>
            <p className="notice__detail">
              This image produced an annotation larger than the service will send back, so it was
              left out. The detections above are complete.
            </p>
          </div>
        )}

        <hr className="section-rule" />

        <table className="table">
          <caption>What was analysed</caption>
          <tbody>
            <tr>
              <th scope="row">Analysed size</th>
              <td>{formatDimensions(result.image.width, result.image.height)}</td>
            </tr>
            <tr>
              <th scope="row">Uploaded size</th>
              <td>
                {formatDimensions(result.image.source_width, result.image.source_height)}
                {result.image.downscaled ? " (scaled down before analysis)" : ""}
              </td>
            </tr>
            <tr>
              <th scope="row">Pixels analysed</th>
              <td>{formatMegapixels(result.image.megapixels)}</td>
            </tr>
            <tr>
              <th scope="row">Upload size</th>
              <td>{formatBytes(result.image.bytes)}</td>
            </tr>
            <tr>
              <th scope="row">Thresholds used</th>
              <td>
                confidence {result.thresholds.confidence.toFixed(2)}, IoU{" "}
                {result.thresholds.iou.toFixed(2)}
              </td>
            </tr>
            <tr>
              <th scope="row">Labels</th>
              <td>
                {result.model.labels.join(", ") || "none declared"} (
                {result.model.labels_source})
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  );
}
