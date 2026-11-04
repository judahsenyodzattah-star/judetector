"""Rate limiting.

**What this does and does not protect.** The default backend is an in-process
sliding window. It is per *instance*: with N replicas behind a load balancer a
client can consume the limit on each one, so it bounds accidental load and
runaway clients on a single instance, not a determined abuser.

Global protection belongs at the edge — Cloud Armor, API Gateway, Cloudflare or
an equivalent — or in a shared store such as Redis. `build_limiter` therefore
returns a documented interface rather than hard-coding one policy, responses
carry `RateLimit-*` headers with `RateLimit-Scope`, and `docs/API.md` states the
dependency instead of implying process-local limits are global.
"""

from __future__ import annotations

import math
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from api.errors import problem_response
from api.settings import Settings

__all__ = [
    "InProcessRateLimiter",
    "LIMITED_PATH",
    "NoRateLimit",
    "RateLimitMiddleware",
    "RateLimitResult",
    "RateLimiter",
    "build_limiter",
    "client_key",
    "rate_limit_headers",
]

LIMITED_PATH = "/v1/detect"


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_after_s: float


class RateLimiter(Protocol):
    """Anything that can answer 'may this key proceed?'."""

    scope: str

    def check(self, key: str) -> RateLimitResult: ...


class NoRateLimit:
    """Explicitly no limiting. Used when an edge enforces it instead."""

    scope = "none"

    def check(self, key: str) -> RateLimitResult:  # noqa: ARG002 - protocol shape
        return RateLimitResult(allowed=True, limit=0, remaining=0, reset_after_s=0.0)


class InProcessRateLimiter:
    """Sliding window over the last `window_s`, per key, inside this process only."""

    scope = "instance"

    def __init__(
        self,
        limit: int,
        window_s: float = 60.0,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if limit <= 0:
            raise ValueError("limit must be positive")
        self._limit = limit
        self._window = window_s
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> RateLimitResult:
        now = self._clock()
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            cutoff = now - self._window
            while hits and hits[0] <= cutoff:
                hits.popleft()

            if len(hits) >= self._limit:
                reset = max(0.0, self._window - (now - hits[0]))
                return RateLimitResult(
                    allowed=False,
                    limit=self._limit,
                    remaining=0,
                    reset_after_s=reset,
                )

            hits.append(now)
            return RateLimitResult(
                allowed=True,
                limit=self._limit,
                remaining=max(0, self._limit - len(hits)),
                reset_after_s=self._window,
            )


def build_limiter(settings: Settings) -> RateLimiter:
    """Choose a limiter from configuration.

    `memory` (default) is per-instance; `none` disables limiting in the service so
    an upstream edge limiter can be authoritative. There is deliberately no
    "global in-process" option, because that would be a false claim.
    """
    backend = settings.rate_limit_backend.strip().lower()
    if backend in {"none", "off", "disabled"}:
        return NoRateLimit()
    return InProcessRateLimiter(settings.rate_limit_per_minute)


def rate_limit_headers(decision: RateLimitResult, scope: str) -> dict[str, str]:
    """Standard-ish `RateLimit-*` headers, always reporting the real scope."""
    if decision.limit <= 0:
        return {"RateLimit-Scope": scope}
    return {
        "RateLimit-Limit": str(decision.limit),
        "RateLimit-Remaining": str(decision.remaining),
        "RateLimit-Reset": str(max(0, math.ceil(decision.reset_after_s))),
        "RateLimit-Scope": scope,
    }


class RateLimitMiddleware:
    """Limit `POST /v1/detect` and stamp the quota on every response.

    Middleware rather than a route dependency so the headers survive error
    paths: a `429`, a `413` or a `503` still tells the caller where the quota
    stands, and the limit is applied before the upload is parsed.
    """

    def __init__(self, app: ASGIApp, settings: Settings, limiter: RateLimiter) -> None:
        self.app = app
        self.settings = settings
        self.limiter = limiter

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or scope.get("method") != "POST"
            or scope.get("path") != LIMITED_PATH
        ):
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        client = scope.get("client")
        host = client[0] if client else None
        forwarded = Headers(scope=scope).get("x-forwarded-for")
        decision = self.limiter.check(client_key(self.settings, host, forwarded))
        headers = rate_limit_headers(decision, self.limiter.scope)

        if not decision.allowed:
            retry_after = max(1, math.ceil(decision.reset_after_s))
            response = problem_response(
                request,
                status=429,
                type_="rate_limited",
                title="Too many requests",
                detail=(
                    f"The limit is {decision.limit} analyses per minute on this "
                    f"instance. Retry in {retry_after} seconds."
                ),
                headers={**headers, "Retry-After": str(retry_after)},
            )
            await response(scope, receive, send)
            return

        extra = [(name.lower().encode("latin-1"), value.encode("latin-1"))
                 for name, value in headers.items()]

        async def send_with_quota(message: Message) -> None:
            if message["type"] == "http.response.start":
                message = {**message, "headers": [*message["headers"], *extra]}
            await send(message)

        await self.app(scope, receive, send_with_quota)


def client_key(settings: Settings, client_host: str | None, forwarded_for: str | None) -> str:
    """Identify a caller for rate-limit purposes.

    Behind a trusted proxy the first `X-Forwarded-For` entry is the client;
    otherwise the socket address is used. The header is spoofable, so
    `JUDETECTOR_TRUST_PROXY` is off by default and documented as a deployment
    requirement.
    """
    if settings.trust_proxy and forwarded_for:
        first = forwarded_for.split(",")[0].strip()
        if first:
            return first
    return client_host or "unknown"
