# JUDEtector — design direction

**Pass 1: exploration.** Approved direction: *Mostly A — Proof, with B's fixed-column
readout for detection results only.* Implementation notes and the review outcome are in
**§8 Pass 3** at the end of this document.

> **Superseded in Phase 5.** §1–§8 describe the proof-sheet interface that shipped in
> Phases 1–4. Phase 5 replaced its *structure* with an application frame: a dark
> navigation rail, a light workspace, cards, semantic colour roles and a detection list.
> The research, the measured audit and the architecture decision are in
> [`PHASE5_REFERENCE_REDESIGN.md`](PHASE5_REFERENCE_REDESIGN.md); the rules that no longer
> apply are listed in **§9**. Paper, crop marks and editorial treatments are no longer
> part of the interface; the warm canvas, the ochre marking colour and the monospace data
> voice are what survived.

Method note: there is no `frontend-design` skill installed in this sandbox. I searched the
whole filesystem (`find / -iname "SKILL.md"`, plus a directory sweep) and the only design
skill present is Streamlit's own `developing-with-streamlit`
(`.venv/.../streamlit/.agents/skills/developing-with-streamlit/SKILL.md`, with
`references/design.md`, `theme.md` and `layouts.md`). I read it in full and followed it as
the available methodology: prefer native theme tokens over CSS, sentence case, no dividers
for their own sake, native elements before custom HTML. If `frontend-design` can be
installed, install it and I will re-read it before Pass 2.

---

## 1. What the current interface is, and why it still reads as a template

Current state (PR #3, Phase 4): paper `#FAFAF8`, ink `#15181A`, one teal `#0F766E`,
hairline rules, system sans, 10px radii, no icons in content. It is legible, honest and
accessible. It is also anonymous.

- **The accent does no work.** Teal appears on the primary button, the focus ring, the
  active nav rule and the illustration. Nothing about it says *image analysis*. Swap the
  words and the same page could sell invoicing software.
- **The image is the least-designed element.** On Detect the upload preview is
  `st.image(width=380)`, floating in a column; the result is two default Streamlit columns
  with captions. The one thing this product exists to do — show you an image and then show
  you the same image marked — has the weakest treatment on the screen.
- **Every page is the same page.** Header, then a stack of sections of equal weight. Home,
  Detect, Camera and Help differ in copy length, not in composition. That is the signature
  of a template, not a product.
- **Home is still the landing formula**, just quieter: left copy block (headline,
  sentence, button, link), right illustration panel. The eyebrow badge is gone; the
  arrangement is not.
- **Numbers are set in prose type.** Counts, percentages, thresholds and dimensions have no
  tabular voice, so a result line reads like a sentence rather than a readout.
- **10px radii and 1px grey borders** are the default softness of every 2024–25 component
  library. Nothing in the surface treatment refers to photography, printing or inspection.
- **No mark of authorship.** Remove the one drawn illustration and there is no visual
  signature left — no repeated element, no metre, no rule that a reader would recognise on
  a second visit.

The brief is right that the answer is not another skin. What is missing is a **structural
idea**: one organising metaphor that decides composition, typography and colour at once.

---

## 2. Direction A — **Proof** (recommended)

### 2.1 Premise

The product's real subject is a pair: an image, and the same image marked. That is a
**proof** — a photographic proof print with crop marks and a caption.

So the interface behaves like a proof sheet, not a dashboard:

- The page is a sheet. Images are **mounted prints**: white mount, hairline crop marks at
  the corners, a mono **caption strip** underneath carrying real facts (file name,
  dimensions, file size, detection count).
- One vertical margin organises everything: headline, mount and caption all begin on the
  same left edge. Alignment is the design; no box needs to announce itself.
- Colour is reserved for **marking**. The chrome is ink on paper; the one accent is the
  colour of a grease pencil, used only where the machine has marked something or where you
  are about to act.

### 2.2 Palette — six named colours

| Token | Hex | Role | Measured contrast |
|---|---|---|---|
| **Sheet** | `#F4F2ED` | page ground (warm light grey, deliberately not cream) | ink on it 15.91:1 |
| **Mount** | `#FFFFFF` | image mounts, input surfaces, cards-that-are-really-prints | ink on it 17.8:1 |
| **Ink** | `#16181A` | all text, rules that carry meaning, primary button fill | 15.91 / 17.8:1 |
| **Ink soft** | `#52585C` | secondary text, caption fields, interactive borders | 6.45:1 on sheet, 7.22:1 on mount |
| **Rule** | `#D0CBC1` | crop marks, separators, table hairlines (decorative only) | 1.62:1 — never a control boundary |
| **Mark** | `#8A5A00` | the marking colour: annotation outline, "detected" label, primary action, active nav rule, focus ring | 5.93:1 on mount, 5.3:1 on sheet, white on it 5.93:1 |

Notes that matter:

- **Ochre, not red.** Red is the colour software uses for failure, and this app has a real
  failure state ("Image analysis is temporarily unavailable"). A vermilion accent
  (`#A63A2A`, 6.44:1) was the runner-up and lost on that collision. Ochre is the colour of
  a chinagraph pencil: it marks, it does not alarm.
- **`Rule` is decorative and never a control boundary.** Anything interactive (the uploader
  frame, focus rings) uses `Ink soft` or darker, so it clears the 3:1 non-text threshold at
  6.45–7.22:1.
- No green anywhere in the chrome, which removes the uploader's green-surface failure mode
  at the palette level rather than by override.

### 2.3 Typography — two roles, no pairing trend

One system grotesque for language; one system monospace for facts. No webfont, no Google
Fonts request, no serif accent words, no Space Grotesk / Instrument Serif pairing.

- **Text:** `-apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`
  — weights 400 / 500 / 600 only.
- **Facts:** `ui-monospace, SFMono-Regular, "SF Mono", "Cascadia Mono", Menlo, Consolas,
  monospace` — caption strips, filenames, dimensions, counts, confidences, thresholds,
  the wordmark set small in mono. Tabular numerals on by default.

Scale (seven steps, all rem): `0.72` caption field label (mono, +0.08em tracking) ·
`0.78` meta · `0.88` UI and control labels · `0.94` body (1.62 line-height) ·
`1.06` lead · `1.5` section title · `2.4` headline (`2.0` under 860px).

The typographic move that carries the identity: **a caption is a set of labelled fields**,
not a sentence — `FILE sample.png · FRAME 1024×768 · SIZE 214 KB`, labels in mono at 0.72rem,
values in mono at 0.78rem. On Home the same format describes the specimen; after analysis it
describes the real image. Home and the workspace speak the same language.

### 2.4 Spacing, grid, radii, borders

- Spacing: 4px base, `--s1…--s9` = 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96.
  Related items 8–16, groups 24–32, sections 64–96. No element gets an ad-hoc value.
- Grid: content width **1120px**, page padding 32px (mobile) / 64px (desktop),
  twelve columns with a 24px gutter, used as **5:7** (text : print) on Home and **7:5**
  (print : controls) in the workspace — the image always takes the larger share.
- Radii: **2px**. Not 10px. A printed sheet has square corners; softness was one of the
  things making the previous interface feel like a component library.
- Borders: hairline 1px `Rule` for separation; the uploader frame is the single 1.5px dashed
  boundary in the product, because it is the single place asking to be filled.

### 2.5 Homepage wireframe

```
 sheet ───────────────────────────────────────────────────────────────────────────────
 │ JUDEtector                                        Detect   Camera   Help          │  native nav, hairline under
 │                                                                                  │
 │  See exactly                                    ╭ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─╮ │
 │                                                 │ ╭─────────────────────────╮ │ │  crop marks
 │  what the model                                 │ │                         │ │ │
 │  sees.                                          │ │     specimen print      │ │ │  ← illustration only
 │                                                 │ │   (drawn, not model     │ │ │
 │  Upload an image to analyse it.                 │ │        output)          │ │ │
 │                                                 │ │                         │ │ │
 │  ┌───────────────────────────┐                  │ ╰─────────────────────────╯ │ │
 │  │   Analyse an image  →     │  primary         ╰ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─╯ │
 │  └───────────────────────────┘                  ILLUSTRATION · NOT A          │
 │  Use the camera instead                         DETECTION RESULT.             │
 │                                                                                  │
 │  ──────────────────────────────────────────────────────────────────────────────  │
 │  UPLOAD OR CAPTURE      ANALYSE          REVIEW             DOWNLOAD             │
 │  ●──────────────────────●────────────────●──────────────────●                    │  4 stations on one rule
 │                                                                                  │
 │  JUDEtector · images are processed in memory and never stored                    │
 │  Detection is not recognition.                                    Help →         │
 sheet ───────────────────────────────────────────────────────────────────────────────
```

Composition notes: headline, mount and rule share one left margin; the print is the widest
object on the page; the flow is a **rule with four stations** rather than a sentence or three
icon cards; the footer is one mono line plus one plain sentence.

### 2.6 Detection workspace wireframe

```
 │ Detect                                                                           │
 │ Upload an image to analyse it.                                                   │
 │                                                                                  │
 │  ╭ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ╮  │
 │  ┆        Drop an image here, or browse                                       ┆  │  1.5px dashed, Ink soft
 │  ┆        JPG · PNG · WEBP · BMP · 25 MB                                       ┆  │
 │  ╰ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ╯  │
 │                                                                                  │
 │  ╭───────────────────────────╮   FILE  sample.png                                │
 │  │                           │   FRAME 1024 × 768   SIZE 214 KB                  │
 │  │     mounted print         │   ────────────────────────────────────────────    │
 │  │                           │   Confidence threshold        0.25   ───●─────    │
 │  ╰───────────────────────────╯   Overlap (IoU)              0.45   ──●───────    │
 │                                  ▸ Advanced settings                             │
 │  ┌───────────────────┐                                                           │
 │  │  Analyse image    │                                                           │
 │  └───────────────────┘                                                           │
 │  ══════════════════════════════════════════════════════════════════════════════  │
 │  Result                                                                          │
 │  ╭───────────────╮ ╭───────────────╮   2 DETECTIONS                               │
 │  │  Original     │ │  Detected     │   mean 76.5%   min 62.0%   max 91.0%         │
 │  │               │ │   ▢      ▢    │   threshold 0.25   overlap 0.45   34 ms      │
 │  ╰───────────────╯ ╰───────────────╯                                             │
 │  ORIGINAL.png      DETECTED.png      ┌──────────────────────┐                    │
 │                                      │ Download annotated   │                    │
 │                                      └──────────────────────┘                    │
```

The result block is the payoff: two prints side by side under one shared caption row, with
the numbers as a mono **readout** to the right and the download at the end of that readout.
No metric cards, no tinted result band.

### 2.7 The single distinctive idea

> **A proof sheet: the page is a neutral mount, every image is mounted with crop marks and
> described by a mono caption strip, and the only colour in the product is the marking
> colour, used where the machine marked the image or where you act on it.**

Everything else follows from that sentence: the crop marks (framing), the caption strips
(real metadata, not labels for their own sake), the ochre accent (the pencil), the square
radii and the single margin (a sheet, not a card).

### 2.8 Page by page

| Page | Composition |
|---|---|
| **Home** | 5:7 text : print; headline, one sentence, one action, the mount, the four-station rule, mono footer. |
| **Detect** | 7:5 print : controls; uploader frame → mounted print + caption strip → thresholds as labelled sliders in a collapsed panel → one primary action → result as two prints + readout + download. |
| **Camera** | Same print grammar with the camera input in the mount slot; explicitly says one frame per capture, no live video. |
| **Help** | The only prose-heavy page, so it is set as a two-column text page with mono field labels (How it works / Reading the result / Your image / Limits) and no imagery. |
| **Developer** | Keeps its plain diagnostic density but uses the same caption-strip format for model facts, so it reads as the same product without borrowing consumer styling. |

### 2.9 How it lands in the existing architecture

- `.streamlit/config.toml` carries as much as possible natively (skill guidance):
  `primaryColor #8A5A00`, `backgroundColor #F4F2ED`, `secondaryBackgroundColor #FFFFFF`,
  `textColor #16181A`, `baseFontSize 15`, `codeFont` = mono, `radii` 2px if supported.
- `app/ui/theme.py` keeps a small stylesheet for what the theme cannot express: crop-mark
  corners, caption strips, the four-station rule, the mount padding around `st.image`,
  the uploader frame, focus rings.
- `app/ui/components.py` primitives become: `page_head`, `section`, `print_frame`,
  `caption_strip`, `readout`, `note`, `rule_flow`, `footer`. `empty_state`, `steps`,
  `bullets` and `kv_row` are re-expressed in that vocabulary rather than kept alongside it.
- The uploader fix stays structural: Streamlit paints the dropzone with `secondaryBg`, which
  is white here; the dropzone rule sets ink text, ink-soft instructions, and a browse button
  that is a plain ink-outlined control. Crops are CSS on `[data-testid="stImage"]`; captions
  are our own markdown, not `st.image(caption=...)`, because a caption must be a field strip.
- Unchanged: routes and Home as default, hidden `/developer` with no security claims, upload
  and camera, explicit *Analyse image*, original/annotated comparison, download, advanced
  settings collapsed, session statistics, model-unavailable behaviour, the detection
  pipeline, and every existing honesty guarantee.

---

## 3. Direction B — **Bench** (alternative, genuinely different)

### 3.1 Premise

Treat the app as an **instrument**: a measuring bench for images, not a document. Nothing is
staged; the tool is the product. Home is not a landing page at all — it is the bench with an
empty frame, because a bench you can touch is more credible than a picture of one.

### 3.2 Palette

| Token | Hex | Role | Contrast |
|---|---|---|---|
| **Plate** | `#FFFFFF` | frames, fields, readouts | graphite 17.66:1 |
| **Steel** | `#E9EBEA` | ground (cool, clinical) | graphite 14.75:1 |
| **Graphite** | `#16191B` | text, rules, primary action | — |
| **Pencil** | `#5A6065` | secondary text, borders | 5.32:1 on steel |
| **Hair** | `#C8CDCB` | grid lines, tick marks | decorative 1.61:1 |
| **Cobalt** | `#20439B` | the single signal: measurement caret, active state, action | 8.98:1 on plate |

### 3.3 Typography and layout

Mono-first: every label, number and control title is set in mono; sans appears only in
paragraphs (Help, notes). Numerals right-aligned in fixed columns, so readouts line up
vertically down the page. 8px baseline; a hard two-column field layout with a fixed 160px
label column; visible grid rules; a tick-mark ruler along the top edge of the frame, drawn
from real image dimensions.

### 3.4 Homepage wireframe

```
 │ JUDEtector                          image analysis      │ 01 Home  02 Detect  03 Camera │
 ├──────────────────────────────────────────────────────────────────────────────────────────
 │ ┌ 01 ────────────────────────────────────────────────┐
 │ │  Load an image                                     │
 │ │  ┌──────────────────────────────────────────────┐    │   ticks along the top edge
 │ │  │ ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  │    │
 │ │  │             empty frame, no specimen          │    │
 │ │  │                                              │    │
 │ │  └──────────────────────────────────────────────┘    │
 │ │  source ─────  none      size ─────  —       thresh ─  0.25 │
 │ └────────────────────────────────────────────────────┘
 │ ┌ 02 ────────────────────────────────────────────────┐
 │ │  Readout                                           │
 │ │  detections      0      mean       —      time     —  │
 │ └────────────────────────────────────────────────────┘
```

### 3.5 Verdict on B

It is disciplined and it would never be mistaken for a SaaS template, but:

- Mono-first chrome suits analysts; the stated audience is a **nontechnical user**, for whom
  an empty frame on the front page reads as "unfinished" rather than "ready".
- Its beauty depends on precision (tick alignment, tabular columns), and Streamlit renders
  sliders, metrics and images inside its own wrappers, so the precision would be approximate
  in the places that matter most.
- The instrument language borrows from Linear/Vercel-adjacent aesthetics, which is its own
  kind of convention — cooler, but still a costume.

---

## 4. Self-critique: what in these directions could still look AI-generated

| Risk | Direction | Mitigation already in the proposal |
|---|---|---|
| Warm paper + mono captions + one accent is itself a 2025 "tasteful editorial" recipe | A | No serif, no grain, no oversized italic accent, no all-caps manifesto; caption strips only carry **real data** and disappear when there is none; the accent appears on at most three elements per screen |
| Crop marks are a fashionable graphic flourish | A | They are drawn only around **actual images**, in the same rule colour used for real separators, and they are the alignment system (they mark the mount's extent), not a pattern |
| "Fake editorial" — labels invented to look designed (SUBJECT / SERIES / PLATE 01) | A | Banned. Fields are limited to file, frame, size, count, confidence, threshold — each already present in the app's data |
| A single large specimen on Home can read as a stock product preview | A | It is an abstract drawn plate, captioned as an illustration, and it is not a mock UI — no fake chrome, no fake numbers |
| Empty frame on Home can read as unfinished | B | Mitigated in B by tick marks and a live readout, but this is the reason B is not recommended |
| Mono-everything reads as "developer tool cosplay" | B | Sans for prose, mono only for labels/numbers |
| Numbered sections (01 / 02) are a template tic | B | They are the bench's station logic, but they would repeat on every page — a genuine risk |
| Both: a hairline grey interface can feel timid at small sizes | A, B | Direction A uses a 2.4rem headline and a print at ≥55% width so the sheet has one clearly dominant object per screen |

One more: a design like this can fail by being *too* quiet on a laptop. The counterweight is
compositional, not decorative — one large object, one strong margin, one saturated mark.

---

## 5. Recommendation

**Direction A — Proof.** Reasons, in order:

1. It derives from the product's actual pair (original / annotated) instead of from a
   design trend, so it can survive future feature work rather than needing a new skin.
2. It fixes the two weakest things in the current build by construction: the image becomes
   the largest object on every screen with a real mount and a caption, and Home stops being
   a left-copy/right-panel landing page.
3. The caption strip is **functional**: it is where file name, dimensions, size, count and
   confidence belong, so the identity adds information density instead of decoration.
4. A nontechnical user reads a proof sheet instantly: a picture, marked, captioned.
5. Ochre + ink + white mounts contains no purple, teal, gradient or glass, and its contrast
   is verifiable (all text ≥ 5.3:1, controls ≥ 6.4:1).

---

## 6. Decisions I need before building

1. **Direction** — A (Proof), B (Bench), or a stated mix.
2. **Mark colour** — ochre `#8A5A00` (recommended) or the runner-up vermilion `#A63A2A`.
3. **Specimen on Home** — keep a drawn plate on the mount (recommended, captioned as an
   illustration) or leave the mount empty with instruction text only, so nothing on Home can
   be mistaken for output.

## 7. What Pass 2 will and will not change

Will change: `.streamlit/config.toml` theme tokens, `app/ui/theme.py`, `app/ui/components.py`
and the four consumer views plus the developer page's presentation; the uploader's rendered
treatment; the result readout; tests that assert the old visual language.

Will not change: `app/core/*`, the registry, rendering colours of detection boxes, the
detection pipeline, routes, `/developer` separation and its "hidden, not access-controlled"
wording, the model-unavailable behaviour, upload/camera/analyse/download semantics, and
every honesty guarantee. No new dependencies, no webfonts, no animation, no JS.


---

## 8. Pass 3 — what was built, and what review changed

**Approved:** Direction A (Proof) as the design language, with the fixed-column numeric
readout borrowed from B for actual detection results only — no industrial styling, no
rulers, no numbered stations, no instrument panels.

### Delivered

| Piece | Implementation |
|---|---|
| Sheet, mounts, ink, hairlines, marking colour | Tokens in `.streamlit/config.toml` (native, so Streamlit's own widgets inherit them) and `app/ui/theme.py` |
| Mounted print | `plate()` for drawn plates, and Streamlit images styled as mounts with two hairline registration marks in the mount's top-left and bottom-right corners |
| Caption strip | `caption_strip()` — monospace `LABEL value` pairs for file, frame, size |
| Readout | `readout()` — fixed label column, monospace values right-aligned, tabular numerals; used for results and for the developer page's facts |
| Flow | `flow_line()` — four stations on one rule, used once on Home; Help keeps numbered steps because a how-to is genuinely ordered |
| Home | The same specimen mounted twice (*Original*, *Annotated*) as the page's primary visual, captioned "Illustration, not an actual detection result."; one primary action, one camera page link, no fake chrome |
| Brand marks | Redrawn from the palette: an ink plate with white registration corners and one ochre rule, replacing the teal rounded badge and the Inter reference |

### Adjustments made against the approved brief

1. **The homepage pair is honest by construction.** `specimen_svg()` builds both plates from
   one function; the annotated version is the identical string plus one marking rectangle.
   A test strips the rectangle and asserts equality, so "identical except for the marking"
   cannot silently drift.
2. **No invented measurements.** The readout shows count, mean confidence, confidence range
   and the two applied thresholds — all emitted by `DetectionResult`. Processing time is
   measured with `perf_counter` and stays in the collapsed detail section. Confidence rows
   disappear when a result has none, so an empty result never shows a placeholder score.
3. **The image stays dominant.** Detect is a 7:5 split with the print on the left and the
   controls beside it; each result print is half the content width. Registration marks are
   1px hairlines outside the mount, never over the image.
4. **Monospace is selective.** Caption strips, readout labels and values, plate captions and
   slider values only. Prose (`meta`, footer, notes, Help) is set in the sans stack — a
   review pass caught and fixed two places where sentences had leaked into mono.
5. **The uploader is still structural.** `secondaryBackgroundColor` is `#FFFFFF`, so
   Streamlit paints the dropzone white at the theme level; the rule then sets ink label,
   ink-2 instructions, a 1.5px dashed ink-2 frame at 7.2:1, and a white browse button with
   ochre text and a 1px ochre outline. Hover, focus-within and disabled states are asserted.
6. **Ochre discipline is enforced, not just intended.** A test rejects any background set to
   the marking colour outside the primary action, another asserts the neutral pieces contain
   no marking colour, and a third asserts the accent is numerically distant from every
   colour the detector draws with.
7. **Nothing fashionable was added.** Tests fail on gradients, filters, backdrop-filter,
   text shadows, keyframes, transforms, transitions and any non-focus `box-shadow`; the only
   radius in the stylesheet is 2px; the type scale is exactly nine steps.

### Outstanding

No browser exists in this environment, so the rendered result has not been seen: colours are
verified numerically and against the installed Streamlit source, layout is verified through
`AppTest` and CSS breakpoints, and the dropzone's painted appearance on a real display still
needs a human check.

---

## 9. Phase 5 — what supersedes §1–§8

Approved in Phase 5 and implemented in Stage 0–1. Where this section contradicts an
earlier rule, this section wins.

**Superseded**

| Earlier rule | Now |
|---|---|
| "A proof sheet, not a dashboard"; no cards | Bordered cards hold every task surface (`st.container(border=True)`), with an 8px radius |
| "Avoid cards, icons and surfaces" | Icons are used where a destination or action needs one, from Material Symbols Rounded only |
| Corners are 2px; type scale is nine steps | Radii are 8px (cards) and 6px (controls); type is seven steps: 0.72 / 0.78 / 0.84 / 0.88 / 0.94 / 1.06 / 1.375 rem |
| Spacing scale 4–96px (`--jd-1`…`--jd-9`) | Spacing scale 4/8/12/16/24/32/48px (`--jd-1`…`--jd-7`) |
| Plates, caption strips, crop marks, flow rules, footers | Page header, card, card header, fact strip, detection list, empty state, note, steps, bullets, readout, specimen |
| Home mounts the specimen twice with a primary CTA button | Home is an entry point: the upload control is the primary action and hands off to Detect without inferring; one small captioned plate remains |
| Filters/panel colour: white only | Three surfaces are allowed: canvas `#F4F2ED`, cards `#FFFFFF`, rail `#1E2122` |
| Ochre only in the primary action, focus and annotations | Ochre also draws the 2px active rule in the rail; it still never fills a panel, badge or tinted section |

**Retained**

- Ochre `#8A5A00` remains the only accent, and remains numerically distant from every
  colour the detector draws with.
- No gradients, filters, text shadows, keyframes, transforms or transitions; the only
  `box-shadow` is the focus ring.
- Monospace for data only; prose stays sans.
- The uploader keeps a white surface derived from `secondaryBackgroundColor`, an ink-2
  dashed frame and all four interaction states.
- Honesty rules: no invented metrics, explicit *Analyse image*, timings shown only when
  measured (`<1 ms` rather than `0 ms`), and honest unavailable states.

**Added**

- Contrast is now asserted for the dark rail as well as the light workspace, including
  the active destination, whose ochre indicator is a rule rather than a fill.
- The active rail item is themed natively through `[theme.sidebar]` in
  `.streamlit/config.toml`, plus one CSS rule for the active indicator — no
  high-specificity repainting of Streamlit internals.
- `app/ui/components.py` primitives carry no logic; every number they render is passed in
  from a measurement.
