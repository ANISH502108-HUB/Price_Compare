from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any

from app.models import Product
from app.scrapers import BlinkitScraper, InstamartScraper
from app.services.similarity import group_products
from app.workers.scrape_worker import run_scraper_worker


def to_sse(event: str, data: dict[str, Any]) -> str:
    payload = json.dumps(data, separators=(",", ":"))
    return f"event: {event}\ndata: {payload}\n\n"


async def stream_search_events(item: str, pincode: str) -> AsyncGenerator[str, None]:
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    scrapers = [BlinkitScraper(), InstamartScraper()]

    tasks = [
        asyncio.create_task(
            run_scraper_worker(scraper=scraper, item=item, pincode=pincode, queue=queue)
        )
        for scraper in scrapers
    ]

    completed_workers = 0
    collected_products: list[Product] = []
    platform_status: dict[str, str] = {}

    yield to_sse(
        event="started",
        data={
            "item": item,
            "pincode": pincode,
            "platforms": [scraper.platform for scraper in scrapers],
        },
    )

    while completed_workers < len(scrapers):
        message = await queue.get()
        message_type = message.get("type")

        if message_type == "platform_done":
            completed_workers += 1
            platform = str(message.get("platform", "unknown"))
            if platform not in platform_status:
                platform_status[platform] = "done"
            continue

        if message_type == "platform_error":
            platform = str(message.get("platform", "unknown"))
            platform_status[platform] = "error"
            yield to_sse(
                event="platform_error",
                data={
                    "platform": platform,
                    "error": message.get("error", "scraper failed"),
                },
            )
            continue

        if message_type == "platform_results":
            platform = str(message.get("platform", "unknown"))
            raw_products = message.get("products", [])
            parsed_products = [Product.model_validate(product) for product in raw_products]
            collected_products.extend(parsed_products)

            groups = group_products(collected_products)
            platform_status[platform] = "success"

            payload: dict[str, Any] = {
                "platform": platform,
                "products": [product.model_dump() for product in parsed_products],
                "groups": [group.model_dump() for group in groups],
                "partial": completed_workers + 1 < len(scrapers),
            }

            yield to_sse(event="platform_results", data=payload)

    await asyncio.gather(*tasks, return_exceptions=True)

    final_groups = group_products(collected_products)
    yield to_sse(
        event="completed",
        data={
            "item": item,
            "pincode": pincode,
            "status": platform_status,
            "groups": [group.model_dump() for group in final_groups],
            "total_products": len(collected_products),
        },
    )
