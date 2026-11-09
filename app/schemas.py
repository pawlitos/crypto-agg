from pydantic import BaseModel, Field


class ExchangePrices(BaseModel):
    """Latest known prices from one exchange, plus the error from the latest attempt, if any."""

    prices: dict[str, float | None] = Field(
        default_factory=dict,
        description=(
            "Last traded price per pair from the last successful fetch; null if the exchange "
            "doesn't list the pair. Kept (possibly stale) when a later fetch fails."
        ),
    )
    updated_at: int | None = Field(
        default=None,
        description="Unix timestamp (seconds) of the last successful fetch; null until the first one succeeds.",
    )
    error: str | None = Field(
        default=None,
        exclude_if=lambda v: v is None,
        description="Error from the latest fetch attempt; omitted when it succeeded.",
    )


class PricesResponse(BaseModel):
    """Latest prices from every exchange."""

    exchanges: dict[str, ExchangePrices] = Field(
        description="Prices keyed by exchange id.",
        examples=[
            {
                "kraken": {
                    "prices": {"BTC/USDC": 74191.0, "ETH/USDC": 2106.21, "SOL/USDC": 86.22},
                    "updated_at": 1793966405,
                },
                "okx": {
                    "prices": {"BTC/USDC": 74222.9, "ETH/USDC": 2107.63, "SOL/USDC": 86.23},
                    "updated_at": 1793966390,
                    "error": "RequestTimeout: okx GET https://www.okx.com/api/v5/market/tickers",
                },
                "bybit": {
                    "prices": {},
                    "error": "ExchangeNotAvailable: bybit GET https://api.bybit.com/v5/market/instruments-info",
                },
            }
        ],
    )


class ExchangePairPrice(BaseModel):
    """Latest known price of one pair on one exchange."""

    exchange: str = Field(description="Exchange id.")
    price: float | None = Field(
        default=None,
        description=(
            "Last traded price from the last successful fetch; null if the exchange doesn't list the pair "
            "or hasn't been fetched yet. Kept (possibly stale) when a later fetch fails."
        ),
    )
    updated_at: int | None = Field(
        default=None,
        description="Unix timestamp (seconds) of the last successful fetch; null until the first one succeeds.",
    )
    error: str | None = Field(
        default=None,
        exclude_if=lambda v: v is None,
        description="Error from the latest fetch attempt; omitted when it succeeded.",
    )


class PairPricesResponse(BaseModel):
    """Latest price of one pair on every exchange."""

    pair: str = Field(description="Pair symbol.", examples=["BTC/USDC"])
    prices: list[ExchangePairPrice] = Field(
        description="One entry per exchange.",
        examples=[
            [
                {"exchange": "kraken", "price": 74191.0, "updated_at": 1793966405},
                {
                    "exchange": "okx",
                    "price": 74222.9,
                    "updated_at": 1793966390,
                    "error": "RequestTimeout: okx GET https://www.okx.com/api/v5/market/tickers",
                },
                {
                    "exchange": "bybit",
                    "error": "ExchangeNotAvailable: bybit GET https://api.bybit.com/v5/market/instruments-info",
                },
            ]
        ],
    )
