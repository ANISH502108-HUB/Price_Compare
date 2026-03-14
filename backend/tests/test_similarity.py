from app.models import Product
from app.services.similarity import group_products, tokenize_name


def test_tokenize_name_splits_tokens():
    tokens = tokenize_name("Amul Taaza Toned Milk 500ml")

    assert {"amul", "taaza", "toned", "milk", "500ml"}.issubset(tokens)


def test_group_products_groups_similar_names():
    products = [
        Product(platform="blinkit", name="Amul Milk 500ml", price=28, url="https://blinkit.example/a"),
        Product(platform="instamart", name="Amul Taaza Milk 500ml", price=27, url="https://instamart.example/b"),
        Product(platform="blinkit", name="Brown Bread", price=40, url="https://blinkit.example/c"),
    ]

    groups = group_products(products)

    assert len(groups) == 2
    assert len(groups[0].offers) == 2
    assert {offer.platform for offer in groups[0].offers} == {"blinkit", "instamart"}
