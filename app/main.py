from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request

from app.collector import Collector
from app.schemas import PricesResponse
from app.timing import log_time


@asynccontextmanager
async def lifespan(app: FastAPI):
    collector = Collector()
    app.state.collector = collector
    collector.start()
    try:
        yield
    finally:
        await collector.stop()


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def log_request_time(request: Request, call_next):
    """Log the total time of every HTTP request."""
    with log_time(f"{request.method} {request.url.path}"):
        return await call_next(request)


def get_collector(request: Request) -> Collector:
    """Background price collector created in lifespan."""
    return request.app.state.collector


CollectorDep = Annotated[Collector, Depends(get_collector)]


@app.get("/v1/prices")
async def prices(collector: CollectorDep) -> PricesResponse:
    return collector.snapshot()
