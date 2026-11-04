/** Browser-only downloads from in-memory data. Nothing is stored server-side. */

export function downloadBlob(blob: Blob, filename: string): string {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.rel = "noopener";
  anchor.style.display = "none";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  return url;
}

export function safeFileName(name: string): string {
  const base = name.replace(/\.[^.]+$/, "").replace(/[^a-zA-Z0-9-_]+/g, "-").slice(0, 60);
  return base || "image";
}
