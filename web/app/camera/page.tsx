import type { Metadata } from "next";
import Link from "next/link";

import { CameraIcon } from "@/components/icons";

export const metadata: Metadata = { title: "Camera" };

export default function CameraPage() {
  return (
    <div className="stack stack--loose">
      <div className="page-header">
        <h1>Camera</h1>
        <p>Live capture is not part of this build.</p>
      </div>

      <section className="card stack" aria-labelledby="camera-state">
        <div className="card__header">
          <h2 className="card__title" id="camera-state">
            Nothing is simulated here
          </h2>
          <CameraIcon style={{ color: "var(--ink-faint)" }} />
        </div>
        <p>
          This page does not open your camera and does not draw a viewfinder it cannot fill. Camera
          capture arrives with the mobile and camera stage, once the upload path used by Detect has
          been validated on a real device.
        </p>
        <p className="muted">
          The prototype&apos;s camera input and this web app both feed the same detection service,
          so the results will be identical when capture is added.
        </p>
        <div className="actions">
          <Link className="button" href="/detect">
            Analyse a photo instead
          </Link>
          <Link className="button button--quiet" href="/help">
            How analysis works
          </Link>
        </div>
      </section>
    </div>
  );
}
