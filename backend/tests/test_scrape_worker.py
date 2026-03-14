import asyncio

import pytest

from app.models import Product
from app.scrapers.base import BaseScraper
from app.workers.scrape_worker import run_scraper_worker


class FlakyScraper(BaseScraper):
    platform = "blinkit"
    base_url = "https://example.com"

    def __init__(self) -> None:
        self.calls = 0

    def parse_products(self, html: str, item: str) -> list[dict]:
        return []

    async def search(self, item: str, pincode: str):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("temporary failure")
        return [
            Product(
                platform="blinkit",
                name="Amul Milk 500ml",
                price=28,
                url="https://example.com/item",
            )
        ]


class AlwaysFailScraper(BaseScraper):
    platform = "instamart"
    base_url = "https://example.com"

    def parse_products(self, html: str, item: str) -> list[dict]:
        return []

    async def search(self, item: str, pincode: str):
        raise RuntimeError("permanent failure")


@pytest.mark.asyncio
async def test_worker_retries_once_then_succeeds():
    queue: asyncio.Queue[dict] = asyncio.Queue()
    scraper = FlakyScraper()

    await run_scraper_worker(scraper, item="milk", pincode="411001", queue=queue)

    first = await queue.get()
    second = await queue.get()

    assert scraper.calls == 2
    assert first["type"] == "platform_results"
    assert first["platform"] == "blinkit"
    assert len(first["products"]) == 1
    assert second == {"type": "platform_done", "platform": "blinkit"}


@pytest.mark.asyncio
async def test_worker_returns_error_after_retry_failure():
    queue: asyncio.Queue[dict] = asyncio.Queue()
    scraper = AlwaysFailScraper()

    await run_scraper_worker(scraper, item="milk", pincode="411001", queue=queue)

    first = await queue.get()
    second = await queue.get()

    assert first["type"] == "platform_error"
    assert first["platform"] == "instamart"
    assert "permanent failure" in first["error"]
    assert second == {"type": "platform_done", "platform": "instamart"}
