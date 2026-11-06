import asyncio
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Annotated, cast

import ccxt.async_support as ccxt
from ccxt.base.types import Ticker, Tickers
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
    markets = await exchange.load_markets()  # cached after the first call; retries if startup failed
    symbols = [p for p in PAIRS if p in markets]
    # ccxt's base Exchange.fetch_tickers only raises NotSupported (each exchange overrides it),
    # so type checkers think it never returns. Re-declare it with its real return type.
    fetch_tickers = cast(Callable[[list[str]], Awaitable[Tickers]], exchange.fetch_tickers)
    tickers = await fetch_tickers(symbols)
    return {p: last_price(tickers.get(p)) for p in PAIRS}


def last_price(ticker: Ticker | None) -> float | None:
    """Last traded price as float; ccxt types it loosely (str, int, Decimal, ...)."""
    if ticker is None or ticker["last"] is None:
        return None
    return float(ticker["last"])


@app.get("/v1/prices")
async def prices(clients: ClientsDep) -> PricesResponse:
    results = await asyncio.gather(
        *(fetch_one(clients[ex_id]) for ex_id in EXCHANGES),
        return_exceptions=True,
    )
    out: dict[str, ExchangePrices] = {}
    for ex_id, res in zip(EXCHANGES, results):
        if isinstance(res, Exception):
            out[ex_id] = ExchangePrices(error=str(res))
        elif isinstance(res, BaseException):
            raise res  # e.g. CancelledError when the request is cancelled: don't swallow it
        else:
            out[ex_id] = ExchangePrices(prices=res)
    return out
