from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.scrapers.blinkit_scraper import BlinkitScraper
    from app.scrapers.instamart_scraper import InstamartScraper

ScraperType = "BlinkitScraper | InstamartScraper"


async def run_scraper_worker(
    scraper: ScraperType,
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
            await queue.put(
                {
                    "type": "platform_error",
                    "platform": scraper.platform,
                    "error": error_message,
                }
            )
    await queue.put({"type": "platform_done", "platform": scraper.platform})
