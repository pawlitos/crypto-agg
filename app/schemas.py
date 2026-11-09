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
                    "prices": {"BTC/USDT": 78150.5, "ETH/USDC": None},
                    "updated_at": 1793966405,
                },
                "okx": {
                    "prices": {"BTC/USDT": 78149.9},
                    "updated_at": 1793966390,
                    "error": "RequestTimeout: okx GET https://www.okx.com/api/v5/market/tickers",
                },
                "bybit": {
                    "prices": {},
                    "updated_at": None,
                    "error": "ExchangeNotAvailable: bybit GET https://api.bybit.com/v5/market/instruments-info",
                },
            }
        ],
    )
