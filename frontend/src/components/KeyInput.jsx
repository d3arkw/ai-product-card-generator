import { useState } from "react";

const KEY_LINKS = {
  openai: "https://platform.openai.com/api-keys",
  gemini: "https://aistudio.google.com/apikey",
  routerai: "https://routerai.ru",
};

export default function KeyInput({ provider, value, onChange }) {
  const [visible, setVisible] = useState(false);
  return (
    <div>
      <p className="mb-2 text-sm font-medium text-text-primary">API-ключ</p>
      <div className="flex gap-2">
        <input
          type={visible ? "text" : "password"}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Вставьте ключ"
          autoComplete="off"
          className="min-w-0 flex-1 rounded-lg border border-border bg-surface px-3 py-2.5 text-sm outline-none placeholder:text-text-secondary focus:border-brand-secondary"
        />
        <button
          type="button"
          onClick={() => setVisible((prev) => !prev)}
          className="shrink-0 rounded-lg border border-border bg-surface px-3 text-sm text-text-secondary transition-colors hover:border-brand-secondary hover:text-text-primary"
        >
          {visible ? "Скрыть" : "Показать"}
        </button>
      </div>
      <p className="mt-2 text-xs leading-relaxed text-text-secondary">
        Ключ используется только для этого запроса и нигде не сохраняется.{" "}
        <a
          href={KEY_LINKS[provider]}
          target="_blank"
          rel="noreferrer"
          className="text-brand-secondary underline underline-offset-2 hover:text-brand-primary"
        >
          Получить ключ
        </a>
      </p>
    </div>
  );
}
