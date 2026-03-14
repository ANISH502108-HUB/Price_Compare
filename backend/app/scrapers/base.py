from __future__ import annotations

import asyncio
import re
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import urlencode

import httpx

from app.models import Product


class ScraperTransportError(RuntimeError):
    def __init__(
        self,
        *,
        platform: str,
        message: str,
        category: str,
        retryable: bool,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.platform = platform
        self.category = category
        self.retryable = retryable
        self.status_code = status_code


class BaseScraper(ABC):
    platform: str
    base_url: str
    timeout = httpx.Timeout(10.0, connect=5.0)
    max_transport_attempts = 3
    backoff_base_seconds = 0.2

    def default_headers(self) -> dict[str, str]:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-IN,en;q=0.9",
        }

    def build_search_url(self, item: str, pincode: str) -> str:
        query = urlencode({"q": item, "pincode": pincode})
        return f"{self.base_url}?{query}"

    async def bootstrap_session(self, client: httpx.AsyncClient, pincode: str) -> None:
        _ = (client, pincode)

    async def fetch_payload(
        self,
        client: httpx.AsyncClient,
        item: str,
        pincode: str,
    ) -> Any:
        url = self.build_search_url(item=item, pincode=pincode)
        return await self.fetch_json(client=client, url=url)

    async def fetch_json(
        self,
        *,
        client: httpx.AsyncClient,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        max_attempts: int | None = None,
    ) -> Any:
        attempts = max_attempts or self.max_transport_attempts
        request_headers = self.default_headers() | (headers or {})

        last_error: ScraperTransportError | None = None
        for attempt in range(1, attempts + 1):
            try:
                response = await client.get(url, params=params, headers=request_headers)
            except (httpx.ConnectError, httpx.ReadError, httpx.TimeoutException) as exc:
                last_error = ScraperTransportError(
                    platform=self.platform,
                    message=f"network error while requesting provider: {exc}",
                    category="network",
                    retryable=True,
                )
                if attempt < attempts:
                    await asyncio.sleep(self._backoff_delay(attempt))
                    continue
                raise last_error from exc

            category, retryable = self.classify_status(response.status_code)
            if category != "success":
                last_error = ScraperTransportError(
                    platform=self.platform,
                    message=(
                        f"provider request failed ({response.status_code}) "
                        f"for {self.platform}"
                    ),
                    category=category,
                    retryable=retryable,
                    status_code=response.status_code,
                )
                if retryable and attempt < attempts:
                    await asyncio.sleep(self._backoff_delay(attempt))
                    continue
                raise last_error

            try:
                return response.json()
            except ValueError as exc:
                raise ScraperTransportError(
                    platform=self.platform,
                    message="provider returned malformed JSON payload",
                    category="invalid_payload",
                    retryable=False,
                    status_code=response.status_code,
                ) from exc

        if last_error is not None:
            raise last_error
        raise ScraperTransportError(
            platform=self.platform,
            message="provider request failed",
            category="unknown",
            retryable=False,
        )

    async def fetch_text(
        self,
        *,
        client: httpx.AsyncClient,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        max_attempts: int | None = None,
    ) -> str:
        attempts = max_attempts or self.max_transport_attempts
        request_headers = self.default_headers() | (headers or {})

        last_error: ScraperTransportError | None = None
        for attempt in range(1, attempts + 1):
            try:
                response = await client.get(url, params=params, headers=request_headers)
            except (httpx.ConnectError, httpx.ReadError, httpx.TimeoutException) as exc:
                last_error = ScraperTransportError(
                    platform=self.platform,
                    message=f"network error while requesting provider: {exc}",
                    category="network",
                    retryable=True,
                )
                if attempt < attempts:
                    await asyncio.sleep(self._backoff_delay(attempt))
                    continue
                raise last_error from exc

            category, retryable = self.classify_status(response.status_code)
            if category != "success":
                last_error = ScraperTransportError(
                    platform=self.platform,
                    message=(
                        f"provider request failed ({response.status_code}) "
                        f"for {self.platform}"
                    ),
                    category=category,
                    retryable=retryable,
                    status_code=response.status_code,
                )
                if retryable and attempt < attempts:
                    await asyncio.sleep(self._backoff_delay(attempt))
                    continue
                raise last_error

            return response.text

        if last_error is not None:
            raise last_error
        raise ScraperTransportError(
            platform=self.platform,
            message="provider request failed",
            category="unknown",
            retryable=False,
        )

    async def warmup_request(
        self,
        *,
        client: httpx.AsyncClient,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        request_headers = self.default_headers() | (headers or {})
        try:
            await client.get(url, params=params, headers=request_headers)
        except httpx.HTTPError:
            return

    @abstractmethod
    def parse_products(self, payload: Any, item: str) -> list[dict]:
        raise NotImplementedError

    async def search(self, item: str, pincode: str) -> list[Product]:
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            await self.bootstrap_session(client=client, pincode=pincode)
            payload = await self.fetch_payload(client=client, item=item, pincode=pincode)
        parsed = self.parse_products(payload=payload, item=item)
        normalized = [self.normalize_product(raw) for raw in parsed]
        return [product for product in normalized if product is not None]

    def normalize_product(self, raw: dict) -> Product | None:
        name = str(raw.get("name", "")).strip()
        url = str(raw.get("url", "")).strip()
        if not name:
            return None

        if not url:
            url = ""

        price_raw = str(raw.get("price", "")).strip()
        price = self.parse_price(price_raw)
        if price is None:
            return None

        return Product(platform=self.platform, name=name, price=price, url=url)

    @staticmethod
    def parse_price(value: str) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)

        cleaned = re.sub(r"[^0-9.]", "", str(value))
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None

    @staticmethod
    def classify_status(status_code: int) -> tuple[str, bool]:
        if 200 <= status_code < 300:
            return "success", False
        if status_code == 403:
            return "blocked", False
        if status_code == 429:
            return "rate_limited", True
        if status_code in {408, 425}:
            return "timeout", True
        if 500 <= status_code < 600:
            return "server_error", True
        if status_code in {401, 404}:
            return "provider_contract", False
        return "http_error", False

    def _backoff_delay(self, attempt: int) -> float:
        return min(self.backoff_base_seconds * (2 ** (attempt - 1)), 1.5)
