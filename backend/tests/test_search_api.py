from fastapi.testclient import TestClient

from app.api import routes
from app.main import app
from app.services import search_service


def test_search_streams_sse_events(monkeypatch):
    async def fake_stream_search_events(item: str, pincode: str):
        yield search_service.to_sse("started", {"item": item, "pincode": pincode})
        yield search_service.to_sse(
            "platform_results",
            {
                "platform": "blinkit",
                "products": [
                    {
                        "platform": "blinkit",
                        "name": "Amul Milk 500ml",
                        "price": 28.0,
                        "url": "https://blinkit.example/milk",
                    }
                ],
                "groups": [],
                "partial": True,
            },
        )
        yield search_service.to_sse("platform_error", {"platform": "instamart", "error": "failed"})
        yield search_service.to_sse("completed", {"groups": [], "total_products": 1})

    monkeypatch.setattr(routes, "stream_search_events", fake_stream_search_events)

    client = TestClient(app)
    response = client.get("/search", params={"item": "milk", "pincode": "411001"})

    assert response.status_code == 200
    assert "event: started" in response.text
    assert "event: platform_results" in response.text
    assert "event: platform_error" in response.text
    assert "event: completed" in response.text


def test_search_rejects_whitespace_item(monkeypatch):
    called = False

    async def fake_stream_search_events(item: str, pincode: str):
        nonlocal called
        called = True
        yield search_service.to_sse("started", {"item": item, "pincode": pincode})

    monkeypatch.setattr(routes, "stream_search_events", fake_stream_search_events)

    client = TestClient(app)
    response = client.get("/search", params={"item": "   ", "pincode": "411001"})

    assert response.status_code == 422
    assert response.json()["detail"] == "item must not be empty"
    assert called is False


def test_search_rejects_invalid_pincode(monkeypatch):
    called = False

    async def fake_stream_search_events(item: str, pincode: str):
        nonlocal called
        called = True
        yield search_service.to_sse("started", {"item": item, "pincode": pincode})

    monkeypatch.setattr(routes, "stream_search_events", fake_stream_search_events)

    client = TestClient(app)
    response = client.get("/search", params={"item": "milk", "pincode": "abc123"})

    assert response.status_code == 422
    assert response.json()["detail"] == "pincode must be a 6-digit number"
    assert called is False
