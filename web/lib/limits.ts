/** Client-side upload rules, mirroring the API's own guards. */

/**
 * The API accepts 25 MB (`JUDETECTOR_MAX_UPLOAD_MB`). The browser checks the
 * same number so an oversized file is caught before it is sent — the server
 * remains the authority and rejects it independently.
 */
export const MAX_UPLOAD_BYTES = 25 * 1024 * 1024;

export const ACCEPTED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp", ".bmp"] as const;

export const ACCEPT_ATTRIBUTE = ["image/jpeg", "image/png", "image/webp", "image/bmp"].join(",");

export const FORMAT_LABEL = "JPG, PNG, WEBP or BMP";

/**
 * The API detects the real format from the bytes and ignores the filename, so
 * this is only a courtesy check that keeps obvious mistakes from being uploaded.
 */
export function rejectionFor(file: File): string | null {
  const name = file.name.toLowerCase();
  const extensionOk = ACCEPTED_EXTENSIONS.some((extension) => name.endsWith(extension));
  if (!extensionOk) {
    return `That file type is not supported. Choose a ${FORMAT_LABEL} image.`;
  }
  if (file.size === 0) {
    return "That file is empty.";
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    return `That image is ${formatMegabytes(file.size)}. The limit is 25 MB.`;
  }
  return null;
}

function formatMegabytes(bytes: number): string {
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
