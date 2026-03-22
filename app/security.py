import os
import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException, Request, status


class InMemoryRateLimiter:
    def __init__(self, max_requests: int = 60, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def check(self, client_id: str) -> None:
        now = time.time()
        bucket = self._requests[client_id]
        while bucket and now - bucket[0] > self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Limite de requisicoes excedido. Tente novamente em instantes.",
            )
        bucket.append(now)


rate_limiter = InMemoryRateLimiter()


def get_client_id(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def rate_limit_dependency(request: Request) -> None:
    rate_limiter.check(get_client_id(request))


def api_key_dependency(x_api_key: str | None = Header(default=None)) -> None:
    configured_key = os.getenv("BOLETO_AUTH_API_KEY")
    if configured_key and x_api_key != configured_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key invalida ou ausente.",
        )
