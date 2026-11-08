import asyncio
from datetime import UTC, datetime
from typing import ClassVar

import ccxt.async_support as ccxt

from app.exchanges import EXCHANGES, fetch_one
from app.schemas import ExchangePrices
from app.timing import logger


class Collector:
    """Polls every exchange in the background and keeps the latest prices in memory."""

    REFRESH_SECONDS: ClassVar[int] = 5

    def __init__(self) -> None:
        """Create one client per exchange (reused for the app's lifetime) and empty state; nothing runs yet."""
        self.exchanges: dict[str, ccxt.Exchange] = {ex_id: getattr(ccxt, ex_id)() for ex_id in EXCHANGES}
        self.state: dict[str, ExchangePrices] = {ex_id: ExchangePrices() for ex_id in EXCHANGES}
        self.tasks: list[asyncio.Task[None]] = []

    def snapshot(self) -> dict[str, ExchangePrices]:
        """Current prices keyed by exchange id."""
        return dict(self.state)  # models are replaced, never mutated, so a shallow copy is safe

    async def poll(self, ex_id: str, exchange: ccxt.Exchange) -> None:
        """Refresh one exchange's prices every REFRESH_SECONDS until cancelled.

        On failure the previous prices are kept and only the error is recorded.
        """
        while True:
            try:
                prices = await fetch_one(exchange)
                self.state[ex_id] = ExchangePrices(prices=prices, updated_at=datetime.now(UTC))
            except Exception as e:  # noqa: BLE001 - one failing exchange must not kill the loop; CancelledError still propagates
                prev = self.state[ex_id]
                self.state[ex_id] = prev.model_copy(update={"error": f"{type(e).__name__}: {e}"})
                logger.warning("collector: %s fetch failed: %s", ex_id, e)
            await asyncio.sleep(self.REFRESH_SECONDS)

    def start(self) -> None:
        """Start one background polling task per exchange and return immediately."""
        self.tasks = [
            asyncio.create_task(self.poll(ex_id, exchange), name=f"collector:{ex_id}")
            for ex_id, exchange in self.exchanges.items()
        ]
        logger.info("collector: polling %s every %ss", ", ".join(EXCHANGES), self.REFRESH_SECONDS)

    async def stop(self) -> None:
        """Cancel the polling tasks, wait for them to finish, then close the exchange clients."""
        for t in self.tasks:
            t.cancel()
        # return_exceptions=True returns each cancelled task's CancelledError instead of raising it,
        # so no suppress(CancelledError) is needed, and a cancellation of stop() itself still propagates.
        await asyncio.gather(*self.tasks, return_exceptions=True)
        await asyncio.gather(*(ex.close() for ex in self.exchanges.values()), return_exceptions=True)
        self.tasks.clear()
