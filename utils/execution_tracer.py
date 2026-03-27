import threading
from datetime import datetime
from queue import Queue
from typing import Any, Dict, Optional


class ExecutionTracer:
    """Collects execution events and optionally streams them to a queue."""

    def __init__(self, event_queue: Optional[Queue] = None):
        self.event_queue = event_queue
        self.events = []
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

