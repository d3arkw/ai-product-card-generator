import json
import re
from pathlib import Path

from pydantic import ValidationError

from app.config import get_settings
from app.deps import get_provider
from app.exceptions import InvalidModelResponseError, ServiceUnavailableError
from app.schemas.generation import GenerateRequest, ProductCard


def system_prompt() -> str:
    rules = (Path(__file__).parent.parent / "prompts" / "product_card.txt").read_text(
        encoding="utf-8"
    )
    schema = json.dumps(ProductCard.model_json_schema(), ensure_ascii=False, indent=2)
    return f"{rules}\n\nСХЕМА ОТВЕТА (верни строго такой JSON):\n{schema}\n"


def build_user_content(payload: GenerateRequest) -> str:
    product_json = payload.product.model_dump_json(indent=2, ensure_ascii=False)
    return f"<<<ДАННЫЕ>>>\n{product_json}\n<<<КОНЕЦ ДАННЫХ>>>"


def normalize(text: str) -> str:
    text = text.lower().replace("ё", "е")
    for dash in ("–", "—", "−"):
        text = text.replace(dash, "-")
    return re.sub(r"\s+", " ", text).strip()


def tokens(text: str) -> list[str]:
    return [
        part for part in re.findall(r"[a-zа-я0-9]+(?:[.,/\-][a-zа-я0-9]+)*", text) if len(part) > 2
    ]


def provenance_problems(card: ProductCard, product_json: str) -> list[str]:
    source = normalize(product_json)
    source_compact = re.sub(r"\s+", "", source)
    source_tokens = set(tokens(source))
    problems = []
    for item in card.characteristics:
        value = normalize(item.value)
        if not value or value in _MISSING_VALUES:
            continue
        if value in source:
            continue
        squashed = re.sub(r"\s+", "", value)
        if len(squashed) > 3 and squashed in source_compact:
            continue
        item_tokens = tokens(value)
        if not item_tokens:
            continue
        known = sum(1 for part in item_tokens if part in source_tokens)
        if known / len(item_tokens) < 0.6:
            problems.append(item.name)
    return problems


_MISSING_VALUES = frozenset(
    {
        "данных нет",
        "нет данных",
        "данные отсутствуют",
        "информация отсутствует",
        "не указано",
    }
)


def repair_note(product_json: str, exc: ValidationError) -> str:
    problems = "; ".join(
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors()
    )
    return (
        f"{product_json}\n\n"
        "Предыдущий ответ не прошёл проверку. "
        f"Ошибки: {problems}. "
        "Верни только исправленный JSON, строго по схеме."
    )


def provenance_note(product_json: str, problems: list[str]) -> str:
    return (
        f"{product_json}\n\n"
        f"Значения не подтверждены исходными данными: {', '.join(problems)}. "
        "Исправь: укажи значение из данных либо поставь «данных нет» "
        "и добавь параметр в missing_data. Верни только исправленный JSON."
    )


async def generate_card(payload: GenerateRequest) -> ProductCard:
    provider = get_provider(payload.provider)
    api_key = payload.api_key.get_secret_value()
    schema = ProductCard.model_json_schema()
    product_json = payload.product.model_dump_json(indent=2, ensure_ascii=False)
    content = build_user_content(payload)
    unavailable_retried = False
    attempts = get_settings().max_repair_retries + 1
    for attempt in range(attempts):
        last = attempt + 1 >= attempts
        try:
            raw = await provider.generate_text(
                system_prompt=system_prompt(),
                user_content=content,
                api_key=api_key,
                response_schema=schema,
            )
        except ServiceUnavailableError:
            if last or unavailable_retried:
                raise
            unavailable_retried = True
            continue
        try:
            card = ProductCard.model_validate_json(raw)
        except ValidationError as exc:
            if last:
                raise InvalidModelResponseError() from exc
            content = repair_note(product_json, exc)
            continue
        problems = provenance_problems(card, product_json)
        if problems:
            if last:
                raise InvalidModelResponseError(
                    "В результате есть данные без подтверждения: " + ", ".join(problems)
                )
            content = provenance_note(product_json, problems)
            continue
        return card
