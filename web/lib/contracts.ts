/**
 * Types mirroring the FastAPI contract in `api/schemas`.
 *
 * They are hand-written rather than generated so the web app cannot drift
 * silently: `tests/contracts.test.ts` compares these against the API's
 * `/openapi.json` when a schema fixture is present, and every field here is
 * named exactly as the API sends it.
 */

export type ModelKind = "subject_specific" | "general_purpose" | string;
export type LabelsSource = "model" | "declared" | "unknown" | string;

export interface Box {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface Detection {
  label: string;
  confidence: number;
  box: Box;
  box_norm: Box;
}

export interface ImageInfo {
  width: number;
  height: number;
  source_width: number;
  source_height: number;
  downscaled: boolean;
  bytes: number;
  megapixels: number;
}

export interface ModelRef {
  id: string;
  display_name: string;
  kind: ModelKind;
  labels: string[];
  labels_source: LabelsSource;
}

export interface Thresholds {
  confidence: number;
  iou: number;
}

export interface Timing {
  inference_ms: number | null;
  total_ms: number | null;
}

export interface AnnotatedImage {
  mime: string;
  encoding: string;
  width: number;
  height: number;
  bytes: number;
  data: string;
}

export interface DetectResponse {
  request_id: string;
  model: ModelRef;
  image: ImageInfo;
  thresholds: Thresholds;
  count: number;
  detections: Detection[];
  timing: Timing;
  annotated?: AnnotatedImage | null;
  warnings?: string[];
}

export interface ModelStatus {
  id: string;
  available: boolean;
  loaded: boolean;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  service: string;
  version: string;
  uptime_s: number;
  model?: ModelStatus | null;
}

export interface ModelCard {
  id: string;
  display_name: string;
  kind: ModelKind;
  task: string;
  labels: string[];
  labels_source: LabelsSource;
  available: boolean;
  limitations: string;
  metrics?: Record<string, unknown> | null;
}

export interface Problem {
  type: string;
  title: string;
  status: number;
  detail: string;
  request_id: string;
}

/**
 * What the app knows about the model at page load. `null` means the status
 * could not be read — which is not the same as "unavailable", and is never
 * rendered as if it were.
 */
export interface ModelInfo {
  health: HealthResponse | null;
  card: ModelCard | null;
  serviceReachable: boolean;
}
