from typing import Annotated
from pydantic import BaseModel, Field


class ExchangePrices(BaseModel):
    """Prices from one exchange, or the error that stopped us getting them."""

    prices: dict[str, float | None] = Field(
        default_factory=dict,
        description="Last traded price per pair; null if the exchange doesn't list the pair.",
        examples=[{"BTC/USDT": 78150.5, "ETH/USDC": None}],
    )
    error: str | None = Field(
        default=None,
        exclude_if=lambda v: v is None,
        description="Error message if fetching from this exchange failed; omitted on success.",
    )


PricesResponse = Annotated[
    dict[str, ExchangePrices],
    Field(
        description="Prices keyed by exchange id.",
        examples=[
            {
                "kraken": {"prices": {"BTC/USDT": 78150.5, "ETH/USDC": None}},
                "okx": {"prices": {}, "error": "RequestTimeout: okx GET https://www.okx.com/api/v5/market/tickers"},
            }
        ],
    ),
]
