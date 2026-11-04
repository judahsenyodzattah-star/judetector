"use client";

import Link from "next/link";

import { formatBytes, formatMs } from "@/lib/format";
import { useSession } from "@/lib/session";

export function SessionPanel() {
  const { staged, result, clearStaged } = useSession();

  return (
    <section className="session" aria-labelledby="session-heading">
      <h2 className="session__heading" id="session-heading">
        This session
      </h2>

      {staged ? (
        <div className="stack stack--tight">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img className="session__thumb" src={staged.url} alt={`Preview of ${staged.name}`} />
          <p className="session__filename">{staged.name}</p>
          <p className="session__file">{formatBytes(staged.size)}</p>
          <div className="uploader__actions" style={{ justifyContent: "flex-start" }}>
            <Link className="button button--quiet" href="/detect">
              Open in Detect
            </Link>
            <button type="button" className="button button--link" onClick={clearStaged}>
              Remove
            </button>
          </div>
        </div>
      ) : (
        <p className="session__empty">
          No image yet. Choosing one here stages it for Detect — it is not analysed until you
          ask.
        </p>
      )}

      <hr className="section-rule" style={{ margin: 0 }} />

      {result ? (
        <div className="stack stack--tight">
          <p className="eyebrow">Last analysis</p>
          <p className="session__count">
            {result.count} {result.count === 1 ? "detection" : "detections"}
          </p>
          <p className="session__file">
            {result.model.display_name} · {formatMs(result.timing.total_ms)} on the server
          </p>
          <Link className="button button--link" href="/detect" style={{ justifySelf: "start" }}>
            View the result
          </Link>
        </div>
      ) : (
        <p className="session__empty">No analysis yet. Results appear here after you run one.</p>
      )}

      <p className="session__file">
        Images stay in this tab. Nothing is uploaded to storage and a reload clears the session.
      </p>
    </section>
  );
}
