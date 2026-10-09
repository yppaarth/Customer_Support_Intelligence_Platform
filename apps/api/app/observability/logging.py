import logging
import sys
import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Request, Response

SENSITIVE_KEYS = {"password", "authorization", "api_key", "token", "secret", "body"}


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='{"level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
        stream=sys.stdout,
    )


def redact(value: dict) -> dict:
    return {k: ("[REDACTED]" if k.lower() in SENSITIVE_KEYS else v) for k, v in value.items()}


async def correlation_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    correlation_id = request.headers.get("x-correlation-id", str(uuid4()))
    request.state.correlation_id = correlation_id
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["x-correlation-id"] = correlation_id
    response.headers["x-response-time-ms"] = str(round((time.perf_counter() - start) * 1000, 2))
    return response
