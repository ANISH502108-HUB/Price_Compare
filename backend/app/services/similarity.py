from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.models import Product, ProductGroup


STOPWORDS = {"the", "and", "for", "with", "fresh", "best", "pack"}


def tokenize_name(name: str) -> set[str]:
    tokens = set(re.findall(r"[a-z0-9]+", name.lower()))
    return {token for token in tokens if token not in STOPWORDS and len(token) > 1}


def similarity_score(left_tokens: set[str], right_tokens: set[str]) -> float:
    if not left_tokens or not right_tokens:
        return 0.0
    intersection = left_tokens & right_tokens
    if not intersection:
        return 0.0
    union = left_tokens | right_tokens
    return len(intersection) / len(union)


@dataclass
class WorkingGroup:
    canonical_name: str
    tokens: set[str]
    offers: list[Product] = field(default_factory=list)


def group_products(products: list[Product]) -> list[ProductGroup]:
    working_groups: list[WorkingGroup] = []

    for product in products:
        product_tokens = tokenize_name(product.name)
        if not product_tokens:
            continue

        best_group: WorkingGroup | None = None
        best_score = 0.0

        for group in working_groups:
            shared_count = len(group.tokens & product_tokens)
            score = similarity_score(group.tokens, product_tokens)
            if shared_count >= 2 and score > best_score:
                best_group = group
                best_score = score

        if best_group is None or best_score < 0.3:
            working_groups.append(
                WorkingGroup(
                    canonical_name=product.name,
                    tokens=set(product_tokens),
                    offers=[product],
                )
            )
            continue

        best_group.offers.append(product)
        best_group.tokens |= product_tokens
        if len(product.name) < len(best_group.canonical_name):
            best_group.canonical_name = product.name

    final_groups: list[ProductGroup] = []
    for index, group in enumerate(working_groups, start=1):
        cheapest_offer = min(group.offers, key=lambda offer: offer.price, default=None)
        final_groups.append(
            ProductGroup(
                group_id=f"group-{index}",
                canonical_name=group.canonical_name,
                tokens=sorted(group.tokens),
                offers=group.offers,
                cheapest_offer=cheapest_offer,
            )
        )

    return final_groups
