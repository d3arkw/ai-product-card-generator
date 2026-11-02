import pytest
from pydantic import ValidationError

from app.schemas.generation import ProductCard
from app.schemas.product import ProductInput


def make_description(length: int = 900) -> str:
    return "о" * length


def make_card(**overrides) -> ProductCard:
    payload = {
        "seo_title": "Манометр DM 02",
        "seo_description": make_description(),
        "characteristics": [{"name": "Диапазон", "value": "0–1,6 МПа"}],
        "search_queries": ["манометр купить", "манометр DM 02", "манометр 1,6 МПа"],
        "commercial_block": "Подходит для котельных.",
        "missing_data": [],
    }
    payload.update(overrides)
    return ProductCard(**payload)


def test_valid_card():
    assert make_card().seo_title == "Манометр DM 02"


def test_title_too_long():
    with pytest.raises(ValidationError):
        make_card(seo_title="x" * 71)


def test_description_too_short():
    with pytest.raises(ValidationError):
        make_card(seo_description=make_description(799))


def test_description_too_long():
    with pytest.raises(ValidationError):
        make_card(seo_description=make_description(1201))


def test_queries_bounds():
    with pytest.raises(ValidationError):
        make_card(search_queries=["один", "два"])
    with pytest.raises(ValidationError):
        make_card(search_queries=["1", "2", "3", "4", "5", "6"])


def test_empty_product_name_rejected():
    with pytest.raises(ValidationError):
        ProductInput(name="")


def test_whitespace_only_name_rejected():
    with pytest.raises(ValidationError):
        ProductInput(name="   ")


def test_specs_are_stripped():
    product = ProductInput(
        name="Манометр",
        specs={"  диапазон  ": "  0–1,6 МПа ", "": "мусор", "  ": "мусор"},
    )
    assert product.specs == {"диапазон": "0–1,6 МПа"}


def test_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        ProductInput(name="Манометр", unknown="x")
