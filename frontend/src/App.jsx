import { useMemo, useState } from "react";
import { generateCard } from "./api/client.js";
import ProviderSelect from "./components/ProviderSelect.jsx";
import KeyInput from "./components/KeyInput.jsx";
import ProductForm from "./components/ProductForm.jsx";
import RawJsonInput from "./components/RawJsonInput.jsx";
import ResultCard from "./components/ResultCard.jsx";
import ErrorBanner from "./components/ErrorBanner.jsx";

const EXAMPLE_JSON = `{
  "name": "Манометр показывающий DM 02",
  "manufacturer": "Манотомь",
  "specs": {
    "диапазон измерений": "0–1,6 МПа",
    "класс точности": "1,5"
  },
  "description": "Прибор предназначен для измерения избыточного давления."
}`;

function CardTitle({ children }) {
  return (
    <h2 className="flex items-center gap-2 text-base font-semibold text-text-primary">
      <span className="h-4 w-1 rounded-full bg-brand-primary" />
      {children}
    </h2>
  );
}

export default function App() {
  const [provider, setProvider] = useState("openai");
  const [apiKey, setApiKey] = useState("");
  const [mode, setMode] = useState("form");
  const [name, setName] = useState("");
  const [manufacturer, setManufacturer] = useState("");
  const [specs, setSpecs] = useState([{ key: "", value: "" }]);
  const [description, setDescription] = useState("");
  const [rawJson, setRawJson] = useState(EXAMPLE_JSON);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState(null);
  const [card, setCard] = useState(null);

  const product = useMemo(() => {
    if (mode === "raw") {
      return { parsed: safeParse(rawJson), raw: true };
    }
    const entries = specs.filter((row) => row.key.trim() !== "");
    return {
      parsed: {
        name,
        manufacturer,
        specs: Object.fromEntries(entries.map((row) => [row.key, row.value])),
        description,
      },
      raw: false,
    };
  }, [mode, rawJson, name, manufacturer, specs, description]);

  const canSubmit = useMemo(() => {
    if (status === "loading") return false;
    if (!apiKey.trim()) return false;
    if (mode === "raw") return product.parsed !== null;
    return name.trim() !== "";
  }, [status, apiKey, mode, product, name]);

  const onSubmit = async () => {
    if (!canSubmit) return;
    setStatus("loading");
    setError(null);
    setCard(null);
    try {
      const body = await generateCard({
        provider,
        apiKey: apiKey.trim(),
        product: product.parsed,
      });
      if (body.ok) {
        setCard(body.data);
        setStatus("done");
      } else {
        setError(body.error);
        setStatus("error");
      }
    } catch (err) {
      setError({ code: "network", message: err.message, details: [] });
      setStatus("error");
    }
  };

  const updateProduct = (patch) => {
    if (patch.name !== undefined) setName(patch.name);
    if (patch.manufacturer !== undefined) setManufacturer(patch.manufacturer);
    if (patch.specs !== undefined) setSpecs(patch.specs);
    if (patch.description !== undefined) setDescription(patch.description);
  };

  return (
    <div className="relative min-h-screen">
      <div aria-hidden className="app-glow pointer-events-none fixed inset-0" />
      <header className="sticky top-0 z-10 border-b border-divider bg-surface/85 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-b from-brand-primary to-brand-dark text-sm font-bold text-text-inverse shadow-md">
            AI
          </div>
          <div>
            <h1 className="text-base font-semibold text-text-primary">
              AI-ассистент товарных карточек
            </h1>
            <p className="text-xs text-text-secondary">
              Черновики карточек для B2B-каталога КИП
            </p>
          </div>
        </div>
        <div className="h-0.5 bg-gradient-to-r from-brand-light via-brand-primary to-brand-light" />
      </header>

      <main className="relative mx-auto grid max-w-6xl gap-4 px-4 py-6 lg:grid-cols-2">
        <div className="space-y-4">
          <div className="rounded-2xl border border-border bg-surface p-5 shadow-[0_10px_40px_-12px_rgba(114,47,55,0.15)]">
            <div className="space-y-4">
              <ProviderSelect value={provider} onChange={setProvider} />
              <KeyInput
                provider={provider}
                value={apiKey}
                onChange={setApiKey}
              />
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-surface p-5 shadow-[0_10px_40px_-12px_rgba(114,47,55,0.15)]">
            <div className="mb-4 flex items-center justify-between">
              <CardTitle>Данные о товаре</CardTitle>
              <div className="flex gap-1 rounded-lg bg-surface-secondary p-1 text-xs">
                {[
                  ["form", "Форма"],
                  ["raw", "JSON"],
                ].map(([id, label]) => (
                  <button
                    key={id}
                    type="button"
                    onClick={() => setMode(id)}
                    className={`rounded-md px-3 py-1.5 font-medium transition-colors ${
                      mode === id
                        ? "bg-surface text-text-primary shadow-sm"
                        : "text-text-secondary hover:text-text-primary"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {mode === "form" ? (
              <ProductForm
                name={name}
                manufacturer={manufacturer}
                specs={specs}
                description={description}
                onChange={updateProduct}
              />
            ) : (
              <RawJsonInput value={rawJson} onChange={setRawJson} />
            )}
            {mode === "raw" && product.parsed === null && (
              <p className="mt-2 text-xs text-error">Некорректный JSON</p>
            )}

            <button
              type="button"
              onClick={onSubmit}
              disabled={!canSubmit}
              className="mt-4 w-full rounded-lg bg-gradient-to-b from-brand-primary to-brand-dark px-4 py-3 text-sm font-medium text-text-inverse shadow-lg transition-all hover:brightness-110 active:brightness-95 disabled:cursor-not-allowed disabled:bg-none disabled:bg-interactive-disabled disabled:shadow-none"
            >
              {status === "loading" ? "Генерация…" : "Сгенерировать карточку →"}
            </button>
            {!apiKey.trim() && (
              <p className="mt-2 text-xs text-text-secondary">
                Введите API-ключ, чтобы продолжить
              </p>
            )}
          </div>
        </div>

        <div className="space-y-4">
          {status === "loading" && (
            <div className="rounded-2xl border border-border bg-surface p-5 shadow-[0_10px_40px_-12px_rgba(114,47,55,0.15)]">
              <div className="h-5 w-1/3 animate-pulse rounded bg-surface-secondary" />
              <div className="mt-3 h-24 animate-pulse rounded bg-surface-secondary" />
              <div className="mt-3 h-10 animate-pulse rounded bg-surface-secondary" />
              <p className="mt-3 text-xs text-text-secondary">
                Модель составляет карточку…
              </p>
            </div>
          )}
          {status === "error" && <ErrorBanner error={error} />}
          {status === "done" && card && <ResultCard card={card} />}
          {status === "idle" && (
            <div className="rounded-2xl border border-dashed border-border bg-surface/70 p-8 text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-interactive-soft text-xl text-brand-primary">
                ✦
              </div>
              <p className="mt-3 text-sm font-medium text-text-primary">
                Здесь появится результат
              </p>
              <p className="mx-auto mt-1 max-w-xs text-xs leading-relaxed text-text-secondary">
                Заполните данные о товаре слева и запустите генерацию. Пустые
                состояния, загрузка и ошибки — всё предусмотрено.
              </p>
            </div>
          )}
        </div>
      </main>

      <footer className="relative mx-auto max-w-6xl px-4 pb-6 text-center text-xs text-text-secondary">
        Ключ передаётся только в запросе и нигде не хранится · OpenAI / Gemini /
        RouterAI
      </footer>
    </div>
  );
}

function safeParse(text) {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}
