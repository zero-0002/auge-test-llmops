import os
import time
import json
import asyncio
import logging
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

API_KEY = os.getenv("API_KEY", "test-secret-key")
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000")

MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "4"))
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm-gateway")

app = FastAPI(title="LLMOps Test Gateway")

REQUEST_COUNT = Counter(
    "llm_requests_total",
    "Total LLM requests",
    ["endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "llm_request_latency_seconds",
    "LLM request latency",
    ["endpoint"]
)

ACTIVE_REQUESTS = Gauge(
    "llm_active_requests",
    "Current active LLM requests"
)


def check_api_key(request: Request):
    auth = request.headers.get("Authorization", "")
    expected = f"Bearer {API_KEY}"

    if auth != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@app.get("/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            res = await client.get(f"{VLLM_BASE_URL}/health")
            vllm_ok = res.status_code == 200
    except Exception:
        vllm_ok = False

    return {
        "gateway": "ok",
        "vllm": "ok" if vllm_ok else "unavailable"
    }


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    check_api_key(request)

    if semaphore.locked():
        REQUEST_COUNT.labels(endpoint="/v1/chat/completions", status="overloaded").inc()
        raise HTTPException(status_code=429, detail="Too many concurrent requests")

    payload = await request.json()
    stream = payload.get("stream", False)

    start = time.time()
    ACTIVE_REQUESTS.inc()

    async with semaphore:
        try:
            if stream:
                return await stream_to_vllm(payload, start)

            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{VLLM_BASE_URL}/v1/chat/completions",
                    json=payload
                )

            latency = time.time() - start
            REQUEST_LATENCY.labels(endpoint="/v1/chat/completions").observe(latency)
            REQUEST_COUNT.labels(endpoint="/v1/chat/completions", status=str(response.status_code)).inc()

            logger.info(json.dumps({
                "event": "chat_completion",
                "status_code": response.status_code,
                "latency_seconds": round(latency, 3),
                "model": payload.get("model"),
                "stream": False
            }))

            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )

        except Exception as e:
            latency = time.time() - start
            REQUEST_COUNT.labels(endpoint="/v1/chat/completions", status="error").inc()

            logger.error(json.dumps({
                "event": "chat_completion_error",
                "error": str(e),
                "latency_seconds": round(latency, 3)
            }))

            raise HTTPException(status_code=500, detail=str(e))

        finally:
            ACTIVE_REQUESTS.dec()


async def stream_to_vllm(payload: dict, start: float):
    async def generator() -> AsyncGenerator[bytes, None]:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{VLLM_BASE_URL}/v1/chat/completions",
                json=payload
            ) as response:
                async for chunk in response.aiter_bytes():
                    yield chunk

        latency = time.time() - start
        REQUEST_LATENCY.labels(endpoint="/v1/chat/completions").observe(latency)
        REQUEST_COUNT.labels(endpoint="/v1/chat/completions", status="streamed").inc()

        logger.info(json.dumps({
            "event": "chat_completion_stream",
            "latency_seconds": round(latency, 3),
            "model": payload.get("model"),
            "stream": True
        }))

    return StreamingResponse(generator(), media_type="text/event-stream")
