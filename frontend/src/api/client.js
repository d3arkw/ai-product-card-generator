const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const TIMEOUT_MS = 180000;

export async function fetchModels() {
  try {
    const response = await fetch(`${API_URL}/api/v1/models`);
    const body = await response.json();
    return body.models ?? null;
  } catch {
    return null;
  }
}

export async function generateCard({ provider, apiKey, product, modelTier }) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  let response;
  try {
    response = await fetch(`${API_URL}/api/v1/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        provider,
        api_key: apiKey,
        product,
        model_tier: modelTier,
      }),
      signal: controller.signal,
    });
  } catch (err) {
    if (err.name === "AbortError") {
      throw new Error(
        "Превышено время ожидания ответа (3 мин). Попробуйте ещё раз.",
      );
    }
    throw new Error("Сервер недоступен. Проверьте, что backend запущен.");
  } finally {
    clearTimeout(timer);
  }
  let payload;
  try {
    payload = await response.json();
  } catch {
    throw new Error(`Сервер вернул некорректный ответ (${response.status}).`);
  }
  return payload;
}
