from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from app.dependencies import CollectorDep
from app.exchanges import PAIRS
from app.schemas import ExchangePairPrice, PairPricesResponse, PricesResponse

router = APIRouter(prefix="/v1/prices", tags=["prices"])


@router.get("")
async def prices(collector: CollectorDep) -> PricesResponse:
    return PricesResponse(exchanges=collector.snapshot())


@router.get("/{base}/{quote}", responses={404: {"description": "Pair is not tracked."}})
async def pair_prices(
    base: Annotated[str, Path(description="Base asset, e.g. BTC (case-insensitive).")],
    quote: Annotated[str, Path(description="Quote asset, e.g. USDC (case-insensitive).")],
    collector: CollectorDep,
) -> PairPricesResponse:
    pair = f"{base}/{quote}".upper()
    if pair not in PAIRS:
        raise HTTPException(status_code=404, detail=f"Pair {pair} is not tracked.")
    return PairPricesResponse(
        pair=pair,
        prices=[
            ExchangePairPrice(exchange=ex_id, price=ex.prices.get(pair), updated_at=ex.updated_at, error=ex.error)
            for ex_id, ex in collector.snapshot().items()
        ],
    )
