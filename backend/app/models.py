from __future__ import annotations

from pydantic import BaseModel, Field


class Product(BaseModel):
    platform: str
    name: str
    price: float
    url: str


class ProductGroup(BaseModel):
    group_id: str
    canonical_name: str
    tokens: list[str] = Field(default_factory=list)
    offers: list[Product] = Field(default_factory=list)
    cheapest_offer: Product | None = None


class PlatformResult(BaseModel):
    platform: str
    success: bool
    products: list[Product] = Field(default_factory=list)
    fallback_used: bool = False
    error: str | None = None
