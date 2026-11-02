# AI-ассистент товарных карточек

![Python 3.14](https://img.shields.io/badge/Python-3.14-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![React 19](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)
![Tailwind 4](https://img.shields.io/badge/Tailwind-4-38BDF8?style=flat-square&logo=tailwindcss&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/pytest-65_passed-4CAF50?style=flat-square&logo=pytest&logoColor=white)

B2B-каталог КИП: принимает данные о товаре (форма или JSON), передаёт выбранной
LLM и возвращает черновик карточки — SEO-заголовок, SEO-описание, характеристики,
поисковые запросы, commercial-блок, `missing_data`. Копирование как JSON / Markdown / текст.

## Для проверяющего

| Что проверить             | Где                                                                          |
| ------------------------- | ---------------------------------------------------------------------------- |
| Живое демо                | http://localhost:5173 (после `docker compose up --build`)                    |
| Пример 1: манометр DM 02  | [docs/examples/product_manometer.md](docs/examples/product_manometer.md)     |
| Пример 2: термометр ТБ-63 | [docs/examples/product_thermometer.md](docs/examples/product_thermometer.md) |
| Входы для примеров        | [backend/examples/](backend/examples/)                                       |
| Системный промпт          | [backend/app/prompts/product_card.txt](backend/app/prompts/product_card.txt) |
| Схема результата          | [backend/app/schemas/](backend/app/schemas/)                                 |
| Соответствие пунктам ТЗ   | [таблица ниже](#соответствие-заданию)                                        |
| Ограничения и улучшения   | [раздел ниже](#ограничения-и-улучшения)                                      |

## Примеры результатов

Оба товара из ТЗ прогнаны через RouterAI (тир `cheap`, `inclusionai/ling-3.0-flash`).
В каждом файле — вход, полный выход JSON и краткая сводка.

| Товар                        | SEO-заголовок                                      | missing_data                                       | Файл                                                           |
| ---------------------------- | -------------------------------------------------- | -------------------------------------------------- | -------------------------------------------------------------- |
| Манометр DM 02, Манотомь     | Манометр показывающий DM 02 диапазон 0–1,6 МПа     | Тип измеряемой величины                            | [product_manometer.md](docs/examples/product_manometer.md)     |
| Термометр ТБ-63, Теплоприбор | Термометр биметаллический ТБ-63, диапазон 0–120 °C | точность, присоединение, масса, диаметр циферблата | [product_thermometer.md](docs/examples/product_thermometer.md) |

## Быстрый старт

```bash
git clone https://github.com/d3arkw/ai-product-card-generator.git
cd ai-product-card-generator
docker compose up --build
```

- Frontend: http://localhost:5173, backend: http://localhost:8000 (`/health`, `POST /api/v1/generate`).
- Frontend идёт через прокси nginx (`/api/` → backend), работает на любом хосте без пересборки.
- Ключи ни в образы, ни в compose не записываются — вводятся в интерфейсе.

Без Docker (Python 3.14+, Node.js 22+):

```bash
cd backend && python -m venv .venv && ../.venv/bin/pip install -r requirements.txt
cd frontend && npm install
cd backend && ../.venv/bin/uvicorn app.main:app --port 8000        # терминал 1
cd frontend && npm run dev -- --port 5173 --host 127.0.0.1          # терминал 2
```

`.env` не нужен: дефолты в коде, переопределение через env (см. [backend/.env.example](backend/.env.example)).
Проверка: `curl http://127.0.0.1:8000/health` → `{"status":"up"}`.

## Модели

Тир выбирается в интерфейсе (уровень + точный id видны сразу), в запрос уходит `model_tier`.
Актуальные id всегда отдаёт `GET /api/v1/models`.

| Провайдер | Эконом                  | Стандарт           | Максимум             |
| --------- | ----------------------- | ------------------ | -------------------- |
| OpenAI    | `gpt-5.4-mini`          | `gpt-5.4`          | `gpt-5.4-pro`        |
| Gemini    | `gemini-3.5-flash-lite` | `gemini-3.6-flash` | `gemini-3.8-flash`   |
| RouterAI  | `ling-3.0-flash`        | `qwen3.7-flash`    | `minimax-m3.1-flash` |

## Использование

1. Выберите провайдера, тир и вставьте API-ключ (ключи: [OpenAI](https://platform.openai.com/api-keys),
   [Gemini](https://aistudio.google.com/apikey), [RouterAI](https://routerai.ru)). Ключ живёт только в запросе.
2. Заполните форму или вставьте JSON товара → «Сгенерировать карточку».
3. Скопируйте результат целиком (JSON / Markdown / текст) или отдельными полями.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/generate \
  -H 'Content-Type: application/json' \
  -d '{"provider":"routerai","model_tier":"cheap","api_key":"ВАШ_КЛЮЧ","product":{"name":"Манометр показывающий DM 02"}}'
```

Успех: `{"ok":true,"data":{...}}`, ошибка: `{"ok":false,"error":{"code":"...","message":"..."}}`.

## Как это устроено

```
backend/app/
  main.py            # POST /api/v1/generate, GET /models, /health, CORS, единый конверт ошибок
  config.py          # модели по тирам, таймауты, лимиты ретраев
  providers/         # BaseLLMProvider; openai, gemini, routerai (OpenAI-совместимый класс)
  services/          # generate_card: вызов → валидация → repair/provenance-ретраи
  schemas/           # GenerateRequest, ProductCard (строгая схема результата)
  prompts/           # product_card.txt — системный промпт отдельно от кода
frontend/src/        # App.jsx, api/client.js, components/ (провайдер, тир, форма, JSON, результат)
```

Решения:

- **Провайдеры** — общая абстракция `BaseLLMProvider`, бизнес-логика не знает SDK;
  RouterAI переиспользует OpenAI-совместимый класс (свой `base_url`, таймаут 180 с — шлюз медленный в строгой схеме).
- **Промпт** ([product_card.txt](backend/app/prompts/product_card.txt)) — только JSON по схеме,
  запрет выдумывать (нет подтверждения → «данных нет» + `missing_data`), лимиты 70 / 800–1200 / 3–5.
- **Анти-выдумывание** — provenance-проверка значений против входных данных + repair-ретраи
  с указанием ошибок валидации; инъекции во входе wrapped в маркеры и игнорируются.
- **BYOK** — ключ как `SecretStr`, только в контексте запроса: нет БД, localStorage и логов.

Стек: Python 3.14, FastAPI, Pydantic, openai, google-genai; React 19, Vite, Tailwind 4.
Дизайн: палитра `#EFFBBB` + `#722F37`, токены в `@theme`, адаптив 390px / 1280px.

## Тесты

```bash
cd backend && ../.venv/bin/ruff check app tests && ../.venv/bin/python -m pytest tests
cd frontend && npm run build
```

65 тестов, внешние API замоканы. Покрыты: валидация входа, схема и лимиты результата,
ретраи, выдуманные значения, `missing_data`, ошибки всех провайдеров, отсутствие ключа
в ответах, изоляция ключей, маппинг тиров.

## Соответствие заданию

| Пункт ТЗ                     | Как выполнено                                                               |
| ---------------------------- | --------------------------------------------------------------------------- |
| Данные JSON через веб-форму  | Форма + режим сырого JSON; примеры в [backend/examples/](backend/examples/) |
| Передача в выбранную LLM     | Три провайдера + тиры, id видны в UI                                        |
| Черновик карточки            | Результат по Pydantic-схеме `ProductCard`                                   |
| JSON и текст для копирования | Копия всей карточки (JSON / Markdown / текст) + покнопочно по полям         |
| Недостающие данные           | `missing_data` + блок «Не хватает данных» в UI                              |
| SEO-заголовок ≤ 70           | Валидация + счётчик `N/70`                                                  |
| SEO-описание 800–1200        | Валидация + счётчик символов                                                |
| Ключевые характеристики      | Таблица; неподтверждённые → «данных нет»                                    |
| 3–5 поисковых запросов       | Валидация количества, пилюли в UI                                           |
| Commercial-блок              | Отдельная секция результата                                                 |
| Ключ не в коде               | BYOK: только в запросе, нигде не хранится                                   |
| Обработка ошибок API         | Понятные тексты: ключ, лимиты, таймаут, недоступность, невалидный ответ     |
| Валидный JSON                | Нативный structured output + серверная валидация + ретраи                   |

## Ограничения и улучшения

Ограничения:

- RouterAI в строгой схеме отвечает около минуты (таймауты 180 с / 3 мин, скелетон загрузки).
- Качество карточки зависит от полноты входных данных и выбранной модели.

Возможные улучшения:

- История генераций и сравнение тиров side-by-side.
- Подгрузка характеристик из каталога производителя по артикулу.
- Кэширование одинаковых запросов и стриминг частичного результата.
