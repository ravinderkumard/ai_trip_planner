import json
import logging

from utils.redis_client import RedisClient
from utils.travel_agent_runner import build_travel_query, run_travel_agent

logger = logging.getLogger(__name__)


class TravelAgentWorker:

    def __init__(self):
        self.redis = RedisClient()
        self.last_id = "0"   # ✅ STATE BELONGS HERE

    def start(self):
        logger.info("Travel Agent Worker Started")

        while True:
            messages = self.redis.client.xread(
                {"agent_tasks": self.last_id},
                block=5000
            )
            print("📥 RAW Redis messages:", messages)
            for stream, msgs in messages:
                for msg_id, data in msgs:
                    try:
                        task = json.loads(data["data"])
                    except (KeyError, json.JSONDecodeError):
                        logger.exception("Failed to decode worker task stream_id=%s", msg_id)
                        self.redis.publish_result(
                            {
                                "task_id": msg_id,
                                "agent": "travel_agent",
                                "status": "failed",
                                "output": "Invalid task payload received by worker.",
                            }
                        )
                        continue

                    if task.get("agent") != "travel_agent":
                        continue

                    self.process_task(task)
                    self.last_id = msg_id   # ✅ UPDATE AFTER READ

    def process_task(self, task):
        task_id = task.get("task_id", "unknown-task")

        logger.info("📦 Processing task_id=%s task=%s", task_id, task)

        try:
            input_data = task.get("input", {})
            if not input_data:
                raise ValueError("Missing input data")

            query = build_travel_query(input_data)

            logger.info("🧠 Running travel agent task_id=%s query=%s", task_id, query)

            result = run_travel_agent(query)

            if isinstance(result, dict):
                output = result.get("answer", "No answer returned")
            else:
                output = str(result)

            response = {
                "task_id": task_id,
                "agent": "travel_agent",
                "status": "success",
                "output": output,
                "saved_file": result.get("saved_file") if isinstance(result, dict) else None,
                "token_usage": result.get("token_usage", {}) if isinstance(result, dict) else {},
            }

            logger.info("✅ Task completed task_id=%s", task_id)

        except Exception as e:
            logger.exception("❌ Worker task failed task_id=%s", task_id)

            response = {
                "task_id": task_id,
                "agent": "travel_agent",
                "status": "failed",
                "output": str(e)
            }

        logger.info("📤 Publishing result task_id=%s status=%s", task_id, response["status"])
        self.redis.publish_result(response)
