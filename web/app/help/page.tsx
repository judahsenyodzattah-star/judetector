import type { Metadata } from "next";
import Link from "next/link";

import { loadModelInfo } from "@/lib/server-api";

export const metadata: Metadata = { title: "Help" };

export default async function HelpPage() {
  const { card } = await loadModelInfo();

  return (
    <div className="stack stack--loose">
      <div className="page-header">
        <h1>Help</h1>
        <p>What this app does, what it refuses to do, and how to read a result.</p>
      </div>

      <div className="prose">
        <h2>What it does</h2>
        <p>
          You choose one image and press <strong>Analyse image</strong>. The image goes to the
          detection service, one model runs over it once, and the app shows what that model
          produced: boxes, a confidence for each box, and the time it took.
        </p>

        <h2>What it does not do</h2>
        <ul>
          <li>It does not identify anyone. A detection says a pattern matched; it is not a name.</li>
          <li>
            It is not general face recognition. The model is trained for one subject, so it is
            expected to miss everyone else.
          </li>
          <li>It does not watch a camera, scan a folder, or run anything you did not start.</li>
          <li>It does not keep history. Reloading the page clears the session.</li>
        </ul>

        {card ? (
          <>
            <h2>This model</h2>
            <p>{card.limitations}</p>
            <dl className="definition-list">
              <dt>Name</dt>
              <dd>{card.display_name}</dd>
              <dt>Labels</dt>
              <dd>{card.labels.length > 0 ? card.labels.join(", ") : "none declared"}</dd>
              <dt>Availability</dt>
              <dd>{card.available ? "loaded and ready" : "not available right now"}</dd>
            </dl>
          </>
        ) : null}

        <h2>Files and limits</h2>
        <ul>
          <li>JPG, PNG, WEBP and BMP. The format is detected from the file itself.</li>
          <li>Up to 25 MB. Larger images are refused before they are sent.</li>
          <li>Very large images are scaled down before analysis; the result says so.</li>
        </ul>

        <h2>Reading a result</h2>
        <ul>
          <li>
            <strong>Detections</strong> is a count of boxes that passed the thresholds — not a
            measure of certainty.
          </li>
          <li>
            <strong>Confidence</strong> is the model&apos;s score for that box. Lower the threshold
            to see weaker candidates.
          </li>
          <li>
            <strong>Timings</strong> are measured: model inference, the server&apos;s total, and the
            round trip from your browser. If one is missing it says so instead of showing a zero.
          </li>
        </ul>

        <h2>If something goes wrong</h2>
        <ul>
          <li>
            <strong>Analysis is unavailable</strong> — the service is up but no model is loaded.
            Nothing is invented in its place.
          </li>
          <li>
            <strong>Too many analyses</strong> — the service limits how often one visitor can
            analyse. The message says how long to wait.
          </li>
          <li>
            <strong>That image could not be read</strong> — the file is damaged or is not the format
            its name suggests.
          </li>
          <li>
            Every error shows a reference you can quote; it matches the server&apos;s log entry.
          </li>
        </ul>

        <h2>Privacy</h2>
        <p>
          Images are held in this browser tab and sent once, when you press the analysis button.
          They are processed in memory and not written to storage. There is no account, no history
          and no analytics in this build.
        </p>

        <p>
          <Link href="/detect">Go to Detect</Link>
        </p>
      </div>
    </div>
  );
}
