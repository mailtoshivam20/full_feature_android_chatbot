import time

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import get_redis

RATE_LIMITS: dict[str, tuple[int, int]] = {
    "/api/v1/generate": (10, 60),
    "/api/v1/chats": (60, 60),
    "/api/v1/auth/login": (10, 60),
    "/api/v1/auth/register": (5, 60),
    "default": (120, 60),
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract user id from JWT if present (best-effort, no DB call)
        client_id = request.client.host if request.client else "unknown"
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            from app.core.security import decode_token
            payload = decode_token(auth[7:])
            if payload.get("sub"):
                client_id = payload["sub"]

        path = request.url.path
        limit, window = next(
            (v for k, v in RATE_LIMITS.items() if k != "default" and path.startswith(k)),
            RATE_LIMITS["default"],
        )

        redis = get_redis()
        key = f"rl:{client_id}:{path}"
        now = int(time.time())
        window_start = now - window

        try:
            pipe = redis.pipeline()
            await pipe.zremrangebyscore(key, 0, window_start)
            await pipe.zadd(key, {str(now): now})
            await pipe.zcard(key)
            await pipe.expire(key, window)
            results = await pipe.execute()
            count = results[2]

            if count > limit:
                return JSONResponse(
                    status_code=429,
                    content={"code": "RATE_LIMITED", "detail": "Too many requests"},
                )
        except Exception:
            pass  # Redis unavailable: allow through

        return await call_next(request)
