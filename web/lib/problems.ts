import type { Problem } from "./contracts";

export interface ProblemCopy {
  title: string;
  detail: string;
  hint?: string;
}

/**
 * Turn a problem document into something a person can act on.
 *
 * The service's own `title` and `detail` are shown as written — they are
 * already written for people and contain no internals — and this adds one
 * sentence of guidance where the next step is not obvious.
 */
export function describeProblem(problem: Problem, retryAfterSeconds?: number | null): ProblemCopy {
  const title = problem.title || "The analysis could not be completed";
  const detail = problem.detail || "The service did not return a reason.";

  switch (problem.type) {
    case "model_unavailable":
      return {
        title: "Analysis is unavailable",
        detail:
          "The service is running, but the model is not loaded, so this image was not analysed.",
        hint: "Nothing was invented in its place. Try again once the model is available.",
      };
    case "rate_limited": {
      const wait =
        retryAfterSeconds && retryAfterSeconds > 0
          ? ` Try again in ${Math.ceil(retryAfterSeconds)} seconds.`
          : " Try again shortly.";
      return {
        title: "Too many analyses in a short time",
        detail: `The service limits how often one visitor can analyse images.${wait}`,
        hint: "The limit applies per running instance, not globally.",
      };
    }
    case "payload_too_large":
      return {
        title: "That image is too large",
        detail: detail || "The upload limit is 25 MB and images above 40 megapixels are refused.",
        hint: "Resize or export a smaller copy and choose it again.",
      };
    case "unsupported_media_type":
      return {
        title: "That file type is not supported",
        detail: detail || "Only JPG, PNG, WEBP and BMP images can be analysed.",
        hint: "Converting the file to one of those formats will fix it.",
      };
    case "invalid_image":
      return {
        title: "That image could not be read",
        detail: detail || "The file could not be decoded as an image.",
        hint: "It may be truncated or damaged. Try another copy or export it again.",
      };
    case "invalid_request":
      return {
        title: "Those settings are not valid",
        detail: detail || "One of the analysis settings was outside its allowed range.",
        hint: "Reset the thresholds and try again.",
      };
    case "inference_failed":
    case "internal_error":
      return {
        title: "The analysis failed",
        detail:
          "The service hit an error while producing a result. This is a fault on our side, not in your image.",
        hint: "Trying once more is reasonable; if it keeps failing, report the reference below.",
      };
    case "unexpected_response":
      return { title, detail, hint: "This usually means a proxy or host, not the model, refused the request." };
    default:
      return { title, detail };
  }
}
