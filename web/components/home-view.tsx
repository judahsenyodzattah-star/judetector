"use client";

import { useRouter } from "next/navigation";

import type { ModelInfo } from "@/lib/contracts";
import { useSession } from "@/lib/session";

import { ModelUnavailableNotice } from "./model-status";
import { SessionPanel } from "./session-panel";
import { Uploader } from "./uploader";

export function HomeView({ modelInfo }: { modelInfo: ModelInfo }) {
  const router = useRouter();
  const { stage } = useSession();

  return (
    <div className="stack stack--loose">
      <div className="page-header">
        <h1>Check a photo for the trained subject</h1>
        <p>
          One detector, trained for one person. Choose an image, set the thresholds, and run one
          analysis — nothing happens until you ask for it.
        </p>
      </div>

      <ModelUnavailableNotice info={modelInfo} />

      <div className="split">
        <div className="stack">
          <Uploader
            onSelect={(file) => {
              stage(file);
              router.push("/detect");
            }}
            note="The image is read in this tab and sent once, only when you run an analysis. It is not stored."
          />
          <p className="eyebrow" style={{ letterSpacing: "0.04em", textTransform: "none" }}>
            Choose an image → set the thresholds → analyse
          </p>
        </div>
        <SessionPanel />
      </div>

      {modelInfo.card ? (
        <section className="card" aria-labelledby="model-heading">
          <div className="card__header">
            <h2 className="card__title" id="model-heading">
              The model behind this
            </h2>
            <span className="tag">
              {modelInfo.card.kind === "subject_specific" ? "Subject-specific" : modelInfo.card.kind}
            </span>
          </div>
          <p>{modelInfo.card.limitations}</p>
          <hr className="section-rule" />
          <dl className="definition-list">
            <dt>Name</dt>
            <dd>{modelInfo.card.display_name}</dd>
            <dt>Labels</dt>
            <dd>
              {modelInfo.card.labels.length > 0 ? modelInfo.card.labels.join(", ") : "none declared"}
            </dd>
            <dt>Label source</dt>
            <dd>{modelInfo.card.labels_source}</dd>
          </dl>
        </section>
      ) : null}
    </div>
  );
}
