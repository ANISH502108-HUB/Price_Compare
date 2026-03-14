from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote_plus

import httpx

from app.scrapers.base import BaseScraper


class InstamartScraper(BaseScraper):
    platform = "instamart"
    base_url = "https://www.swiggy.com/dapi/instamart/search"
    bootstrap_url = "https://www.swiggy.com/instamart"
    mirror_search_url = "https://r.jina.ai/http://www.swiggy.com/instamart/search"

    async def bootstrap_session(self, client: httpx.AsyncClient, pincode: str) -> None:
        await self.warmup_request(client=client, url=self.bootstrap_url, params={"pincode": pincode})

    async def fetch_payload(
        self,
        client: httpx.AsyncClient,
        item: str,
        pincode: str,
    ) -> Any:
        endpoints: list[tuple[str, dict[str, Any]]] = [
            (
                "https://www.swiggy.com/dapi/instamart/search",
                {"query": item, "pincode": pincode},
            ),
            (
                "https://www.swiggy.com/api/instamart/search",
                {"query": item, "pincode": pincode},
            ),
            (
                "https://www.swiggy.com/dapi/instamart/items/search",
                {"query": item, "pincode": pincode},
            ),
        ]

        last_error: Exception | None = None
        for url, params in endpoints:
            try:
                return await self.fetch_json(
                    client=client,
                    url=url,
                    params=params,
                    headers={"Referer": "https://www.swiggy.com/instamart"},
                )
            except Exception as exc:
                last_error = exc

        try:
            markdown = await self.fetch_text(
                client=client,
                url=self.mirror_search_url,
                params={"query": item, "pincode": pincode},
                headers={"Referer": "https://www.swiggy.com/instamart"},
            )
            return {"markdown": markdown, "item": item}
        except Exception as exc:
            last_error = exc

        if last_error is not None:
            raise last_error
        return {}

    def parse_products(self, payload: Any, item: str) -> list[dict]:
        if isinstance(payload, dict) and isinstance(payload.get("markdown"), str):
            return self._parse_products_from_markdown(payload["markdown"], item=item)

        products: list[dict] = []
        seen: set[tuple[str, str, str]] = set()

        for node in self._iter_product_nodes(payload):
            name = self._extract_name(node)
            if not name:
                continue

            price = self._extract_price(node)
            if price is None:
                continue

            url = self._extract_url(node)
            signature = (name, str(price), url)
            if signature in seen:
                continue
            seen.add(signature)
            products.append({"name": name, "price": price, "url": url})

        return products

    def _iter_product_nodes(self, value: Any):
        if isinstance(value, dict):
            keys = set(value.keys())
            if self._looks_like_product(keys):
                yield value
            for child in value.values():
                yield from self._iter_product_nodes(child)
            return
        if isinstance(value, list):
            for entry in value:
                yield from self._iter_product_nodes(entry)

    @staticmethod
    def _looks_like_product(keys: set[str]) -> bool:
        name_keys = {"name", "display_name", "product_name", "title", "item_name"}
        price_keys = {"price", "selling_price", "final_price", "offer_price", "discounted_price"}
        return bool(keys & name_keys) and bool(keys & price_keys)

    @staticmethod
    def _extract_name(node: dict[str, Any]) -> str:
        for key in ("name", "display_name", "product_name", "title", "item_name"):
            value = node.get(key)
            if value:
                return str(value).strip()
        return ""

    @staticmethod
    def _extract_price(node: dict[str, Any]) -> Any:
        for key in ("price", "selling_price", "final_price", "offer_price", "discounted_price"):
            value = node.get(key)
            if isinstance(value, dict):
                nested = value.get("value") or value.get("amount")
                if nested is not None:
                    return nested
            if value is not None:
                return value
        return None

    def _extract_url(self, node: dict[str, Any]) -> str:
        for key in ("url", "deeplink", "share_url", "product_url"):
            value = node.get(key)
            if value:
                return self._absolute_url(str(value))
        slug = node.get("slug")
        if slug:
            return self._absolute_url(f"/instamart/item/{slug}")
        return ""

    @staticmethod
    def _absolute_url(url: str) -> str:
        if not url:
            return ""
        if url.startswith("http"):
            return url
        if not url.startswith("/"):
            url = f"/{url}"
        return f"https://www.swiggy.com{url}"

    def _parse_products_from_markdown(self, markdown: str, *, item: str) -> list[dict]:
        lines = [line.strip() for line in markdown.splitlines() if line.strip()]
        results: list[dict] = []
        seen: set[tuple[str, str]] = set()
        default_url = f"https://www.swiggy.com/instamart/search?query={quote_plus(item)}"

        index = 0
        while index < len(lines):
            line = lines[index]
            image_match = re.match(r"!\[Image\s+\d+:(.*?)\]\(", line)
            if not image_match:
                index += 1
                continue

            fallback_name = image_match.group(1).strip()
            cursor = index + 1
            block_end = len(lines)
            while cursor < len(lines):
                if re.match(r"!\[Image\s+\d+:", lines[cursor]):
                    block_end = cursor
                    break
                cursor += 1

            block = lines[index:block_end]
            name = self._extract_block_name(block, fallback_name=fallback_name)
            price = self._extract_block_price(block)
            if name and price is not None:
                signature = (name, str(price))
                if signature not in seen:
                    seen.add(signature)
                    results.append({"name": name, "price": price, "url": default_url})

            index = block_end

        return results

    @staticmethod
    def _extract_block_name(block: list[str], *, fallback_name: str) -> str:
        for line in block:
            if line.lower().endswith("mins") or line.lower() == "ad":
                continue
            if line == fallback_name:
                return line
        return fallback_name

    def _extract_block_price(self, block: list[str]) -> float | None:
        for line in block:
            if re.fullmatch(r"\d+(?:\.\d+)?", line):
                return self.parse_price(line)
        return None
