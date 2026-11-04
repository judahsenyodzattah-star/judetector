/** Number formatting. Unmeasured values are said to be unmeasured. */

export function formatMs(value: number | null | undefined): string {
  if (value === null || value === undefined) return "not measured";
  if (value < 1) return "<1 ms";
  if (value < 10) return `${value.toFixed(1)} ms`;
  return `${Math.round(value)} ms`;
}

export function formatConfidence(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatMegapixels(value: number): string {
  return `${value.toFixed(1)} MP`;
}

export function formatDimensions(width: number, height: number): string {
  return `${width} × ${height}`;
}

export function fileNameWithoutExtension(name: string): string {
  return name.replace(/\.[^.]+$/, "");
}
