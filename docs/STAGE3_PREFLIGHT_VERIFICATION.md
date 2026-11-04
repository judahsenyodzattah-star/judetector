# Stage 3 preflight verification

Answers to the six questions asked before any deployment approval. Everything
here was checked against vendor documentation on **2026-11-04**; nothing was
provisioned, no billing was enabled, no account was created.

Sources:

- Vercel deployment protection — `vercel.com/docs/deployment-protection`
- Vercel generated URLs — `vercel.com/docs/deployments/generated-urls`
- Vercel limits and fair use — `vercel.com/docs/limits`, `vercel.com/docs/limits/fair-use-guidelines`
- Vercel pricing — `vercel.com/pricing`
- Cloud Run pricing — `cloud.google.com/run/pricing`
- Cloud Run ingress — `cloud.google.com/run/docs/securing/ingress`
- Cloud Run max instances — `cloud.google.com/run/docs/configuring/max-instances`
- Cloud Billing budgets — `cloud.google.com/billing/docs/how-to/budgets`
- Cloud Billing spend caps — `cloud.google.com/billing/docs/how-to/budgets-spend-caps`
- Cloud Load Balancing pricing — `cloud.google.com/load-balancing/pricing`
- Cloud Armor pricing — `cloud.google.com/armor/pricing`
- Artifact Registry pricing — `cloud.google.com/artifact-registry/pricing`
- Cloudflare rate limiting — `developers.cloudflare.com/waf/rate-limiting-rules`
- Cloudflare transform rules — `developers.cloudflare.com/rules/transform`
- Cloudflare plans — `cloudflare.com/plans`

---

## 1. Verified plans and pricing

### Vercel — Hobby is enough for this project (D2)

| | Hobby | Pro |
|---|---|---|
| Price | **$0** | $20/month per deploying seat, includes $20 usage credit |
| Commercial use | Not allowed — personal, non-commercial only | Allowed |
| Fast data transfer | 100 GB/month included | Flat Rate CDN |
| Function invocations | 1,000,000/month included | Usage-based after credit |
| Active CPU / provisioned memory | 4 CPU-hours, 360 GB-hours | Usage-based |
| Deployments per day / concurrent builds | 100 / 1 | 6,000 / up to 500 |
| Build time per deployment | 45 min | 45 min |
| Runtime logs | 1 hour retention | 1 day |
| **Vercel Authentication (Standard Protection)** | **Available on all plans** | Available |
| Password Protection | **Not available on Hobby** | $20/month per protected project |
| On-demand billing | **None** — monthly allotments only | On-demand after credit |

**Finding:** Vercel's fair-use page defines commercial use as sites that take
payments, advertise a product, are paid to host, run affiliate links as their
purpose, or carry advertising; it states explicitly that *asking for donations
does not count*. An unmonetised educational project with no ads, payments or
sponsorship fits Hobby. **Nothing in this application needs Pro**: the upload
never crosses a Vercel Function, so the 4.5 MB limit and function usage are
irrelevant, and the only server work is small SSR reads.

Hobby caveats to accept: 1-hour runtime log retention (use Cloud Run logs for the
API), a single concurrent build, and no Password Protection — protection is
Vercel Authentication (see §2).

### Cloudflare — Free is enough for rate limiting; origin bypass is the catch (D5)

| | Free | Pro |
|---|---|---|
| Price | **$0** | **$20/month billed annually, $25 billed monthly** |
| Rate limiting rules | 1 rule, counting period 10 s, mitigation 10 s, IP characteristic only | 2 rules, periods up to 1 min, mitigation up to 1 h |
| Transform Rules (request header) | Yes, 10 active rules, **no regex** | 25 rules |
| Unmetered DDoS, WAF, free managed ruleset | Yes | Yes |

**Findings**

1. A single free rule can cap e.g. 5 requests / 10 s per IP — enough to blunt a
   single-source flood, but it is one rule with a fixed 10 s window, and
   Cloudflare documents that counters are per-data-centre with a delay of up to a
   few seconds, so a small number of excess requests can still reach the origin.
2. **Origin bypass is real and cannot be closed for free on this stack.**
   Cloudflare can only front a hostname served by Cloud Run if that hostname is
   mapped to the Cloud Run service (Cloud Run routes by `Host`; a proxied
   `api.<domain>` needs a domain mapping, which is free but needs a domain you
   own). Even then, the service remains reachable by sending `Host: api.<domain>`
   to Google's frontend, and Cloud Run cannot require Cloudflare's mTLS client
   certificate.
3. What actually narrows the bypass, in order of cost:

   | Approach | Closes the bypass? | Cost |
   |---|---|---|
   | **Disable the default `run.app` URL** (Cloud Run ingress setting) after mapping a domain | Removes the easiest path; the mapped hostname remains reachable by `Host` spoofing | $0 |
   | **Shared-secret header** set by a Cloudflare Transform Rule and required by the API | Yes, for anyone who does not know the secret | $0, but **needs a small API change** (opt-in env var) — approval required |
   | Cloud Armor + external Application Load Balancer, Cloudflare removed | Yes, LB-level | ≈$24.25/month before request charges — conflicts with a $5 budget |
   | Cloudflare Authenticated Origin Pulls (mTLS) | Not usable: Cloud Run does not support requiring a client certificate | — |

**Recommendation:** for an educational deployment, take the **free rule + Cloud
Run `max-instances=3` + a Cloud Run spend cap** and accept that a determined
client can bypass the edge and will then hit the service's own per-instance
limiter. Add the shared-secret header only if you judge the bypass material; it is
the only free method that actually closes it.

### Google Cloud — unchanged unit prices, one new finding

| Meter | Price (verified 2026-11-04) |
|---|---|
| Cloud Run CPU, active | $0.000024 / vCPU-second |
| Cloud Run CPU, idle min-instance | $0.0000025 / vCPU-second |
| Cloud Run memory | $0.0000025 / GiB-second |
| Cloud Run requests | $0.40 / million |
| Cloud Run free tier (monthly, request-based) | 180,000 vCPU-s · 360,000 GiB-s · 2M requests |
| Global LB forwarding rule | $0.025 / hour ≈ $18.25 / month |
| Cloud Armor Standard | $0.006849315 / hour per policy ≈ $5.00 · $0.001369863 / hour per rule ≈ $1.00 · $0.75 / M requests |
| Artifact Registry storage | 0.5 GiB free, then ≈ $0.10 / GiB-month |

**New finding:** Google Cloud now offers **spend cap budgets**, which *pause*
service usage when gross estimated costs pass the cap — a real cap, not an
alert. Cloud Run is an explicitly eligible service. See §6.

---

## 2. A protected preview without merging PR #3

Everything below uses features available on **Hobby**. No merge, no production
promotion, no custom domain required.

### What Vercel gives us

- Pushing the branch `arena/72af7497-judetector` creates a **preview deployment**
  with two URLs: a per-commit URL (`<project>-<hash>-<scope>.vercel.app`) and a
  **branch URL** (`<project>-git-<branch-name>-<scope>.vercel.app`). The branch
  URL is stable across pushes and always points at the latest deployment of that
  branch.
- **Standard Protection + Vercel Authentication is available on all plans** and
  protects every deployment except the production domain. Visitors must sign in
  with a Vercel account that has access to the project. Password Protection is
  Pro-only and is not needed.

### The plan

1. Create the Vercel project with Root Directory `web`, production branch `main`,
   and no production deployment yet (the branch is not merged).
2. Enable **Deployment Protection → Standard Protection → Vercel Authentication**.
3. Push to `arena/72af7497-judetector`; note the branch URL:
   `https://<project>-git-arena-72af7497-judetector-<scope>.vercel.app`.
4. Set preview environment variables: `NEXT_PUBLIC_API_BASE_URL` and
   `API_INTERNAL_URL` to the API origin (see step 5).
5. **CORS**: put exactly that branch URL in `JUDETECTOR_CORS_ORIGINS` — one exact
   origin, no wildcard, no per-commit URLs. The per-commit URLs will not work for
   analysis, which is the intended trade-off.

### The API problem, stated plainly

A protected Vercel preview is only a *frontend*. It cannot analyse anything
without a reachable API, and creating that API is Cloud Run provisioning, which
is not authorised. Three options:

| Option | What the reviewer sees | Cost | Needs |
|---|---|---|---|
| **A. Local preview** (current) | Everything, including real analysis if weights are installed locally | $0 | Nothing |
| **B. Vercel preview + locally tunnelled API** | Everything, over a temporary public tunnel to the local machine | $0 | A tunnel tool; the API is publicly reachable while the tunnel is open, so it is a short-lived review, not a deployment |
| **C. Vercel preview + Cloud Run API** | Everything, as production would be | Cloud Run usage (likely $0 in free tier) + Artifact Registry ≈ $0.20 | Explicit deployment approval |

Recommended sequence: **A now** (visual and functional review with no cloud), **B**
only if a shareable link is needed before approval, **C** after approval.

### Caveat about what "protected" covers

Vercel Authentication protects the *pages*. It does not protect the API origin
(Cloud Run is public by design, protected by rate limits and caps), and it does
not stop someone who guesses a per-commit URL from loading the HTML — but the
CORS allowlist means such a page still cannot analyse anything cross-origin.
Neither protection is an access-control system for the model; both are gates on
convenience. Stated so the deployment is not described as "private".

---

## 3. Configuration that creates unavoidable recurring charges

"Unavoidable" here means: recurs every month with no traffic, or exists as soon as
a resource exists. Everything else is usage-based and can be zero.

| Resource | Recurring when idle? | Floor cost | How to avoid or bound it |
|---|---|---|---|
| **Artifact Registry** (container image) | **Yes** — storage bills whether or not the service runs | **≈$0.20/month** (2.5 GiB image, 0.5 GiB free) | Keep at most two image tags, delete old ones; the torch image is the expensive part (~1.5 GiB+) |
| **Cloud Storage** (weights bucket) | **Yes** — storage bills while the object exists | **≈$0.02/month** for <1 GiB | Delete the bucket when finished |
| **Cloud Run compute** | No — request-based billing charges only while an instance is processing or starting | $0 at rest | `min-instances=0`; delete the service to stop it entirely |
| **Cloud Logging** (Cloud Run request logs) | Only if you exceed the free ingest allowance | ≈$0 for this volume | Set log exclusion for `/v1/health`; keep 30-day retention |
| **Load balancer forwarding rule** (Cloud Armor route) | **Yes** — $0.025/hour from creation | **$18.25/month** | Do not create it; use Cloudflare free instead |
| **Cloud Armor Standard policy** | **Yes** — hourly per policy and per rule | **$6.00/month** | Do not create it |
| **Custom domain** | Yes — registrar renewal | ~$10–15/year | Stay on `run.app` and `vercel.app` until there is a reason (note §1: Cloudflare in front of Cloud Run *needs* a mapped domain) |
| **Vercel Pro** | Yes — per seat | $20/month | Stay on Hobby (§1) |
| **Cloudflare Pro** | Yes | $20/month billed annually | Stay on Free |
| **Static IP / Cloud NAT / VPN** | Yes | $0–$30+/month | Not needed; do not create |
| **Cloud Storage egress** (image pulls at cold start) | Small, usage-based | cents | Image locality avoided by keeping the service in one region |

**Total floor for the proposed deployment: ≈$0.22/month** (Artifact Registry +
automatic Cloud Storage), before any request-based Cloud Run usage. Everything
else in the table is optional and costs exactly zero while unused.

The two genuinely unavoidable items are the image in Artifact Registry and the
weights object. Both persist until deleted, and both are cheap; neither can be
hidden by `min-instances=0`.

---

## 4. Obtaining and validating the trained model weights

### Why this blocks everything real

`models/judah-face-v1/best.pt` is absent, `torch`/`ultralytics` are not installed,
`/v1/health` reports `degraded`, `/v1/detect` returns `503`, and every result in
the test suite comes from `FakeModel` or a captured fixture. There is no
inference figure anywhere in this repository because none has ever been measured.

### Where the weights can come from

| Source | Acceptable? |
|---|---|
| The author supplies `best.pt` (transfer, private bucket, or signed link) | **Yes** — the only legitimate source |
| A weights file already inside the repo history | No — none exists |
| Training a new model on new data | Out of scope for this stage; would need a dataset and a fresh evaluation record |
| Downloading a public face model from the internet | **No** — different model, different subject, and the UI would be lying about what it runs |
| Using ONNX export of the same weights | Deferred by decision; must pass parity against the `.pt` path first |

### Chain of custody

1. Receive the file with its **SHA-256, byte size, and the label list** from the author; record all four in `models/judah-face-v1/PROVENANCE.md` (created at that time, committed, containing no weights).
2. Store it in a **versioned, private** Cloud Storage bucket; enable object versioning so a bad replacement can be rolled back to the previous generation.
3. Never commit it. `.gitignore` already blocks `*.pt`; `tests/test_repo_hygiene.py` fails the build if weights appear in the tree.
4. Access to the bucket: one service account, `roles/storage.objectViewer`, scoped to that bucket.

### Validation gates — each must pass before the next

| Gate | Check | Evidence to record |
|---|---|---|
| V1 File integrity | SHA-256 matches the author's value; loads with `torch.load` on CPU | hash, size, load time |
| V2 Registry wiring | `/v1/model` reports `available: true`, `labels_source: model`, labels equal to the author's list | JSON response |
| V3 Sanity inference | Three images: one of the subject (expect detections), one without (expect none), one of a different person (expect none or clearly stated behaviour) | counts, confidences, images |
| V4 Parity | The `slow`-marked test that runs the same image through `analyse_image` and the endpoint and compares boxes/confidences — **this test does not exist yet and must be written** | test output |
| V5 Measured timings | Cold start, model load, RSS, inference p50/p95, annotated PNG size | numbers in `metrics/` and `docs/API.md` |
| V6 Streamlit parity | The prototype, using the same weights, produces the same boxes on the same image | side-by-side record |
| V7 Cloud parity | Same image, same boxes from the deployed service as from local | JSON diff |

Only after V1–V7 may the interface show timings for the model, and only if an
evaluation record exists may `/v1/model` return non-null `metrics`. Until then it
stays `null` and the pages say "not measured".

### If the weights never arrive

The honest outcome is a public demonstration of the **unavailable state**: upload
works, the analyse button explains that no model is loaded, and nothing is
invented. That is a legitimate thing to deploy and to review; it is not a
detection demo, and it must not be described as one.

---

## 5. Browser-based acceptance procedure

Full script: [`ACCEPTANCE_RUNBOOK.md`](ACCEPTANCE_RUNBOOK.md). It covers:

- the environment matrix (Chrome, Edge, Firefox, Safari 18+, iOS Safari, Android Chrome) and the six widths;
- a test-data kit (a subject image, a non-subject image, a corrupt file, a 26 MB file, a GIF renamed `.png`, a 5000×4000 JPEG);
- step-by-step scripts for Home, Detect, Camera and Help with the exact expected result at each step;
- evidence capture (screenshot naming, DevTools network checks, a defect log with severity);
- sign-off criteria and what counts as a blocking defect versus a note.

The runbook is written so a reviewer with no knowledge of the codebase can execute
it and produce a defensible record.

---

## 6. Rollback and cost containment — verified, with one correction

### Correction to the readiness report

The earlier report listed `--max-instances=0` as an emergency stop. **That is
wrong.** Cloud Run accepts a maximum-instance value from **1** upward, so
`--max-instances=0` is not a valid setting. The correct stop switches are:

| Action | Command | Effect |
|---|---|---|
| Block public traffic | `gcloud run services update judetector-api --region us-central1 --ingress internal` | Internet requests can no longer reach the service; it stays deployed and configured |
| Disable the default URL only | Cloud Run ingress setting "disable default URL" | Removes `run.app` reachability while a mapped custom domain keeps working |
| Stop compute entirely | `gcloud run services delete judetector-api --region us-central1` | No instances, no compute billing; the image and its storage remain |
| Pin a previous revision | `gcloud run services update-traffic judetector-api --region us-central1 --to-revisions=<rev>=100` | Instant rollback, no rebuild |
| Redeploy a pinned digest | `gcloud run deploy … --image …@sha256:<digest>` | Restores a known-good image |

The readiness report has been corrected accordingly.

### Verified rollback paths

- **Cloud Run**: revisions are immutable and traffic can be split or pinned to a
  previous revision; images are referenced by digest. Nothing else needs
  reverting, because there is no database and no stored image.
- **Vercel**: deployments are immutable; the previous production deployment can be
  promoted back from the dashboard, or `vercel promote <deployment>` from the CLI.
  `NEXT_PUBLIC_*` changes need a redeploy because they are inlined at build time.
- **Weights**: object versioning on the bucket plus `JUDETECTOR_MODEL_PATH` lets
  you point at a previous generation without touching the image.
- **Edge**: disabling a Cloudflare rule is immediate; so is removing a domain
  mapping.

What cannot be verified from here: all of the above are documented procedures, not
executed steps. The commands cannot be dry-run without an existing service, so the
first execution of each is part of the deployment review, not of this report.

### Cost containment — what is and is not a cap

| Mechanism | Hard cap? | Detail |
|---|---|---|
| **Budget alerts** (the usual "$5 budget") | **No.** Notifications only. | Alerts fire at thresholds you set; spend continues. Never describe this as a cap. |
| **Spend cap budget** (Cloud Billing, eligible services) | **Yes**, with limits | Cloud Run is eligible. When *gross estimated* cost passes 100 % of the cap, new usage of that service in that project is **paused** for the rest of the month and resumes automatically next period. Scoped to one project + one service, monthly period only, uses list prices and ignores credits, in-flight requests finish and bill, and services may take up to an hour to return after lifting. **Persistent resources (storage, registry) keep billing** — spend caps do not pause those. |
| **Cloud Run `max-instances=3`** | Yes, for parallelism | Brief exceedance during traffic spikes is documented as possible. |
| **Cloud Run request timeout / concurrency** | Yes, per request | Bounds the cost of a single stuck request. |
| **Project quota on Cloud Run instances** | Yes | Set below the default; needs a quota adjustment request. |
| **Vercel Hobby** | Effectively, because no on-demand billing exists | Exceeding an allotment stops the feature rather than billing. |
| **Cloudflare Free** | n/a | No usage charges on the free plan. |

**So the containment story is:** a spend cap budget on `run.googleapis.com` is
the one real hard stop for compute, `max-instances=3` bounds a burst, and the
$5/$20 budget alerts are an early-warning system — not a cap. The floor costs in
§3 (Artifact Registry + Cloud Storage, ≈$0.22/month) sit outside any cap and
continue until the resources are deleted.

A spend cap can only exist **after** a billing account exists, which is exactly
the step awaiting approval. It must be configured in the same change as the first
deployment, not afterwards.

---

## 7. Decisions still required

| # | Decision | Recommended answer |
|---|---|---|
| **A1** | Enable Google Cloud billing and create the project? | Yes, with a spend cap budget on Cloud Run at $5 configured in the same change |
| **A2** | Deploy the API to Cloud Run at all in Stage 3, or stop at a local/tunnelled preview? | Deploy, since acceptance cannot be completed without it — but only after weights exist, otherwise the deployment demonstrates the unavailable state |
| **A3** | Buy a domain (~$10–15/year) so Cloudflare can front Cloud Run? | Not yet; stay on `run.app` and rely on the app limiter plus caps. Without a domain, Cloudflare cannot protect the API at all |
| **A4** | Add the **shared-secret header** to the API (opt-in env var) to close origin bypass? | Only if you consider bypass material; it is the only free closure and it is a code change |
| **A5** | Vercel Hobby confirmed, or Pro? | **Hobby** — the project is non-commercial, needs no password protection, and carries no uploads |
| **A6** | Accept the $0.22/month floor (image + weights storage) as the minimum recurring cost? | Yes, it is the floor for any container deployment |
| **A7** | Who provides `best.pt`, and is it available now? | Required before any real-inference acceptance; if unavailable, the deployment is an honest unavailable-state demo |
| **A8** | Approve Vercel **preview-only** deployment (protected, unmerged) before full deployment? | Yes — it is free, reversible and exercises the real build pipeline |
