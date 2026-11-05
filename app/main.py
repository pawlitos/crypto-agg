import asyncio
from contextlib import asynccontextmanager
from typing import Annotated

import ccxt.async_support as ccxt
from fastapi import Depends, FastAPI, Request

from app.schemas import ExchangePrices, PricesResponse
from app.timing import log_time

EXCHANGES = ["kraken", "bybit", "okx"]
PAIRS = ["BTC/USDT", "BTC/USDC", "ETH/USDT", "ETH/USDC"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    clients: dict[str, ccxt.Exchange] = {}
    app.state.clients = clients
    try:
        for ex_id in EXCHANGES:
            clients[ex_id] = getattr(ccxt, ex_id)()
        with log_time("startup: load_markets (all exchanges)"):
            await asyncio.gather(*(c.load_markets() for c in clients.values()), return_exceptions=True)
        yield
    finally:
        await asyncio.gather(*(c.close() for c in clients.values()), return_exceptions=True)
        clients.clear()


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def log_request_time(request: Request, call_next):
    """Log the total time of every HTTP request."""
    with log_time(f"{request.method} {request.url.path}"):
        return await call_next(request)


def get_clients(request: Request) -> dict[str, ccxt.Exchange]:
    """Exchange clients created in lifespan, keyed by exchange id."""
    return request.app.state.clients


ClientsDep = Annotated[dict[str, ccxt.Exchange], Depends(get_clients)]


async def fetch_one(exchange: ccxt.Exchange) -> dict[str, float | None]:
    await exchange.load_markets()  # no-op if already loaded; retries if startup failed
    symbols = [p for p in PAIRS if p in exchange.markets]
    tickers = await exchange.fetch_tickers(symbols)
    return {p: tickers.get(p, {}).get("last") for p in PAIRS}


@app.get("/v1/prices")
async def prices(clients: ClientsDep) -> PricesResponse:
    results = await asyncio.gather(
        *(fetch_one(clients[ex_id]) for ex_id in EXCHANGES),
        return_exceptions=True,
    )
    return {
        ex_id: ExchangePrices(error=str(res)) if isinstance(res, Exception) else ExchangePrices(prices=res)
        for ex_id, res in zip(EXCHANGES, results)
    }
