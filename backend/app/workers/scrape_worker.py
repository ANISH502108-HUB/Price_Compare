from __future__ import annotations

import asyncio
from typing import Any

from app.scrapers.base import BaseScraper
from app.scrapers.base import ScraperTransportError


async def run_scraper_worker(
    scraper: BaseScraper,
    item: str,
    pincode: str,
    queue: asyncio.Queue[dict[str, Any]],
    max_attempts: int = 2,
) -> None:
    last_exception: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            products = await scraper.search(item=item, pincode=pincode)
            await queue.put(
                {
                    "type": "platform_results",
                    "platform": scraper.platform,
                    "products": [product.model_dump() for product in products],
                }
            )
            break
        except Exception as exc:
            last_exception = exc
            if attempt < max_attempts:
                await asyncio.sleep(0.25)
                continue

            error_message = str(last_exception)
            if isinstance(last_exception, ScraperTransportError):
                status = (
                    f" status={last_exception.status_code}"
                    if last_exception.status_code is not None
                    else ""
                )
                error_message = (
                    f"provider_error category={last_exception.category}{status}: "
                    f"{last_exception}"
                )

            await queue.put(
                {
                    "type": "platform_error",
                    "platform": scraper.platform,
                    "error": error_message,
                }
            )
    await queue.put({"type": "platform_done", "platform": scraper.platform})
