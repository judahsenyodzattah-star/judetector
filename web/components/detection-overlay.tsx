import type { Detection } from "@/lib/contracts";
import { formatConfidence } from "@/lib/format";

export function DetectionOverlay({
  detections,
  showLabels,
}: {
  detections: Detection[];
  showLabels: boolean;
}) {
  if (detections.length === 0) return null;

  return (
    <>
      <svg
        className="stage__overlay"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        aria-hidden="true"
        data-testid="detection-overlay"
      >
        {detections.map((detection, index) => {
          const { x1, y1, x2, y2 } = detection.box_norm;
          return (
            <rect
              key={`${detection.label}-${index}`}
              className="overlay-box"
              x={x1 * 100}
              y={y1 * 100}
              width={Math.max(0, x2 - x1) * 100}
              height={Math.max(0, y2 - y1) * 100}
            />
          );
        })}
      </svg>
      {showLabels
        ? detections.map((detection, index) => {
            const { x1, y1, x2 } = detection.box_norm;
            return (
              <span
                key={`label-${detection.label}-${index}`}
                className="overlay-tag"
                style={{
                  left: `${Math.min(Math.max(x1, 0), 1) * 100}%`,
                  top: `${Math.min(Math.max(y1, 0), 1) * 100}%`,
                  maxWidth: `${Math.min(Math.max(x2 - x1, 0.12), 1) * 100}%`,
                }}
              >
                {detection.label} · {formatConfidence(detection.confidence)}
              </span>
            );
          })
        : null}
    </>
  );
}
