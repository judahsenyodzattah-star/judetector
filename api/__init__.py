"""JUDEtector inference API.

A thin FastAPI surface over the existing, unchanged detection engine in
`app/core` and `app/components/pipeline.py`. Nothing here re-implements
detection: the API validates a request, calls the same pipeline the Streamlit
prototype calls, and serialises the same measurements.

Service-level rules, enforced by tests:

* No fabricated output. When weights or the ML stack are missing, the service
  reports `degraded` and `/v1/detect` returns a problem document instead of
  detections.
* No leakage. Problem documents never contain filesystem paths, dependency
  names, stack traces or registry keys.
* No retention. Requests are processed in memory; responses are `no-store`.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0"
