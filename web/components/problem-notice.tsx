import type { Problem } from "@/lib/contracts";
import { describeProblem } from "@/lib/problems";

import { AlertIcon } from "./icons";

export function ProblemNotice({
  problem,
  retryAfterSeconds,
  requestId,
}: {
  problem: Problem;
  retryAfterSeconds?: number | null;
  requestId?: string | null;
}) {
  const copy = describeProblem(problem, retryAfterSeconds);
  const reference = requestId || problem.request_id;

  return (
    <div className="notice notice--error" role="alert">
      <p className="notice__title">
        <AlertIcon style={{ verticalAlign: "-3px", marginRight: 8 }} />
        {copy.title}
      </p>
      <p className="notice__detail">{copy.detail}</p>
      {copy.hint ? <p className="notice__detail">{copy.hint}</p> : null}
      {reference ? <p className="notice__meta">Reference {reference}</p> : null}
    </div>
  );
}
