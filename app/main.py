from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request

from app.collector import Collector
from app.middlewares import log_request_time
from app.schemas import PricesResponse


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
app.middleware("http")(log_request_time)


def get_collector(request: Request) -> Collector:
    """Background price collector created in lifespan."""
    return request.app.state.collector


CollectorDep = Annotated[Collector, Depends(get_collector)]


@app.get("/v1/prices")
async def prices(collector: CollectorDep) -> PricesResponse:
    return collector.snapshot()
