import json
import logging
import os
import threading
from queue import Queue

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from starlette.responses import JSONResponse

from utils.execution_tracer import ExecutionTracer
from utils.prompt_injection_guard import contains_suspicious_prompt_patterns
from utils.rate_limiter import InMemoryRateLimiter
from utils.travel_agent_runner import run_travel_agent
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "10"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))


def get_allowed_origins() -> list[str]:
    configured_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
    if not configured_origins.strip():
        return DEFAULT_ALLOWED_ORIGINS
    return [origin.strip() for origin in configured_origins.split(",") if origin.strip()]


def get_client_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "").strip()
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown-client"


rate_limiter = InMemoryRateLimiter(
    max_requests=RATE_LIMIT_MAX_REQUESTS,
    window_seconds=RATE_LIMIT_WINDOW_SECONDS,
)


def enforce_rate_limit(request: Request) -> JSONResponse | None:
    client_id = get_client_identifier(request)
    limiter_key = f"{client_id}:{request.url.path}"
    allowed, retry_after = rate_limiter.allow(limiter_key)
    if allowed:
        return None
    logger.warning("Blocking request due to rate limit path=%s client=%s", request.url.path, client_id)
    return JSONResponse(
        status_code=429,
        content={"error": "Too many requests. Please try again later."},
        headers={"Retry-After": str(retry_after)},
    )


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["Content-Type", "Authorization"],
)


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Question must not be empty.")
        return normalized

@app.post("/query")
async def query_travel_agent(query:QueryRequest, request: Request):
    try:
        rate_limited_response = enforce_rate_limit(request)
        if rate_limited_response is not None:
            return rate_limited_response
        if contains_suspicious_prompt_patterns(query.question):
            logger.warning("Rejected suspicious synchronous query")
            return JSONResponse(
                status_code=400,
                content={"error": "The request contains unsupported instruction patterns."},
            )
        logger.info("Received synchronous travel query")
        return run_travel_agent(query.question)
    except Exception:
        logger.exception("Travel agent request failed")
        return JSONResponse(
            status_code=500,
            content={"error": "The request could not be processed at this time."},
        )


@app.post("/query/stream")
async def query_travel_agent_stream(query: QueryRequest, request: Request):
    rate_limited_response = enforce_rate_limit(request)
    if rate_limited_response is not None:
        return rate_limited_response
    if contains_suspicious_prompt_patterns(query.question):
        logger.warning("Rejected suspicious streaming query")
        return JSONResponse(
            status_code=400,
            content={"error": "The request contains unsupported instruction patterns."},
        )
    logger.info("Received streaming travel query")
    event_queue: Queue = Queue()
    tracer = ExecutionTracer(event_queue=event_queue)

    def worker():
        try:
            result = run_travel_agent(query.question, tracer=tracer)
            event_queue.put({"type": "final", "timestamp": "", "message": "Workflow completed", "details": result})
        except Exception:
            logger.exception("Streaming travel agent request failed")
            event_queue.put(
                {
                    "type": "error",
                    "timestamp": "",
                    "message": "The request could not be processed at this time.",
                    "details": {},
                }
            )
        finally:
            event_queue.put(None)

    threading.Thread(target=worker, daemon=True).start()

    def event_stream():
        while True:
            event = event_queue.get()
            if event is None:
                break
            yield json.dumps(event) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")
