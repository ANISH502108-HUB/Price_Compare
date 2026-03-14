from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote_plus

import httpx

from app.scrapers.base import BaseScraper


class BlinkitScraper(BaseScraper):
    platform = "blinkit"
    base_url = "https://blinkit.com/v1/search"
    bootstrap_url = "https://blinkit.com/"
    mirror_search_url = "https://r.jina.ai/http://blinkit.com/s/"

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
                "https://blinkit.com/v1/search",
                {"q": item, "pincode": pincode},
            ),
            (
                "https://blinkit.com/v1/layout/listing_widgets",
                {"q": item, "pincode": pincode, "widget_type": "search"},
            ),
        ]

        last_error: Exception | None = None
        for url, params in endpoints:
            try:
                return await self.fetch_json(
                    client=client,
                    url=url,
                    params=params,
                    headers={"Referer": "https://blinkit.com/"},
                )
            except Exception as exc:
                last_error = exc

        try:
            markdown = await self.fetch_text(
                client=client,
                url=self.mirror_search_url,
                params={"q": item, "pincode": pincode},
                headers={"Referer": "https://blinkit.com/"},
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
        name_keys = {"name", "display_name", "product_name", "title"}
        price_keys = {"price", "selling_price", "final_price", "offer_price", "mrp"}
        return bool(keys & name_keys) and bool(keys & price_keys)

    @staticmethod
    def _extract_name(node: dict[str, Any]) -> str:
        for key in ("name", "display_name", "product_name", "title"):
            value = node.get(key)
            if value:
                return str(value).strip()
        return ""

    @staticmethod
    def _extract_price(node: dict[str, Any]) -> Any:
        for key in ("price", "selling_price", "final_price", "offer_price", "mrp"):
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
            return self._absolute_url(f"/prn/{slug}")
        return ""

    @staticmethod
    def _absolute_url(url: str) -> str:
        if not url:
            return ""
        if url.startswith("http"):
            return url
        if not url.startswith("/"):
            url = f"/{url}"
        return f"https://blinkit.com{url}"

    def _parse_products_from_markdown(self, markdown: str, *, item: str) -> list[dict]:
        lines = [line.strip() for line in markdown.splitlines() if line.strip()]
        results: list[dict] = []
        seen: set[tuple[str, str]] = set()
        default_url = f"https://blinkit.com/s/?q={quote_plus(item)}"

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
            results.append({"name": name, "price": price, "url": default_url})

        return results

    @staticmethod
    def _is_rupee_price_line(value: str) -> bool:
        return bool(re.fullmatch(r"[₹\\u20b9]\s*\d+(?:\.\d+)?", value))

    @staticmethod
    def _is_noise_line(value: str) -> bool:
        lowered = value.lower()
        if not lowered:
            return True
        if lowered in {"add", "markdown content:"}:
            return True
        if lowered.startswith("title:") or lowered.startswith("url source:"):
            return True
        if lowered.startswith("![image"):
            return True
        if lowered.startswith("showing results"):
            return True
        if lowered.endswith("mins"):
            return True
        return False

    def _name_before_price(self, lines: list[str], index: int) -> str:
        for offset in (2, 1, 3, 4, 5):
            lookup_index = index - offset
            if lookup_index < 0:
                continue
            candidate = lines[lookup_index].strip()
            if self._is_noise_line(candidate):
                continue
            if self._is_rupee_price_line(candidate):
                continue
            if self._looks_like_pack_size(candidate):
                continue
            return candidate
        return ""

    @staticmethod
    def _looks_like_pack_size(value: str) -> bool:
        lowered = value.lower().strip()
        if not lowered:
            return True
        if re.fullmatch(r"\d+(?:\.\d+)?", lowered):
            return True
        return bool(
            re.fullmatch(
                r"\d+(?:\s*x\s*\d+)?\s*(ml|l|ltr|litre|litres|g|gm|kg|pack|combo)",
                lowered,
            )
        )
