from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class ExchangePrices(BaseModel):
    """Latest known prices from one exchange, plus the error from the latest attempt, if any."""

    prices: dict[str, float | None] = Field(
        default_factory=dict,
        description=(
            "Last traded price per pair from the last successful fetch; null if the exchange "
            "doesn't list the pair. Kept (possibly stale) when a later fetch fails."
        ),
        examples=[{"BTC/USDT": 78150.5, "ETH/USDC": None}],
    )
    updated_at: datetime | None = Field(
        default=None,
        description="UTC time of the last successful fetch; null until the first one succeeds.",
    )
    error: str | None = Field(
        default=None,
        exclude_if=lambda v: v is None,
        description="Error from the latest fetch attempt; omitted when it succeeded.",
    )


PricesResponse = Annotated[
    dict[str, ExchangePrices],
    Field(
        description="Prices keyed by exchange id.",
        examples=[
            {
                "kraken": {
                    "prices": {"BTC/USDT": 78150.5, "ETH/USDC": None},
                    "updated_at": "2026-11-06T12:00:05Z",
                },
                "okx": {
                    "prices": {"BTC/USDT": 78149.9},
                    "updated_at": "2026-11-06T11:59:50Z",
                    "error": "RequestTimeout: okx GET https://www.okx.com/api/v5/market/tickers",
                },
            }
        ],
    ),
]
