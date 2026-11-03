# `models/` — where trained weights go

**Model weights are never committed to this repository.** `*.pt`, `*.onnx`,
`*.pth` and `*.engine` are blocked by `.gitignore`.

## Expected layout

```
models/
├── README.md                          # this file
├── judah-face-v1/
│   └── best.pt                        # your trained Ultralytics weights
└── general-face-v1/                   # optional future model
    └── best.pt
```

The active model's path is declared in [`config/models.json`](../config/models.json)
under the `weights` key, and can be overridden at runtime:

```bash
export JUDETECTOR_MODEL_PATH=/absolute/path/to/best.pt
```

## Which model is currently registered?

| id | path | kind | labels | present? |
|---|---|---|---|---|
| `judah-face-v1` | `models/judah-face-v1/best.pt` | subject-specific | `judah` | no (not supplied) |
| `general-face-v1` | `models/general-face-v1/best.pt` | general-purpose | `face` | no (template, disabled) |

Until weights are supplied, the application starts normally and reports
*"weights missing"* on every page. It will not display detections it cannot produce.

See [`docs/MODEL_INTEGRATION.md`](../docs/MODEL_INTEGRATION.md) for the full procedure.
