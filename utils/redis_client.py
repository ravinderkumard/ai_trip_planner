import json
import os

import redis


class RedisClient:
    @staticmethod
    def _default_redis_host() -> str:
        if os.getenv("REDIS_HOST"):
            return os.getenv("REDIS_HOST", "localhost")
        if os.path.exists("/.dockerenv"):
            return "host.docker.internal"
        return "localhost"

    def __init__(self):
        self.client = redis.Redis(
            host=self._default_redis_host(),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            password=os.getenv("REDIS_PASSWORD") or None,
            decode_responses=True
        )

    def read_tasks(self):
        return self.client.xread({"agent_tasks": "0"}, block=5000)

    def publish_result(self, data):
        self.client.xadd("agent_results", {
            "data": json.dumps(data)
        })
