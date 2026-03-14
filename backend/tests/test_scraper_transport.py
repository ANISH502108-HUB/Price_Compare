import httpx
import pytest

from app.scrapers.base import BaseScraper
from app.scrapers.base import ScraperTransportError


class DummyScraper(BaseScraper):
    platform = "dummy"
    base_url = "https://example.com/search"

    def parse_products(self, payload, item: str) -> list[dict]:
        _ = (payload, item)
        return []


@pytest.mark.asyncio
async def test_fetch_json_retries_on_rate_limit_then_succeeds():
    scraper = DummyScraper()
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(status_code=429, json={"error": "slow down"}, request=request)
        return httpx.Response(status_code=200, json={"ok": True}, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        payload = await scraper.fetch_json(client=client, url="https://example.com/api")

    assert calls["count"] == 2
    assert payload == {"ok": True}


@pytest.mark.asyncio
async def test_fetch_json_classifies_403_as_blocked_without_retry():
    scraper = DummyScraper()
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(status_code=403, json={"error": "forbidden"}, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ScraperTransportError) as captured:
            await scraper.fetch_json(client=client, url="https://example.com/api")

    assert calls["count"] == 1
    assert captured.value.category == "blocked"
    assert captured.value.retryable is False
