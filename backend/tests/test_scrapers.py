import pytest

from app.scrapers.blinkit_scraper import BlinkitScraper
from app.scrapers.instamart_scraper import InstamartScraper


@pytest.mark.asyncio
async def test_blinkit_scraper_outputs_normalized_products(monkeypatch):
    payload = {
        "data": {
            "items": [
                {
                    "name": "Amul Taaza Milk 500ml",
                    "price": 28,
                    "url": "/p/milk-500",
                }
            ]
        }
    }

    scraper = BlinkitScraper()

    async def fake_fetch_payload(*, client, item: str, pincode: str):
        _ = (client, item, pincode)
        return payload

    monkeypatch.setattr(scraper, "fetch_payload", fake_fetch_payload)

    products = await scraper.search(item="milk", pincode="411001")

    assert len(products) == 1
    assert products[0].platform == "blinkit"
    assert products[0].name == "Amul Taaza Milk 500ml"
    assert products[0].price == 28.0
    assert products[0].url == "https://blinkit.com/p/milk-500"


@pytest.mark.asyncio
async def test_instamart_scraper_outputs_normalized_products(monkeypatch):
    payload = {
        "data": {
            "cards": [
                {
                    "item_name": "Amul Milk 500ml",
                    "discounted_price": "Rs 27",
                    "deeplink": "/instamart/p/milk-500",
                }
            ]
        }
    }

    scraper = InstamartScraper()

    async def fake_fetch_payload(*, client, item: str, pincode: str):
        _ = (client, item, pincode)
        return payload

    monkeypatch.setattr(scraper, "fetch_payload", fake_fetch_payload)

    products = await scraper.search(item="milk", pincode="411001")

    assert len(products) == 1
    assert products[0].platform == "instamart"
    assert products[0].name == "Amul Milk 500ml"
    assert products[0].price == 27.0
    assert products[0].url == "https://www.swiggy.com/instamart/p/milk-500"


@pytest.mark.asyncio
async def test_blinkit_scraper_parses_markdown_fallback(monkeypatch):
    markdown = """
Title: Buy milk Online | blinkit
URL Source: http://blinkit.com/s/?q=milk
Markdown Content:
Showing results for "milk"
![Image 1](https://cdn.grofers.com/assets/eta-icons/15-mins.png)
13 mins
Mother Dairy Cow Milk
1 ltr
₹59
ADD
"""

    scraper = BlinkitScraper()

    async def fake_fetch_payload(*, client, item: str, pincode: str):
        _ = (client, pincode)
        return {"markdown": markdown, "item": item}

    monkeypatch.setattr(scraper, "fetch_payload", fake_fetch_payload)

    products = await scraper.search(item="milk", pincode="411001")

    assert len(products) == 1
    assert products[0].platform == "blinkit"
    assert products[0].name == "Mother Dairy Cow Milk"
    assert products[0].price == 59.0
    assert products[0].url == "https://blinkit.com/s/?q=milk"


@pytest.mark.asyncio
async def test_instamart_scraper_parses_markdown_fallback(monkeypatch):
    markdown = """
Title: Instamart
URL Source: http://www.swiggy.com/instamart/search?query=milk
Markdown Content:
Showing results for "milk"
![Image 1: Nandini Pasteurised Toned Milk](https://instamart-media-assets.swiggy.com/image.png)
6 MINS
Nandini Pasteurised Toned Milk
500 ml
24
"""

    scraper = InstamartScraper()

    async def fake_fetch_payload(*, client, item: str, pincode: str):
        _ = (client, pincode)
        return {"markdown": markdown, "item": item}

    monkeypatch.setattr(scraper, "fetch_payload", fake_fetch_payload)

    products = await scraper.search(item="milk", pincode="411001")

    assert len(products) == 1
    assert products[0].platform == "instamart"
    assert products[0].name == "Nandini Pasteurised Toned Milk"
    assert products[0].price == 24.0
    assert products[0].url == "https://www.swiggy.com/instamart/search?query=milk"
