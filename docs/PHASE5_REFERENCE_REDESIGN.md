# Phase 5 — Ultralytics-referenced product redesign

**Proposal for approval. No application code has been changed.**

Branch `arena/72af7497-judetector` · PR #3 stays open · nothing merged or deployed.

---

## 0. Method, and what I could actually see

Honesty about sources matters more here than anywhere else in this project, because the
request is to learn from a live commercial product.

| Source | Access | What it gave |
|---|---|---|
| `platform.ultralytics.com` (marketing page) | **Reached** via the proxied fetch tool | Product scope, workflow vocabulary (upload → annotate → train → export/deploy), the "Try YOLO26 inference" pitch |
| `docs.ultralytics.com/platform` + `/quickstart` + `/deploy/inference` | **Reached** | Sidebar sections, Home dashboard regions, Predict tab behaviour, parameter ranges and defaults, empty states, overlays, download behaviour |
| Six platform screenshots (via image search, sourced from Ultralytics' own docs CDN) | **Reached, and viewed** | The authenticated app: Predict tab empty and with results, Home dashboard, parameter sliders |
| The authenticated app itself | **Not reachable** | No account, no login, and no ability to inspect DOM/CSS, hover states, focus rings, disabled styling, or resize behaviour |
| `platform.ultralytics.com` from the sandbox shell | **Blocked** (`curl` → 000) | Confirms direct network access is restricted; only proxied tooling works |

Labelling used below: **[OBS]** directly observed in a screenshot, **[DOC]** stated in
Ultralytics documentation, **[INF]** inferred or estimated by me, **[OURS]** a decision for
JUDEtector rather than a claim about Ultralytics.

Screenshot dimensions limit precision: the images are ~500 px wide, so measurements
(spacing, type sizes, radii) are **estimates**, not CSS values. I have not reproduced any
Ultralytics branding, wordmark, artwork or screen layout.

---

## 1. Ultralytics reference study

### 1.1 Application frame

**[OBS]** A persistent dark left rail (~190 px at a 1600 px viewport) against a light warm
canvas, with content in a max-width band and a slim top bar above it. The frame is the same
on every page; only the content region changes. This is the single biggest structural
difference from JUDEtector, where each page renders as a loose document on the canvas.

**[OBS]** The content region is composed of **bordered white cards** with a card header
(small title, optional inline tab strip, right-aligned actions) and a card body. Cards are
used to group one job — "Input image", "Results", "Datasets", "Projects", "Storage" — never
to decorate a paragraph.

### 1.2 Navigation

**[OBS]** The rail carries: wordmark, a search field with a `⌘K` hint, then grouped
sections — *Home / Explore / Agents*, **Annotate** (with an inline `+`), **Train**,
**Deployments**, **Help / Settings** — with "25 More" disclosure when a group is long, and a
user block (avatar, name, plan) pinned to the bottom. **[OBS]** A floating "Ask AI" pill sits
bottom-right, above everything.

**[OBS]** The top bar carries a breadcrumb/location, a visibility state ("Public"), object
actions (star, kebab), and utility icons on the right (usage, apps, help, avatar).

**[DOC]** Onboarding tours highlight exactly this structure: Home, Explore, Annotate, Train,
Deploy, Settings, Account — evidence that the information architecture is deliberate and
stable, not incidental.

**[OURS]** The transferable principle: *one persistent frame, grouped destinations, object
actions in the header, utilities on the right*. The principle not to transfer: density of
destinations. JUDEtector has five, and adding more would be costume.

### 1.3 Page header and metric strip

**[OBS]** The model page opens with a compact header (icon, name, state pill, actions) and
then a **strip of four metric cards** — mAP50 61.9%, mAP50-95 28.8%, Precision 63.8%,
Recall 61.7% — each with a small sparkline filling the right half of its card. Metric labels
are small and muted; values are large and dark; the sparkline is a pale tint, not a chart
with axes.

**[INF]** Metric values ≈ 20–22 px, labels ≈ 11–12 px, card radius ≈ 8 px, border ≈ 1 px
light grey, no visible shadow at rest.

**[OURS]** JUDEtector has almost no real metrics to show on a consumer page (one model, one
class), so copying a four-card metric strip would mean inventing numbers. The principle to
take is the *strip*: a single row of compact, equal-height facts — detection count, mean
confidence, inference time, applied threshold — all genuinely measured.

### 1.4 Tabs, segmented controls, progressive disclosure

**[OBS]** Underline-style tabs (`Overview | Train | Predict | Export | Deploy`) separate
jobs within one object. Inside the Results card, a second, smaller tab set
(`Response | JSON | Docs`) separates reading levels. A segmented control (`Image | Webcam`)
switches input method inside the Input card.

**[DOC]** Training dialogs hide anything advanced behind **Advanced Settings**; the Predict
tab keeps sliders visible but secondary; API examples live in their own tab.

**[OURS]** Three levels of disclosure are visible at once and none of them competes: page
tabs (job), card tabs (output format), advanced panel (expert settings). JUDEtector currently
has *zero* of these and puts per-box coordinates in a collapsed expander at the very bottom —
which is disclosure in the wrong direction.

### 1.5 Upload and input

**[OBS]** The dropzone is a dashed rectangle containing a circular icon button (upload
glyph), a bold one-line prompt ("Drop an image here"), a secondary line ("or click to
browse"), and a muted capability line listing formats and the size limit. Below the
dropzone, **example images** are offered as thumbnails next to a **Webcam** tile, so a
first-time user never faces an empty file dialog.

**[DOC]** Predict tab accepts JPEG, PNG, WebP, AVIF, HEIC, JP2, TIFF, BMP; 10 MB limit;
**inference runs automatically** on upload, on example click, and on webcam capture; it
re-runs when confidence, IoU or image size change.

**[OURS]** JUDEtector must keep an explicit *Analyse image* action (see §9, decisions) — but
the dropzone's internal structure (icon, prompt, "or click to browse", capability line) and
the "secondary ways in" row are directly transferable, and we already have a Camera page to
point at instead of a webcam tile.

### 1.6 Results presentation

**[OBS]** The results card header reads `8 detections found` on the left and `357 ms` on the
right. Below it, three small timing tiles — `25 ms Preprocess`, `303.3 ms Inference`,
`2.9 ms Postprocess`. Then a **detection list**: one row per detection, a colour dot keyed to
the class, the class name, and a right-aligned confidence percentage, separated by hairlines.
A footer line carries versions (`Ultralytics 8.4.0 · PyTorch 2.9.0`).

**[OBS]** Overlays on the image are coloured boxes with filled label chips at the corner; the
class colour in the list matches the box colour on the image.

**[OBS]** Two controls sit over the preview once results exist: click to enlarge (overlays
preserved) and download the annotated image.

**[OURS]** The list-plus-overlay pairing is the reference's strongest single idea for a
detection product: the same detection is legible as a *shape on the image* and as a *row in a
list*, tied by colour. JUDEtector currently offers neither (a dataframe of coordinates inside
an expander, and a flattened PNG).

### 1.7 States

**[DOC]** Empty Results: "Prediction results will appear here." **[DOC]** Monitoring tab with
no data: "No images processed". **[DOC]** A model without weights shows an empty state
instead of a broken Predict tab. **[DOC]** Dataset headers carry **Ready / Not Ready** badges
that are clickable to reveal the missing condition.

**[OURS]** Two patterns worth adopting wholesale: (a) an empty state that names the *next
action* rather than apologising, and (b) a status badge that explains itself when clicked
instead of silently changing colour.

### 1.8 User versus technical separation

**[DOC]** The Predict tab is the human-facing surface (drop, look, download). The technical
surface is separated: an **API Docs** card with Python/JS/cURL prefilled with the current
sliders, a **JSON** tab, deployment endpoints and monitoring, and account/billing behind
Settings. Inference parameters are exposed as three sliders, not as configuration files.

**[OURS]** This validates JUDEtector's existing audience split (consumer pages versus hidden
`/developer`) and suggests one improvement: technical *output* (raw records) should be a tab
next to the human summary, not a mystery expander.

### 1.9 What must not be copied

Ultralytics' lime accent, wordmark, card-for-card layout, icon choices, "Ask AI" affordance,
marketing copy, and screenshots. JUDEtector keeps its own mark, its ochre-and-paper identity,
and its much smaller surface area.

---

## 2. Principles extracted, and what each one forces here

| # | Principle (reference) | JUDEtector consequence |
|---|---|---|
| 1 | A persistent frame: rail + top bar + content band | Build a real `AppShell`; stop rendering loose documents per page |
| 2 | Cards group one job, never decorate | Introduce `Card` with header/tabs/body/actions; delete free-floating sections |
| 3 | Job tabs, output tabs, advanced panel — three disclosure levels | Detect gets `Results / Details` tabs; params stay in a collapsed panel; coordinates become a Details tab |
| 4 | Input left, results right, both always present | Stable two-panel workspace; results never push the input away |
| 5 | Every detection exists twice: on the image and in the list, tied by colour | Detection list with class colour dots + confidence bars; overlay toggles on the viewer |
| 6 | Compact fact strip instead of hero numbers | Real metrics only: detections, mean confidence, inference ms, threshold |
| 7 | Empty states name the next action; badges explain themselves | Rewrite every empty state; model status badge explains state on click |
| 8 | Human surface first, technical output one level down | Raw records move from a hidden expander to a `Details` tab |
| 9 | Dense typography, small radii, hairline borders, restrained elevation | Move from 2 px "print" corners to 8 px cards/6 px controls; keep hairlines; shadows only for overlays |

---

## 3. JUDEtector audit — why it currently reads as unfinished

Measured in the working tree, not estimated:

```
pages                 5 (Home, Detect, Camera, Help, hidden Developer)
custom CSS            16.6 KB — 114 rule blocks, 34 custom classes,
                      33 Streamlit-internal data-testid selectors
icons in content      0
uses of st.tabs       0    st.segmented_control 0    st.popover 0
                      0    st.toast 0    st.status 0    st.skeleton 0    st.badge 0
image interaction     none (st.image only: no zoom, pan, overlay toggle, hover)
detections UI         one dataframe of coordinates, inside a collapsed expander
tests                 202 (AppTest + CSS/contrast guards)
```

### Findings

1. **There is no application frame.** Each page starts with a text heading on the canvas.
   Streamlit's default sidebar lists five words with no grouping, no context, no user block.
   Consequence: every screen looks like a page someone wrote, not a product someone built.
   *(Reference: persistent rail + top bar.)*

2. **The workspace is a document, not a tool.** Detect is: uploader → print → caption →
   controls → button → results, stacked vertically. Results appear *below the fold* and push
   the input controls out of view. Consequence: after analysing you cannot see the controls
   and the outcome at the same time. *(Reference: fixed two-panel.)*

3. **The image cannot be inspected.** `st.image` renders a static picture. No zoom, no pan,
   no overlay toggle, no per-detection highlight, no coordinate readout. Consequence: the
   central object of a computer-vision product is the least capable element on screen.

4. **Detections are unreadable as a list.** Coordinates live in a dataframe inside an
   expander; confidence appears only as an aggregate. Consequence: a user cannot answer
   "which box is that?" — the reference answers it by colour-linking list rows to boxes.

5. **Over-styled internals, under-built components.** 33 `data-testid` selectors style
   Streamlit's private markup, while the app itself has no Card, Toolbar, Badge, EmptyState
   or Menu abstraction. Consequence: high maintenance risk *and* a visually thin product.

6. **No iconography at all.** After the last phase removed every glyph, controls read as
   plain text: nothing signals upload, camera, download, parameters, or status. Recognisable
   controls need recognisable marks.

7. **States are sentences.** Errors are a bordered line; loading is Streamlit's spinner;
   there is no skeleton, no disabled reasoning, no success confirmation, no drag-over state
   in the dropzone beyond a border colour.

8. **Typography has no component roles.** Nine sizes exist, but Page title / Card title /
   Body / Label / Data have no fixed mapping, and mono is used for captions *and* for prose
   in places. Consequence: hierarchy is inconsistent between pages.

9. **Mobile is an automatic stack.** Breakpoints exist (900/860/760) but there is no mobile
   navigation, no sticky primary action, no thumb-reachable controls, and the two-panel
   workspace collapses into a very long scroll.

10. **Brand is a single drawing.** The wordmark, the ochre mark and the mounted print are the
    whole identity; nothing else would be recognisable on a second visit.

**What already works and must be kept:** the honest failure state, the subject-specific
model language, the audience split, the token-based colour system, the contrast/test
discipline (202 tests), and the framework-agnostic detection core. The redesign builds on
these rather than replacing them.

---

## 4. Component and icon library evaluation

Registry facts checked directly (`registry.npmjs.org`, `pypi.org`) on 2026-11-04:

| Library | Version | Licence | Last publish | Verdict |
|---|---|---|---|---|
| `lucide-react` | 1.67.0 | ISC | 2026-11-03 | Excellent, actively maintained. **Only if we adopt React (B).** |
| `@phosphor-icons/react` | 2.1.10 | MIT | 2025-05-22 | Viable, but 18 months stale and a heavier aesthetic. **Rejected.** |
| `radix-ui` (unified) | 1.8.1 | MIT | 2026-10-14 | Best-in-class primitives. **Only in B.** |
| `@radix-ui/react-tabs` | 1.2.1 | MIT | 2026-10-14 | As above. |
| `shadcn` (CLI/copy-in) | 4.23.0 | MIT | 2026-10-27 | Good *if* B: copied-in components, customisable, no runtime lock-in. Not a drop-in for Streamlit. |
| `tailwindcss` | 4.3.4 | MIT | 2026-11-02 | Pairs with shadcn in B; irrelevant to A. |
| `konva` / `react-konva` | 10.9.1 / 19.3.2 | MIT | 2026-10-31 / 15 | Correct tool for interactive overlays (zoom/pan/hit-testing). Usable **inside a Streamlit custom component**. |
| `streamlit` (installed) | 1.66.1 | Apache-2.0 | 2026-10-21 | Already here. Has `tabs`, `segmented_control`, `popover`, `toast`, `status`, `skeleton`, `badge`, `pills`, `container(border=)`, `columns(border=)`, `dialog`, `fragment`. |
| `streamlit-image-coordinates` | 0.4.1 | MIT | 2026-08-14 | Maintained. Gives click coordinates only — no zoom/pan/overlays. Optional spike, not a foundation. |
| `streamlit-drawable-canvas` | 0.13.0 | (fabric.js wrapper) | 2026-09-04 | Designed for *drawing* annotations, not viewing. Wrong tool. |
| `streamlit-extras` | 1.6.0 | — | 2026-05-15 | Grab-bag; one or two helpers at most. Not a design foundation. |
| `streamlit-elements` | 0.1.0 | MIT | **2022-04-25** | **Dead. Rejected.** |
| `streamlit-image-annotation` | 0.8.0 | — | 2026-02-24 | Annotation-focused, opinionated styling. Rejected. |

### Recommendation — icons: one family, chosen by architecture

- **If A (Streamlit): use Material Symbols Rounded, which Streamlit already loads.** No new
  dependency, one family, themeable through the font's variable axes (weight, fill, size),
  and consistent with the nav icons already in `st.Page`. Sizes 16 / 20 / 24 only; `fill=1`
  reserved for selected states.
- **If B (React): use Lucide**, one family, 1.5–2 px stroke at 16/20/24.
- **Never both.** Mixing Lucide into a Streamlit app whose chrome is Material Symbols would be
  exactly the inconsistency this phase is meant to fix. The only non-icon mark is
  JUDEtector's own logo.
- Hand-drawing UI glyphs is banned except the brand mark; the current specimen illustration
  stays as an illustration, not as iconography.

### Recommendation — image interaction

Konva is the right engine for zoom/pan/hit-testing, and it can live inside Streamlit as a
**packaged custom component (CCv2)**. Streamlit 1.66 ships `st.components.v2` with
`component(name, html=, css=, js=, isolate_styles=)` for inline components and asset-dir
packaging for bundled React/TS — verified in the installed package, including bidirectional
state (`setStateValue` / `setTriggerValue`). Inline means "one JS string, no bundler"; a
bundled React + Konva viewer is a *packaged* component and must be generated from Streamlit's
official `component-template` (a hard rule in the installed Streamlit skill, and the reason a
Node toolchain is a genuine cost, not a footnote).

---

## 5. Architecture comparison

Scored 1–5 (5 best) against the criteria the brief names. "A1" = Streamlit with native
components only. "A2" = A1 + one packaged CCv2 image viewer. "B" = React/TS SPA + FastAPI
backend around the existing `app/core`.

| Criterion | A1 native | A2 Streamlit + CCv2 viewer | B React + API |
|---|---|---|---|
| Visual control | 3 — native widgets + theme tokens, but internals still need CSS | 4 — everything except the viewer is native; the viewer is fully ours | 5 — total |
| User experience | 3 — good structure, no image interaction | 4 — real viewer, list↔overlay linking | 5 |
| Accessibility | 4 — Streamlit ships focus/labels/aria for free | 4 — viewer must earn its own (keyboard, list alternative) | 3 — must be rebuilt and re-verified |
| Responsive design | 3 — breakpoints, no mobile nav pattern | 3 — same, plus a viewer that must handle touch | 5 |
| Development complexity | **5** — no new toolchain | 3 — Node + component template + build artefacts | 1 — new app, new CI, new hosting, duplicated tests |
| Hosting | 5 — one process, as today | 4 — one process, bundled JS assets committed | 2 — two services (static + API), CORS, sessions |
| Maintenance | 4 — CSS against internals is brittle; tests pin it | 3 — adds a JS surface with its own deps | 2 — two stacks, two dependency trees, two test suites |
| Integration with inference | 5 — direct calls | 5 — direct calls; viewer consumes `records()` | 4 — API layer required, must preserve exact semantics |
| Risk to current functionality | **1** (lowest) — no behavioural change | 2 — viewer is additive and can degrade to `st.image` | 5 (highest) — rewrite of routing, state, upload, download, tests |
| **Total /45** | **33** | **31** | **28** |

### Recommendation: **A2, delivered in two stages**

**Stage A1 first** (native components + design system + frame + two-panel workspace + list),
**then A2** (the viewer). Both stages keep the Python app, its routing, its tests and its
detection semantics.

Why not B now:

- The detection core is already framework-agnostic (`app/core` is Streamlit-free except one
  `import streamlit` in `runtime.py` for caching), so **B remains available later** by adding
  a thin FastAPI wrapper — roughly 150 lines — without touching inference code. Choosing A2
  does not close the door; it defers the cost until there is evidence it is needed.
- The 202-test suite is an asset. B would discard most of it (AppTest-based) and re-earn the
  honesty guarantees from scratch — the riskiest possible move for an app whose entire value
  proposition is "it does not lie about what it detected".
- The concrete gaps are narrow: image interaction, result density, navigation frame. A2
  addresses all three with one component and a component library, not a rewrite.
- B's advantage is real but mostly in *breadth* (many screens, complex state). JUDEtector has
  five pages and one workflow.

**Exit ramp (documented, not built):** if the app grows multi-image/batch, video, or
multi-model comparison, B becomes correct; the seam is `app/core` plus a small API module.

---

## 6. Proposed interface

Identity is unchanged: **paper and ink, mounted prints, one ochre marking colour**. What
changes is that the identity gets an application structure around it. Structure is borrowed
as *principles* (frame, cards, panels, tabs, lists, states) — not as Ultralytics' colours,
layouts or assets.

### 6.1 Navigation specification

**Left rail, 232 px, graphite `#1E2122`**, pinned full height, present on every page.

```
┌──────────────────────┐
│  ◤ JUDEtector        │   brand mark + wordmark (ochre rule inside the mark)
│                      │
│  Workspace           │   group label, 11 px, muted, uppercase-lite tracking
│  ▸ Home              │   active: ochre left rule 2px + white text + weight 600
│  ▸ Detect            │   icon 20px, label 14px, row height 40px, radius 6px
│  ▸ Camera            │   hover: rgba(255,255,255,.06)
│  ▸ Help              │
│                      │
│                      │
│                      │   flexible spacer
│  Model               │
│  ● Ready             │   status row: dot + label, clickable → explains state
│  judah · 1 class     │   11 px muted, real registry values only
│                      │
│  ◔ jane@…  ⚙  ?      │   user block: avatar, name, settings, help
└──────────────────────┘
```

Rules: destinations are five and stay five; the Developer page is **not** in the rail (hidden
route, as today). The rail carries no search field — there is nothing to search. No "Ask AI"
equivalent. On `<900 px` the rail becomes a 56 px top bar with a menu button opening a
dialog; the primary action also repeats in a sticky bottom bar.

**Top bar (56 px, on the canvas):** left = page title only on mobile; on desktop the page
title lives in the content band (see 6.2). Right = `Help` icon-link, model status chip,
nothing else. No breadcrumb until there is a second level of hierarchy (there isn't).

### 6.2 Desktop structures

**Home — an application entry point, not a hero**

```
┌ App rail ┬──────────────────────────────────────────────────────────────────────┐
│          │  Home                                            [Analyse an image]  │
│          │  Upload a photo, or take one with your camera.      [Use the camera]  │
│          │                                                                       │
│          │  ┌ Image ────────────────────────────────────┐  ┌ Session ─────────┐ │
│          │  │ ╭ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ╮ │  │ 12 analyses      │ │
│          │  │ ┆        ⬆  Drop an image here           ┆ │  │ 14 images        │ │
│          │  │ ┆        or click to browse              ┆ │  │ 82.4% mean conf. │ │
│          │  │ ┆  JPG · PNG · WEBP · BMP · up to 25 MB  ┆ │  │ ──────────────── │ │
│          │  │ ╰ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ╯ │  │ Recent           │ │
│          │  │  Prefer your camera? Open Camera →        │  │ sample.png ②     │ │
│          │  └───────────────────────────────────────────┘  │ 0.5s ago         │ │
│          │  ┌ How it works ─────────────────────────────┐  └──────────────────┘ │
│          │  │ ① Upload or capture  ② Analyse  ③ Download │                       │
│          │  └───────────────────────────────────────────┘                        │
└──────────┴──────────────────────────────────────────────────────────────────────┘
```

Notes: the dropzone works here and routes to Detect with the file — Home is a *starting
surface*, not a poster. Session facts are real (`app/core/stats.py`); when empty, the Session
card shows an empty state that names the next action. No oversized headline, no drawn
specimen on Home (the specimen moves to Help, where explaining the product belongs).

**Detect — the workspace**

```
┌ App rail ┬──────────────────────────────────────────────────────────────────────┐
│          │  Detect                                    Model ● Ready   [ ⚙ Params ]│
│          │  ┌ Image ────────────────────────────┐  ┌ Results ──────────────────┐│
│          │  │ [ Image ] (segmented: Image|Cam)  │  │ Results │ Details │ JSON   ││
│          │  │                                   │  │ 2 detections found   41 ms││
│          │  │  ╭─────────────────────────────╮  │  │ ┌────────┬────────┬─────┐ ││
│          │  │  │                             │  │  │ │⏱ 4 ms  │⚡ 34 ms │ 3 ms│ ││
│          │  │  │   preview / viewer +        │  │  │ │Prepro. │Infer.  │Post │ ││
│          │  │  │   overlays, zoom, pan       │  │  │ └────────┴────────┴─────┘ ││
│          │  │  │                             │  │  │ ● judah        91.0% ▓▓▓ ││
│          │  │  ╰─────────────────────────────╯  │  │ ● judah        62.0% ▓▓   ││
│          │  │  [−] [100%] [+]  [Fit]  [Overlay] │  │ ────────────────────────  ││
│          │  │  sample.png · 1024×768 · 214 KB   │  │ Threshold 0.25 · IoU 0.45 ││
│          │  │                                   │  │ [ Download annotated ]    ││
│          │  │  [ Analyse image ]  (primary)     │  └───────────────────────────┘│
│          │  └───────────────────────────────────┘                               │
└──────────┴──────────────────────────────────────────────────────────────────────┘
```

Rules: the two panels are always present; results never displace the input. Only *measured*
timings appear — JUDEtector records inference time, so the tile row shows **Inference** and
**Total** unless pre/post are instrumented (they are not; see decisions §9.4). The results
list row is the unit of meaning: colour dot ↔ overlay colour, class, confidence bar, value.
`Details` holds per-box coordinates; `JSON` holds the raw records (technical, one level
down). Parameters open in a popover from the header, so the workspace stays calm.

**Camera** — identical workspace, `Image | Camera` segmented control defaults to Camera; the
capture card replaces the dropzone; the last snapshot is retained with a `Retake` action.

**Help** — a two-column article layout (topic index left, content right), max 68 ch measure,
with the specimen illustration used once, labelled. Topics: Getting started · Reading a
result · Your images · Limits.

**Developer** — same frame, distinct skin: monospace tables, model resolution, weights path,
runtime availability, recorded metrics, session runs, last error. Header carries a permanent
`Hidden, not access-controlled` badge with explanatory popover.

### 6.3 Mobile structures (<900 px)

```
┌────────────────────────────────────┐        ┌────────────────────────────────────┐
│ ☰  Detect              ● Ready     │        │ ☰  Home                            │
├────────────────────────────────────┤        ├────────────────────────────────────┤
│ ┌ Image ─────────────────────────┐ │        │  Upload a photo, or take one with  │
│ │  ╭ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ╮ │ │        │  your camera.                      │
│ │  ┆   Drop an image here        ┆ │ │        │  ┌──────────────────────────────┐  │
│ │  ┆   or click to browse        ┆ │ │        │  │ ⬆  Drop an image here        │  │
│ │  ╰ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ╯ │ │        │  │ JPG · PNG · WEBP · 25 MB     │  │
│ └────────────────────────────────┘ │        │  └──────────────────────────────┘  │
│ ┌ Results ───────────────────────┐ │        │  ┌ Session ─────────────────────┐  │
│ │ Results │ Details              │ │        │  │ 12 analyses · 82.4% mean     │  │
│ │ 2 detections · 41 ms           │ │        │  └──────────────────────────────┘  │
│ │ ● judah 91.0% ▓▓▓▓▓▓▓          │ │        │                                    │
│ └────────────────────────────────┘ │        ├────────────────────────────────────┤
├────────────────────────────────────┤        │ [   Analyse an image   ]           │
│ [    Analyse image    ]  [⬇]       │        └────────────────────────────────────┘
└────────────────────────────────────┘
```

Mobile rules: single column, panels in job order (image → results → parameters); sticky
bottom bar carries the primary action plus download; drawer navigation with the same five
destinations; touch targets ≥44 px; the viewer supports pinch-zoom and one-finger pan;
`Details`/`JSON` remain reachable but never dominate.

### 6.4 Component inventory

| Component | Variants | States |
|---|---|---|
| `AppShell` (rail + top bar + band) | desktop / collapsed rail / mobile drawer | default |
| `NavItem` | destination, group label | default, hover, active, focus-visible |
| `PageHeader` | title + subtitle + actions slot | default |
| `Card` | with header / header+tabs / body only | default, busy |
| `CardTabs` | underline | default, active, focus, disabled |
| `SegmentedControl` | 2–3 options | default, active, focus, disabled |
| `Dropzone` | with format caption | idle, drag-over, uploading, error, filled |
| `ImageViewer` | fit / zoom / pan / overlay on-off | loading, ready, error, empty |
| `ToolBar` (viewer controls) | icon buttons + zoom label | default, hover, active, disabled |
| `DetectionList` | row: dot, class, bar, % | default, hover, selected, empty |
| `FactStrip` | 3–4 tiles | default, empty |
| `ParamPanel` | confidence + IoU sliders | default, changed, disabled |
| `StatusBadge` | ready / unavailable / hidden | default, popover-open |
| `EmptyState` | icon, title, next-action link | default |
| `InlineAlert` | info / warning / error | default |
| `Toast` | success / failure | auto-dismiss |
| `Button` | primary / secondary / quiet / danger-free | default, hover, active, focus, disabled, loading |
| `IconButton` | 32 px / 40 px | as Button |

### 6.5 Icon specification

Material Symbols Rounded (A) or Lucide (B) — one family, three sizes (16 inline, 20 UI, 24
feature), 2 px optical weight, `fill=1` only for selected states. Allowed glyphs are limited
to those that carry meaning: `upload`, `photo_camera`, `download`, `tune` (parameters),
`info`, `check_circle`, `error`, `search` (only if a search field exists), `arrow_back`,
`help`. No icon on every card heading; no decorative icons; icon-only buttons require
`aria-label` and a tooltip.

### 6.6 Colour and typography tokens

Colour (extends the current palette; nothing removed):

| Token | Value | Use |
|---|---|---|
| `sheet` | `#F4F2ED` | app canvas |
| `mount` | `#FFFFFF` | cards, viewer surface, inputs |
| `rail` | `#1E2122` | navigation rail only |
| `rail-muted` | `#A9ADA9` | rail labels |
| `ink` | `#16181A` | primary text |
| `ink-2` | `#52585C` | secondary text, labels |
| `rule` | `#D0CBC1` | hairlines, dividers |
| `border-strong` | `#BCB6AA` | card borders on canvas |
| `mark` | `#8A5A00` | primary action, active nav rule, focus ring, detection outline |
| `mark-quiet` | `#F0E4CE` | selection tint inside lists only (not a card surface) |
| `ok` | `#1F6F4A` | ready status text |
| `warn` | `#8A4B0B` | warnings |
| `danger` | `#A03024` | failures (text and 1 px borders only) |

Typography — system sans for language, system mono for data. Roles, not just sizes:

| Role | Size / weight | Notes |
|---|---|---|
| Page title | 20 px / 600 | one per page |
| Card title | 14 px / 600 | with 12 px muted subtitle when needed |
| Body | 14 px / 400, 1.55 | max 72 ch |
| Label | 12 px / 500, `ink-2` | field and tab labels |
| Data label | 11 px mono / 500, tracking .04em | caption strips, fact tiles |
| Data value | 14 px mono / 500 tabular | counts, ms, coordinates |
| Metric value | 22 px mono / 600 tabular | only in the fact strip |

Spacing 4/8/12/16/24/32/48; card padding 20 px; grid gutter 16 px; content band 1180 px with
32 px side padding (desktop), 16 px (mobile). Radii: 8 px cards, 6 px controls, 999 px only
for status dots. Borders: 1 px `border-strong` on cards, 1 px `rule` for internal dividers.
Elevation: none at rest; `0 1px 2px rgba(22,24,26,.06)` for popovers/dialogs only. Focus:
2 px `mark` outline with 2 px offset on every interactive element.

### 6.7 Image-viewer specification

- **Purpose:** inspect a detection result as an image, not as a table row.
- **Source:** the uploaded image (as data URL) plus `DetectionResult.records()` as JSON. Overlays
  are drawn client-side; **the downloadable annotated PNG remains the server-rendered image**
  (`app/core/rendering.py`, unchanged), so exports never disagree with what's on screen.
- **Controls:** zoom out / zoom in / fit / 1:1 / overlay toggle / label toggle; zoom 50–400 %,
  wheel + pinch, drag to pan, double-click to fit.
- **Keyboard:** `+`/`-` zoom, `0` reset, `F` fit, `O` toggle overlay, `L` toggle labels, arrows pan;
  the viewer is focusable and announces zoom changes via `aria-live`.
- **Linking:** hovering a detection row outlines that box and dims the rest; clicking a box
  scrolls the row into view and selects it. Selection is one state shared by list and canvas.
- **Empty/loading/error:** skeleton rectangle while decoding; explicit message for an
  unreadable image; no overlay when there are zero detections.
- **Degradation:** if the component fails to load, the app falls back to `st.image` and the
  list stays fully usable — the feature is additive, never load-bearing.
- **Honesty:** the viewer never invents detections; it renders exactly the records it is given,
  and shows "Illustration" labelling nowhere (it only ever shows a user's real image).

### 6.8 Interaction-state specification

| Element | Hover | Active/pressed | Focus-visible | Disabled | Loading |
|---|---|---|---|---|---|
| Primary button | `mark-hover` | 1 px inset shadow, no size change | 2 px `mark` ring, 2 px offset | `sheet` fill, `ink-2` text, cursor not-allowed, `aria-disabled` | label swaps to "Analysing…" + 16 px spinner, width preserved |
| Secondary button | `sheet` fill, border `ink-2` | as hover + inset | as primary | as primary | inline spinner |
| Icon button | `sheet` fill | as hover | ring | 40 % opacity + `aria-disabled` | — |
| Nav item | `rgba(255,255,255,.06)` | — | ring inset | — | — |
| Card | no hover (not clickable) | — | — | busy: 60 % content + skeleton | skeleton rows |
| Detection row | `mark-quiet` tint + box emphasised | selected: tint + left 2 px `mark` | ring | — | — |
| Dropzone | border `ink`, background stays white | — | ring on focus-within | — | progress bar + "Uploading…" |
| Slider | track `mark` | thumb scale 1.0 (no growth) | ring | 40 % opacity | — |

Rules: no colour fade on text, no layout shift on state change, transitions ≤120 ms and
colour/border only, `prefers-reduced-motion` respected.

### 6.9 Loading, empty, success, failure

| Situation | Treatment |
|---|---|
| App boot | rail + shell render immediately; content skeleton per card |
| No image yet | Dropzone prompt + capability line; results card shows "Prediction results will appear here." |
| Uploading | Dropzone progress + filename row; cancel available |
| Invalid file | Inline alert above the results card: "That file could not be read as an image." + formats |
| Analysing | Primary button loading; results skeleton with the fixed layout so nothing jumps |
| Zero detections | Results header "No detections found"; explicit hint to lower the threshold; viewer shows the image unmarked |
| Success | Result count + fact strip + list; toast "Analysed in 341 ms" (measured) |
| Model unavailable | Single sentence in the results card, *no metrics, no list, no download*; cause retained for `/developer` |
| Developer route | Permanent badge "Hidden, not access-controlled" with explanatory popover |

### 6.10 Responsive behaviour

| Breakpoint | Frame | Content |
|---|---|---|
| ≥1200 px | 232 px rail | band 1180 px; two panels 58/42; fact strip 4 across |
| 900–1199 px | 64 px icon rail (tooltips) | panels 60/40; fact strip 2×2 |
| 640–899 px | 56 px top bar + drawer | single column; sticky bottom action bar |
| <640 px | same | full-width cards, 16 px padding, viewer pinch-zoom, list rows 56 px tall |

---

## 7. Implementation plan (A2)

| Stage | Work | Acceptance | Risk |
|---|---|---|---|
| **0. Frame & tokens** | Rail + top bar via `st.navigation`/page config; token refresh (rail, borders, radii 8/6, elevation); `Card`/`PageHeader`/`StatusBadge`/`EmptyState`/`IconButton` primitives on **native** components (`st.container(border=True)`, `st.popover`, `st.badge`, `st.segmented_control`) | Every page renders inside the frame; 202 tests still pass; no behavioural change | Low — visual only |
| **1. Home + Detect workspace** | Home as entry point (dropzone, real session facts); Detect as two-panel with fact strip, detection list, `Results/Details/JSON` tabs, params popover | Upload → Analyse → results fully usable; no invented numbers; tests updated for new structure | Medium — AppTest assertions change |
| **2. Image viewer (A2)** | Packaged CCv2 component from the official template (React + TS + Konva), payload builder tested in Python, `st.image` fallback | Zoom/pan/overlay/keyboard/list linking work; fallback verified; no pipeline change | **High** — new toolchain, component API, CI build |
| **3. Camera + Help + Developer** | Same shell; capture card; article layout; developer badges and tables | Consistent frame; audience split intact | Low |
| **4. Mobile & states** | Drawer nav, sticky action bar, skeleton/empty/error/toast coverage | <900 px usable one-handed; states all reachable | Medium |
| **5. Verification & delivery** | AppTest matrix, contrast + CSS guards, viewer unit tests, docs, PR #3 update | `pytest`/`ruff` green; no weakened honesty tests; screenshots pending browser | Low |

**Testing strategy:** keep every detection-correctness and honesty test; rewrite UI tests
against the new structure; add guards for the new tokens (rail contrast, focus ring, radii
set); add Python unit tests for the viewer payload (records → overlay primitives) so the JS
side has a tested contract; treat the viewer as optional at runtime, with a test that asserts
the fallback.

**Explicitly unchanged:** `app/core/*`, detection semantics, `rendering.py` output, upload
limits, camera capture, download bytes, Python/Streamlit stack, five routes, hidden
`/developer`, and every honesty guarantee (no fabricated outputs, subject-specific wording,
"Image analysis is temporarily unavailable" for users).

---

## 8. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Styling Streamlit internals stays brittle (33 testids today) | High | Medium | Move as much as possible to native components + config tokens; keep the bundle-hook test; cap custom selectors |
| CCv2 API churn between Streamlit minors | Medium | Medium | Pin Streamlit minor; keep the `st.image` fallback; isolate the component behind one Python module |
| Node toolchain in a Python repo (build step, lockfile, CI) | Medium | High | Only if Stage 2 is approved; commit built `asset_dir`; document the rebuild command; no CDN at runtime |
| AppTest cannot exercise canvas interaction | High | Medium | Test the payload contract in Python; manual browser checklist; fallback path asserted |
| Visual regressions without a browser in this environment | Certain | Medium | Numeric contrast guards + user review of the live preview; explicit "unseen" disclosure |
| Density vs. clarity: a professional UI can over-pack | Medium | Medium | Hard caps: one fact strip, ≤4 tiles, ≤2 tabs per card, 12 px minimum label size |
| Scope creep into a full React rewrite | Medium | High | Staged approval gates; B only on evidence (batch/video/multi-model) |
| Losing the honesty guarantees while redesigning | Low | Severe | The 202-test suite gates every stage; unusable-analysis state must stay a test, not a memory |

---

## 9. Decisions I need before implementation

1. **Architecture** — A2 staged (recommended: A1 now, viewer next), A1 only, or B (React + API).
2. **Navigation** — graphite rail (recommended, gives the app a frame and matches the density
   goal) versus keeping the light sidebar.
3. **Home** — application entry point with dropzone + real session facts (recommended) or the
   current editorial page with the drawn specimen pair.
4. **Timings** — show only measured values (inference ms, total ms). Showing
   preprocess/postprocess tiles like the reference would require instrumenting
   `app/core/detector.py`; I propose **not** doing that, so the UI never displays a number the
   pipeline does not measure. Confirm, or approve the instrumentation.
5. **Explicit analysis** — keep the *Analyse image* button (recommended: consent, cost,
   predictability) versus the reference's automatic inference on upload.
6. **Stage 2 approval** — the packaged CCv2 viewer adds a Node build. Approve in principle now,
   or decide after Stage 1 is visible.

---

## 10. What happens after approval

I implement in stage order on `arena/72af7497-judetector`, keep PR #3 updated, run `pytest`
and `ruff` at every stage, and report — for each stage — what changed, what the tests now
assert, and which parts still need a real browser. Nothing is merged into `main`.
