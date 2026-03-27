import logging
import threading
import time
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> tuple[bool, int]:
        now = time.time()
        with self._lock:
            timestamps = self._requests[key]
            window_start = now - self.window_seconds

            while timestamps and timestamps[0] <= window_start:
                timestamps.popleft()

            if len(timestamps) >= self.max_requests:
                retry_after = max(1, int(timestamps[0] + self.window_seconds - now))
                logger.warning("Rate limit exceeded for key=%s retry_after=%s", key, retry_after)
                return False, retry_after

            timestamps.append(now)
            return True, 0
