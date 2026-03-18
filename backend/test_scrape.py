import asyncio
import sys
import io
import json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')

from app.scrapers.blinkit_scraper import BlinkitScraper
from app.scrapers.instamart_scraper import InstamartScraper

async def test_scrape():
    blinkit = BlinkitScraper()
    instamart = InstamartScraper()
    
    print("Testing Blinkit scraper...")
    try:
        blinkit_products = await blinkit.search(item="milk", pincode="411001")
        print(f"Blinkit: Got {len(blinkit_products)} products")
        for p in blinkit_products[:5]:
            print(f"  - {p.name[:50]}: Rs.{p.price}")
    except Exception as e:
        import traceback
        print(f"Blinkit error: {e}")
        traceback.print_exc()
    
    print("\n--- Trying Swiggy restaurant search instead ---")
    try:
        import httpx
        client = httpx.AsyncClient(timeout=15.0, follow_redirects=True)
        # Try Swiggy general search API
        response = await client.get(
            "https://www.swiggy.com/dapi/search/index",
            params={"lat": "18.5204", "lng": "73.8567", "str": "milk"},
            headers={
                "Referer": "https://www.swiggy.com/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Keys: {list(data.keys())}")
        await client.aclose()
    except Exception as e:
        import traceback
        print(f"Swiggy search error: {e}")
        traceback.print_exc()

    print("\n--- Testing Instamart with Playwright ---")
    try:
        instamart_products = await instamart.search(item="milk", pincode="411001")
        print(f"Instamart: Got {len(instamart_products)} products")
        for p in instamart_products[:5]:
            print(f"  - {p.name[:50]}: Rs.{p.price}")
    except Exception as e:
        import traceback
        print(f"Instamart error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_scrape())