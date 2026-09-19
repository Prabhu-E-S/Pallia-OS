"""In-memory rate limiting (extension point).

A single-process, process-local limiter is enough for development and single
node deployments. Replace this module with a Redis-backed limiter when the
service runs behind multiple workers.

Current policy: limit failed + successful login attempts per
``(email, client_ip)`` within a sliding window.
"""

import time
from collections import defaultdict, deque
from threading import Lock

from app.core.config import get_settings
from app.core.errors import TooManyRequestsError


class SlidingWindowLimiter:
    """Tracks recent events per key in a sliding time window."""

    def __init__(self, max_events: int, window_seconds: int) -> None:
        self._max_events = max_events
        self._window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _prune(self, key: str, now: float) -> deque[float]:
        events = self._events[key]
        cutoff = now - self._window_seconds
        while events and events[0] <= cutoff:
            events.popleft()
        if not events:
            self._events.pop(key, None)
        return self._events[key]

    def allow(self, key: str) -> bool:
        """True if the key has not exceeded the event budget."""
        with self._lock:
            remaining = len(self._prune(key, time.monotonic()))
            if remaining >= self._max_events:
                return False
            return True

    def record(self, key: str) -> None:
        with self._lock:
            now = time.monotonic()
            events = self._prune(key, now)
            events.append(now)


class LoginRateLimiter:
    """Applies the login rate-limit policy and raises on hard limits."""

    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self._limiter = SlidingWindowLimiter(max_attempts, window_seconds)

    def check(self, email: str, client_ip: str | None) -> None:
        key = f"{email}|{client_ip or 'unknown'}"
        if not self._limiter.allow(key):
            raise TooManyRequestsError("Too many login attempts, try again later")

    def record(self, email: str, client_ip: str | None) -> None:
        key = f"{email}|{client_ip or 'unknown'}"
        self._limiter.record(key)


_settings = get_settings()
login_limiter = LoginRateLimiter(
    max_attempts=_settings.login_max_attempts,
    window_seconds=_settings.login_rate_window_seconds,
)
