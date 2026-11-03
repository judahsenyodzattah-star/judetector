# `metrics/` — recorded evaluation results

This folder holds **evaluation records**: numbers produced by a real evaluation run
of a real model on real data. The Dashboard reads these files and displays them
verbatim.

**Nothing here is generated, estimated or filled in by the application.** If no
record exists, the Dashboard says so and shows no numbers.

## Recording your metrics

Create `metrics/<model-id>.json` — e.g. `metrics/judah-face-v1.json`:

```json
{
  "model_id": "judah-face-v1",
  "model_name": "judah model v1",
  "split": "test",
  "evaluated_on": "2026-11-15",
  "source": "Ultralytics HUB evaluation on the held-out test split",
  "metrics": {
    "mAP50": 0.0,
    "mAP50_95": 0.0,
    "precision": 0.0,
    "recall": 0.0
  },
  "per_class": {
    "judah": { "mAP50": 0.0, "precision": 0.0, "recall": 0.0 }
  },
  "curves": ["curves/pr_curve.png"],
  "notes": "Copied from my own evaluation run; no values changed."
}
```

Replace the `0.0` placeholders with **your** actual values.

### Rules the loader enforces

| Rule | Behaviour |
|---|---|
| `model_id` and `metrics` required | otherwise a visible schema error |
| Metrics must be numbers in `[0, 1]` | percentages such as `81.2` are rejected, not rescaled |
| Missing metrics stay missing | no defaulting, no interpolation |
| Unknown metric names | preserved and displayed under "additional metrics" |
| Accepted aliases | `mAP50`, `mAP50(B)`, `mAP50-95`, `mAP50_95`, `precision(B)`, `recall(B)`, `f1` |
| `curves` | relative paths to plot images shown beneath the metrics |

## Where do the numbers come from?

- **Ultralytics HUB** — open your trained model, run/lookup validation, copy the
  metrics shown for your validation or test split.
- **Local evaluation** — `model.val(data="data.yaml", split="test")` prints
  `mAP50`, `mAP50-95`, precision and recall.

> Report the split the numbers came from (`val` vs `test`) in the `split` field.
> Only the held-out test split is a fair final estimate.
