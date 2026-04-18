import threading
from datetime import datetime
from queue import Queue
from typing import Any, Dict, Optional


class ExecutionTracer:
    """Collects execution events and optionally streams them to a queue."""

    def __init__(self, event_queue: Optional[Queue] = None):
        self.event_queue = event_queue
        self.events = []
        self.token_usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }
        self._lock = threading.Lock()

    def log(self, event_type: str, message: str, **details: Any) -> Dict[str, Any]:
        event = {
            "type": event_type,
            "message": message,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "details": details,
        }
        with self._lock:
            self.events.append(event)
        if self.event_queue is not None:
            self.event_queue.put(event)
        return event

    def add_token_usage(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: int = 0,
    ) -> Dict[str, int]:
        with self._lock:
            self.token_usage["input_tokens"] += input_tokens
            self.token_usage["output_tokens"] += output_tokens
            self.token_usage["total_tokens"] += total_tokens
            return dict(self.token_usage)

    def get_token_usage(self) -> Dict[str, int]:
        with self._lock:
            return dict(self.token_usage)
