from fastapi import Request

from app.timing import log_time


async def log_request_time(request: Request, call_next):
    """Log the total time of every HTTP request."""
    with log_time(f"{request.method} {request.url.path}"):
        return await call_next(request)
