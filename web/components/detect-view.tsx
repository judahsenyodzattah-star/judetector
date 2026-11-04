"use client";

import { useState } from "react";

import { ApiProblemError, detectImage } from "@/lib/api";
import type { DetectResponse, ModelInfo, Problem } from "@/lib/contracts";
import { formatBytes, formatMs } from "@/lib/format";
import { useSession } from "@/lib/session";

import { DetectionOverlay } from "./detection-overlay";
import { ModelUnavailableNotice, availabilityOf } from "./model-status";
import { ProblemNotice } from "./problem-notice";
import { ResultsPanel } from "./results-panel";
import { Uploader } from "./uploader";

interface Failure {
  problem: Problem;
  retryAfterSeconds: number | null;
  requestId: string | null;
}

export function DetectView({ modelInfo }: { modelInfo: ModelInfo }) {
  const {
    staged,
    result,
    setResult,
    stage,
    thresholds,
    setThresholds,
    includeAnnotated,
    setIncludeAnnotated,
  } = useSession();

  const [pending, setPending] = useState(false);
  const [failure, setFailure] = useState<Failure | null>(null);
  const [clientMs, setClientMs] = useState<number | null>(null);
  const [showLabels, setShowLabels] = useState(true);

  const availability = availabilityOf(modelInfo);
  const unavailable = availability === "unavailable";
  const canAnalyse = Boolean(staged) && !pending && !unavailable;

  async function analyse() {
    if (!staged) return;
    setPending(true);
    setFailure(null);
    try {
      const { result: next, meta } = await detectImage({
        file: staged.file,
        confidence: thresholds.confidence,
        iou: thresholds.iou,
        includeAnnotated,
      });
      setResult(next);
      setClientMs(meta.clientMs);
    } catch (error) {
      if (error instanceof ApiProblemError) {
        setFailure({
          problem: error.problem,
          retryAfterSeconds: error.meta.retryAfterSeconds,
          requestId: error.meta.requestId,
        });
      } else {
        setFailure({
          problem: {
            type: "internal_error",
            title: "The analysis could not be completed",
            status: 0,
            detail: "Something interrupted the request before it finished.",
            request_id: "",
          },
          retryAfterSeconds: null,
          requestId: null,
        });
      }
      // A previous successful result stays on screen: it is still a real result
      // for this image, and the error above explains why a new one is missing.
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="stack stack--loose">
      <div className="page-header">
        <h1>Detect</h1>
        <p>
          One image, one explicit analysis. The result reports what the model produced and how long
          it took — never an estimate.
        </p>
      </div>

      {availability !== "ok" ? <ModelUnavailableNotice info={modelInfo} /> : null}

      <div className="split">
        <div className="stack">
          <div className="stage">
            {staged ? (
              <>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  className="stage__image"
                  src={staged.url}
                  alt={`Staged image ${staged.name}`}
                />
                {result ? <DetectionOverlay detections={result.detections} showLabels={showLabels} /> : null}
              </>
            ) : (
              <div className="stage__empty">
                <p className="uploader__title">No image staged</p>
                <p>Choose a photo to begin. It stays in this tab until you analyse it.</p>
                <Uploader onSelect={stage} compact />
              </div>
            )}
          </div>

          {staged ? (
            <div className="actions">
              <span className="muted" style={{ fontSize: "var(--step-1)" }}>
                {staged.name} · {formatBytes(staged.size)}
              </span>
              {result ? (
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={showLabels}
                    onChange={(event) => setShowLabels(event.target.checked)}
                  />
                  Show labels on boxes
                </label>
              ) : null}
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={includeAnnotated}
                  onChange={(event) => setIncludeAnnotated(event.target.checked)}
                />
                Ask the service for its annotated PNG
              </label>
            </div>
          ) : null}
        </div>

        <aside className="stack" aria-label="Analysis controls">
          <div className="card stack">
            <div className="field">
              <div className="field__row">
                <label className="field__label" htmlFor="confidence">
                  Confidence threshold
                </label>
                <span className="field__value">{thresholds.confidence.toFixed(2)}</span>
              </div>
              <input
                id="confidence"
                type="range"
                min={0.01}
                max={0.99}
                step={0.01}
                value={thresholds.confidence}
                onChange={(event) =>
                  setThresholds({ confidence: Number(event.target.value) })
                }
              />
              <p className="field__help">
                Lower values find more candidates and more false positives.
              </p>
            </div>

            <div className="field">
              <div className="field__row">
                <label className="field__label" htmlFor="iou">
                  Overlap threshold (IoU)
                </label>
                <span className="field__value">{thresholds.iou.toFixed(2)}</span>
              </div>
              <input
                id="iou"
                type="range"
                min={0.1}
                max={0.95}
                step={0.01}
                value={thresholds.iou}
                onChange={(event) => setThresholds({ iou: Number(event.target.value) })}
              />
              <p className="field__help">
                How much two boxes may overlap before one is dropped.
              </p>
            </div>

            <button type="button" className="button" onClick={analyse} disabled={!canAnalyse}>
              {pending ? "Analysing…" : "Analyse image"}
            </button>
            {!staged ? (
              <p className="field__help">Choose an image first.</p>
            ) : unavailable ? (
              <p className="field__help">
                Analysis is unavailable while the model is not loaded.
              </p>
            ) : (
              <p className="field__help">
                Nothing runs until you press this. Changing thresholds does not re-run it.
              </p>
            )}
          </div>

          {failure ? (
            <ProblemNotice
              problem={failure.problem}
              retryAfterSeconds={failure.retryAfterSeconds}
              requestId={failure.requestId}
            />
          ) : null}
        </aside>
      </div>

      {result ? (
        <ResultsPanel result={result} clientMs={clientMs} fileName={staged?.name ?? "image"} />
      ) : null}

      {modelInfo.card ? (
        <section className="card" aria-labelledby="limits-heading">
          <div className="card__header">
            <h2 className="card__title" id="limits-heading">
              What this result can and cannot tell you
            </h2>
            <span className="tag">
              {modelInfo.card.labels.length > 0
                ? modelInfo.card.labels.join(", ")
                : "no labels declared"}
            </span>
          </div>
          <p>{modelInfo.card.limitations}</p>
          <p className="muted" style={{ marginTop: "var(--space-2)" }}>
            Confidences are this model&apos;s scores for these boxes. They are not a probability
            that a person is in the photo, and a detection is not an identification.
          </p>
        </section>
      ) : null}
    </div>
  );
}
