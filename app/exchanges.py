from collections.abc import Awaitable, Callable
from typing import cast

import ccxt.async_support as ccxt
from ccxt.base.types import Ticker, Tickers

EXCHANGES = ["kraken", "bybit", "okx"]
PAIRS = ["BTC/USDT", "BTC/USDC", "ETH/USDT", "ETH/USDC"]


async def fetch_one(exchange: ccxt.Exchange) -> dict[str, float | None]:
    """Last price of every pair in PAIRS on one exchange; None for pairs it doesn't list or has no price for."""
    markets = await exchange.load_markets()  # cached after the first call; retries until it succeeds
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
