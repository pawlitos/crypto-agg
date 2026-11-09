from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.collector import Collector
from app.middlewares import log_request_time
from app.routers import prices


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
app.include_router(prices.router)
