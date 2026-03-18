from __future__ import annotations
from typing import Any
import httpx
import re
from app.scrapers.base import BaseScraper
from app.models import Product

class InstamartScraper(BaseScraper):
    platform = "instamart"
    base_url = "https://www.swiggy.com/instamart"
    mirror_search_url = "https://r.jina.ai/https://www.swiggy.com/instamart/search"

    async def fetch_payload(
        self,
        client: httpx.AsyncClient,
        item: str,
        pincode: str,
    ) -> Any:
        try:
            markdown = await self.fetch_text(
                client=client,
                url=self.mirror_search_url,
                params={"q": item, "pincode": pincode},
                headers={"Referer": "https://www.swiggy.com/instamart/"},
            )
            return {"markdown": markdown, "item": item}
        except Exception as exc:
            raise exc

    def parse_products(self, payload: Any, item: str) -> list[dict]:
        if isinstance(payload, dict) and isinstance(payload.get("markdown"), str):
            return self._parse_products_from_markdown(payload["markdown"], item=item)
        return []

    def _parse_products_from_markdown(self, markdown: str, *, item: str) -> list[dict]:
        lines = [line.strip() for line in markdown.splitlines() if line.strip()]
        results: list[dict] = []
        seen: set[tuple[str, str]] = set()
        
        # Simple extraction based on the pattern observed in Instamart fallback tests
        for index, line in enumerate(lines):
            if not self._is_rupee_price_line(line):
                continue
            
            name = self._name_before_price(lines, index)
            if not name:
                continue
            
            price = self.parse_price(line)
            if price is None:
                continue
            
            signature = (name, str(price))
            if signature in seen:
                continue
            seen.add(signature)
            results.append({"name": name, "price": price, "url": "https://www.swiggy.com/instamart/search?q=" + item})
        return results

    @staticmethod
    def _is_rupee_price_line(value: str) -> bool:
        # Regex to match prices like '24', 'Rs 24', '₹24'
        return bool(re.fullmatch(r"(?:Rs\.?\s*|₹)?\s*\d+(?:\.\d+)?", value, re.IGNORECASE))

    def _name_before_price(self, lines: list[str], index: int) -> str:
        for offset in (1, 2, 3, 4):
            lookup_index = index - offset
            if lookup_index < 0:
                continue
            candidate = lines[lookup_index].strip()
            if self._is_noise_line(candidate):
                continue
            return candidate
        return ""

    @staticmethod
    def _is_noise_line(value: str) -> bool:
        lowered = value.lower()
        # Filter out common noise lines
        if not lowered or lowered in {"add", "mins", "min", "view details", "out of stock"}:
            return True
        # Filter out numeric only or discount lines
        if re.fullmatch(r"\d+%?\s*(off|discount)?", lowered):
            return True
        # Filter out promotional headers
        if any(keyword in lowered for keyword in ["title:", "url source:", "markdown content:", "![image", "showing results", "best price"]):
            return True
        return False
