import type { ModelInfo } from "@/lib/contracts";

export type Availability = "ok" | "unavailable" | "unknown";

export function availabilityOf(info: ModelInfo): Availability {
  if (!info.serviceReachable) return "unknown";
  if (info.health?.status === "ok" && info.health.model?.available) return "ok";
  return "unavailable";
}

/** Two words and a dot — never a claim the service has not made. */
export function ModelStatusLine({ info }: { info: ModelInfo }) {
  const state = availabilityOf(info);
  const label =
    state === "ok"
      ? "Model available"
      : state === "unavailable"
        ? "Model unavailable"
        : "Status unknown";

  return (
    <span className="status-line">
      <span className="status-dot" data-state={state} aria-hidden="true" />
      <span>{label}</span>
    </span>
  );
}

/** The full unavailable explanation, used where analysis is meant to happen. */
export function ModelUnavailableNotice({ info }: { info: ModelInfo }) {
  if (availabilityOf(info) === "ok") return null;

  const unknown = availabilityOf(info) === "unknown";
  return (
    <div className="notice notice--warning" role="status">
      <p className="notice__title">
        {unknown ? "The analysis service could not be reached" : "Analysis is unavailable"}
      </p>
      <p className="notice__detail">
        {unknown
          ? "This page could not read the service status. You can still choose an image, but analysis may fail until the connection returns."
          : "The service is running but no model is loaded, so nothing can be analysed right now. Choosing an image is still safe — no result will be invented to fill the gap."}
      </p>
    </div>
  );
}
