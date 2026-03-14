import asyncio
import json

import pytest

from app.services import search_service


def _parse_sse_chunk(chunk: str) -> tuple[str, dict]:
    lines = [line for line in chunk.strip().splitlines() if line]
    event = lines[0].replace("event: ", "", 1)
    data = json.loads(lines[1].replace("data: ", "", 1))
    return event, data


@pytest.mark.asyncio
async def test_stream_search_events_keeps_event_names_and_payload_keys(monkeypatch):
    class StubBlinkit:
        platform = "blinkit"

    class StubInstamart:
        platform = "instamart"

    async def fake_worker(scraper, item: str, pincode: str, queue: asyncio.Queue, max_attempts: int = 2):
        _ = (item, pincode, max_attempts)
        if scraper.platform == "blinkit":
            await queue.put(
                {
                    "type": "platform_results",
                    "platform": "blinkit",
                    "products": [
                        {
                            "platform": "blinkit",
                            "name": "Amul Milk 500ml",
                            "price": 28.0,
                            "url": "https://blinkit.example/milk",
                        }
                    ],
                }
            )
        else:
            await queue.put(
                {
                    "type": "platform_error",
                    "platform": "instamart",
                    "error": "provider blocked",
                }
            )
        await queue.put({"type": "platform_done", "platform": scraper.platform})

    monkeypatch.setattr(search_service, "BlinkitScraper", StubBlinkit)
    monkeypatch.setattr(search_service, "InstamartScraper", StubInstamart)
    monkeypatch.setattr(search_service, "run_scraper_worker", fake_worker)

    events = []
    async for chunk in search_service.stream_search_events(item="milk", pincode="411001"):
        events.append(_parse_sse_chunk(chunk))

    assert events[0][0] == "started"
    assert events[-1][0] == "completed"

    emitted_names = {name for name, _ in events}
    assert emitted_names == {"started", "platform_results", "platform_error", "completed"}

    started_data = events[0][1]
    assert set(started_data) == {"item", "pincode", "platforms"}

    platform_results_data = next(data for name, data in events if name == "platform_results")
    assert set(platform_results_data) == {"platform", "products", "groups", "partial"}

    platform_error_data = next(data for name, data in events if name == "platform_error")
    assert set(platform_error_data) == {"platform", "error"}

    completed_data = events[-1][1]
    assert set(completed_data) == {"item", "pincode", "status", "groups", "total_products"}
