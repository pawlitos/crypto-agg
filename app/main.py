import asyncio
from contextlib import asynccontextmanager

import ccxt.async_support as ccxt
from fastapi import FastAPI, Request

EXCHANGES = ["kraken", "bybit", "okx"]
PAIRS = ["BTC/USDT", "BTC/USDC", "ETH/USDT", "ETH/USDC"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    clients: dict[str, ccxt.Exchange] = {}
    app.state.clients = clients
    try:
        for ex_id in EXCHANGES:
            clients[ex_id] = getattr(ccxt, ex_id)()
        await asyncio.gather(*(c.load_markets() for c in clients.values()), return_exceptions=True)
        yield
    finally:
        await asyncio.gather(*(c.close() for c in clients.values()), return_exceptions=True)
        clients.clear()


app = FastAPI(lifespan=lifespan)


async def fetch_one(exchange: ccxt.Exchange) -> dict:
    await exchange.load_markets()  # no-op if already loaded; retries if startup failed
    symbols = [p for p in PAIRS if p in exchange.markets]
    tickers = await exchange.fetch_tickers(symbols)
    return {p: tickers.get(p, {}).get("last") for p in PAIRS}


@app.get("/v1/prices")
async def prices(request: Request):
    clients = request.app.state.clients
    results = await asyncio.gather(
        *(fetch_one(clients[ex_id]) for ex_id in EXCHANGES),
        return_exceptions=True,
    )
    return {ex_id: {"error": str(res)} if isinstance(res, Exception) else res for ex_id, res in zip(EXCHANGES, results)}
