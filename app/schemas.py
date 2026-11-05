from pydantic import BaseModel, Field, RootModel


class ExchangePrices(BaseModel):
    """Prices from one exchange, or the error that stopped us getting them."""

    prices: dict[str, float | None] = Field(
        default_factory=dict,
        description="Last traded price per pair; null if the exchange doesn't list the pair.",
        examples=[{"BTC/USDT": 78150.5, "ETH/USDC": None}],
    )
    error: str | None = Field(
        default=None,
        description="Error message if fetching from this exchange failed.",
    )


class PricesResponse(RootModel[dict[str, ExchangePrices]]):
    """Prices keyed by exchange id."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "kraken": {"prices": {"BTC/USDT": 78150.5, "ETH/USDC": None}, "error": None},
                    "okx": {"prices": {}, "error": "RequestTimeout: okx GET https://www.okx.com/api/v5/market/tickers"},
                }
            ]
        }
    }
