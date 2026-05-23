import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.routes.metrics import http_request_duration_seconds


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        if request.url.path != "/metrics/metrics":
            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=str(response.status_code)
            ).observe(duration)

        return response
