# AI-ассистент товарных карточек

![Python 3.14](https://img.shields.io/badge/Python-3.14-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![React 19](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)
![Tailwind 4](https://img.shields.io/badge/Tailwind-4-38BDF8?style=flat-square&logo=tailwindcss&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/pytest-65_passed-4CAF50?style=flat-square&logo=pytest&logoColor=white)

Веб-приложение для B2B-каталога КИП: принимает данные о товаре (форма или JSON),
передаёт их выбранной LLM и возвращает структурированный черновик карточки —
SEO-заголовок, SEO-описание, характеристики, поисковые запросы, commercial-блок
и список недостающих данных. Результат копируется как JSON, Markdown или текст.

## Возможности

- Три LLM-провайдера на выбор: OpenAI, Google Gemini, RouterAI.
- BYOK: пользователь вводит свой API-ключ, ключ живёт только в рамках запроса.
- Строгий structured output (Pydantic + нативный JSON-режим провайдеров).
- Проверка provenance: значения характеристик должны подтверждаться входными данными.
- Защита от prompt-инъекций: маркеры данных + семантическая перепроверка.
- Лимиты: SEO-заголовок ≤ 70 символов, SEO-описание 800–1200 символов, запросы 3–5 шт.
- Состояния интерфейса: пустое, загрузка, результат, ошибка; адаптив 390px / 1280px.

## Стек

Backend: Python 3.14, FastAPI 0.141.1, Pydantic 2.13.5, openai 3.42.1, google-genai 2.34.0.
Тесты: pytest 9.2.0, ruff 0.17.3. Frontend: React 19.3.1, Vite 7.3.7, Tailwind CSS 4.3.3.

## Архитектура

```
backend/app/
  main.py            # FastAPI: POST /api/v1/generate, GET /health, CORS, единый JSON-конверт ошибок
  config.py          # настройки: модели, таймауты, лимиты ретраев
  deps.py            # реестр провайдеров (Strategy)
  exceptions.py      # AppError -> {ok:false, error:{code,message}} без технических деталей
  schemas/           # GenerateRequest (вход), ProductCard (строгая схема результата)
  services/          # generate_card: вызов -> валидация -> repair/provenance-ретраи
  providers/         # BaseLLMProvider; openai, gemini, routerai (OpenAI-совместимый)
  prompts/           # product_card.txt: системный промпт отдельно от кода
frontend/src/
  App.jsx            # поток: провайдер -> ключ -> товар (форма/JSON) -> генерация -> результат
  api/client.js      # POST /api/v1/generate, AbortController 180 c
  components/        # ProviderSelect, KeyInput, ProductForm, RawJsonInput, ResultCard, ErrorBanner
```

Поток: UI собирает `{provider, api_key, product}` → backend выбирает провайдера
по имени, вызывает LLM со схемой `ProductCard`, валидирует ответ, при невалиде
или неподтверждённых значениях повторяет с уточняющей подсказкой
(`max_repair_retries + 1` попыток), возвращает `{ok:true, data}` либо
`{ok:false, error}`.

Ключевые решения:

- Общая абстракция `BaseLLMProvider`: бизнес-логика не знает SDK провайдеров,
  RouterAI переиспользует OpenAI-совместимый класс (тот же контракт, свой
  `base_url`, модель `inclusionai/ling-3.0-flash`, таймаут 180 с вместо 60 с —
  шлюз отвечает медленно в режиме строгой схемы).
- Ключ передаётся `SecretStr`, существует только в контексте запроса: нет БД,
  нет localStorage, нет логов, параллельные запросы изолированы (покрыто тестами).
- Промпт лежит в `prompts/product_card.txt` и правится без изменения кода.

## Быстрый старт через Docker

Сначала скопируйте репозиторий:

```bash
git clone https://github.com/d3arkw/ai-product-card-generator.git
cd ai-product-card-generator
```

Дальше Docker Compose соберёт и поднимет оба сервиса:

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000 (`/health`, `POST /api/v1/generate`)

По умолчанию frontend собран с относительным API-адресом и обращается к backend
через встроенный прокси nginx (`/api/` → `backend:8000`), поэтому работает
на любом хосте без пересборки. Чтобы указать внешний backend напрямую:

```bash
VITE_API_URL=http://<host>:8000 docker compose up --build
```

Остановка: `docker compose down`. Ключи ни в образы, ни в compose-файл
не записываются — вводятся в интерфейсе при каждом запросе.

## Установка и запуск без Docker

Понадобятся Python 3.14+, Node.js 22+ и git. Четыре шага:

**0. Скопируйте репозиторий:**

```bash
git clone https://github.com/d3arkw/ai-product-card-generator.git
cd ai-product-card-generator
```

**1. Backend** — создать окружение и поставить зависимости:

```bash
cd backend
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

**2. Frontend** — поставить зависимости:

```bash
cd frontend
npm install
```

**3. Запуск** — в двух окнах терминала:

```bash
cd backend && ../.venv/bin/uvicorn app.main:app --port 8000   # http://127.0.0.1:8000
cd frontend && npm run dev -- --port 5173 --host 127.0.0.1    # http://127.0.0.1:5173
```

Файл `.env` не нужен: backend работает без него, секреты только пользовательские
и только в запросах. Все значения ниже уже заданы по умолчанию и меняются
без правок кода (см. `backend/.env.example`):

| Провайдер | Эконом                  | Стандарт           | Максимум             |
| --------- | ----------------------- | ------------------ | -------------------- |
| OpenAI    | `gpt-5.4-mini`          | `gpt-5.4`          | `gpt-5.4-pro`        |
| Gemini    | `gemini-3.5-flash-lite` | `gemini-3.6-flash` | `gemini-3.8-flash`   |
| RouterAI  | `ling-3.0-flash`        | `qwen3.7-flash`    | `minimax-m3.1-flash` |

Тир выбирается в интерфейсе (уровень + точный id модели видны сразу),
в запрос уходит `model_tier`. Список моделей отдаёт `GET /api/v1/models`,
поэтому frontend всегда показывает актуальные id.

Проверка: `curl http://127.0.0.1:8000/health` → `{"status":"up"}`.

## API-ключи

Ключ вводится в интерфейсе и нигде не сохраняется. Где получить:

- OpenAI: https://platform.openai.com/api-keys
- Google Gemini: https://aistudio.google.com/apikey
- RouterAI: личный кабинет на https://routerai.ru

## Использование

1. Выберите провайдера и вставьте API-ключ.
2. Заполните форму (название обязательно) или вставьте JSON товара.
3. Нажмите «Сгенерировать карточку» и дождитесь результата.
4. Скопируйте всю карточку как JSON / Markdown / текст либо отдельные поля.

Пример запроса:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/generate \
  -H 'Content-Type: application/json' \
  -d '{"provider":"routerai","api_key":"ВАШ_КЛЮЧ","product":{"name":"Манометр показывающий DM 02","specs":{"диапазон измерений":"0–1,6 МПа"}}}'
```

Ответ при успехе: `{"ok":true,"data":{...}}`; при ошибке:
`{"ok":false,"error":{"code":"invalid_api_key","message":"..."}}`.
Если данных мало, модель вернёт частичный результат и перечислит
недостающее в `missing_data`, а неподтверждённые значения заменит
на «данных нет».

## Примеры результатов

Два товара из ТЗ прогнаны через RouterAI (тир `cheap`,
`inclusionai/ling-3.0-flash`); вход и полный выход сохранены в `docs/examples/`:

| Товар                        | SEO-заголовок                                      | missing_data                                               |
| ---------------------------- | -------------------------------------------------- | ---------------------------------------------------------- |
| Манометр DM 02, Манотомь     | Манометр показывающий DM 02 диапазон 0–1,6 МПа     | Тип измеряемой величины                                    |
| Термометр ТБ-63, Теплоприбор | Термометр биметаллический ТБ-63, диапазон 0–120 °C | точность, присоединение, масса прибора, диаметр циферблата |

- Вход: `backend/examples/product_manometer.json`,
  `backend/examples/product_thermometer.json`.
- Выход: `docs/examples/product_manometer.md`,
  `docs/examples/product_thermometer.md` (полный JSON + краткая сводка).

## Дизайн

Интерфейс построен на фирменной палитре: лаймовый `#EFFBBB` + бордо `#722F37`
(«Premium / Modern Technology»).
Все 19 токенов (`brand-*`, `surface-*`, `text-*`, `interactive-*`, статусные)
заданы в Tailwind v4 через `@theme` в `frontend/src/styles/index.css`
и используются как утилиты (`bg-brand-primary`, `text-text-secondary`).
Адаптив: мобильная колонка 390px и двухколоночный десктоп 1280px.

## Тесты

```bash
cd backend
../.venv/bin/ruff check app tests
../.venv/bin/python -m pytest tests
```

65 тестов, все с моками внешних API — платные вызовы в наборе не выполняются.
Покрыты: входная валидация, схема результата, лимиты полей, ретраи при
невалидном JSON, выдуманные значения, `missing_data`, ошибки OpenAI/Gemini/
RouterAI, отсутствие ключа в ответах, изоляция ключей. Сборка frontend:
`cd frontend && npm run build`.

## Соответствие исходному заданию

| Пункт ТЗ                                | Как выполнено                                                                                                        |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Принимать данные JSON через веб-форму   | Форма (название, производитель, характеристики, описание) + режим вставки сырого JSON; примеры в `backend/examples/` |
| Передавать в выбранную LLM через API    | Три провайдера на выбор: OpenAI, Gemini, RouterAI                                                                    |
| Формировать черновик карточки           | Структурированный результат по Pydantic-схеме `ProductCard`                                                          |
| Возвращать JSON и текст для копирования | Копирование всей карточки как JSON / Markdown / текст + кнопки копирования каждого поля                              |
| Сообщать о недостающих данных           | Поле `missing_data` + жёлтый блок «Не хватает данных» в UI                                                           |
| SEO-заголовок до 70 символов            | Валидация + счётчик `N/70` в интерфейсе                                                                              |
| SEO-описание 800–1200 символов          | Валидация + счётчик символов                                                                                         |
| Список ключевых характеристик           | Таблица характеристик, неподтверждённые помечаются «данных нет»                                                      |
| 3–5 поисковых запросов                  | Валидация количества, отображение пилюлями                                                                           |
| Commercial-блок                         | Отдельная секция результата                                                                                          |
| Ключ не в коде                          | BYOK: ключ вводится в UI, живёт только в запросе, нигде не хранится                                                  |
| Обработка ошибок API                    | Понятные сообщения: неверный ключ, лимиты, таймаут, недоступность, невалидный ответ                                  |
| Валидный JSON                           | Нативный structured output провайдеров + серверная валидация + ретраи                                                |

## Что сделано сверх задания

- **Третий провайдер — RouterAI** (`inclusionai/ling-3.0-flash`): в разы дешевле
  OpenAI для тестовых прогонов, подключается тем же контрактом через
  OpenAI-совместимый класс. Под медленный шлюз поднят отдельный таймаут
  (backend 180 с, frontend 3 мин) — замерено на реальной модели.
- **Анти-выдумывание**: provenance-проверка не даёт модели приписать товару
  чужие характеристики — нет подтверждения в данных, значит «данных нет»
  и пункт в `missing_data`. Покрыто тестами, включая сценарий исчерпанных ретраев.
- **Repair-ретраи**: невалидный ответ не возвращается пользователю — сервис
  переспрашивает модель с указанием конкретных ошибок валидации.
- **Защита от инъекций**: входные данные wrapped в маркеры, инструкции внутри
  описания товара игнорируются; семантическая перепроверка значений.
- **UX как продукт**: скелетон загрузки, пустое состояние, баннеры ошибок,
  счётчики лимитов, три провайдера в один клик, адаптив 390px/1280px.
- **65 тестов + ruff**, все внешние API замоканы; отдельно проверен реальный
  прогон через RouterAI и запуск с нуля (чистый venv, `npm ci`).
- **Docker**: `Dockerfile` backend/frontend (nginx) и `docker-compose.yml`
  с healthcheck — демо поднимается одной командой.

## Известные ограничения

- Генерация через RouterAI занимает около минуты (строгая JSON-схема на шлюзе),
  таймауты: backend 180 с, frontend 3 мин, показан скелетон загрузки.
- Качество карточки зависит от полноты входных данных и выбранной модели.
