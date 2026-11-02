import { useState } from "react";
import { copyText, toMarkdown, toText } from "../utils/format.js";

function CopyButton({ text, label }) {
  const [state, setState] = useState("idle");
  const onClick = async () => {
    const ok = await copyText(text);
    setState(ok ? "done" : "failed");
    setTimeout(() => setState("idle"), 1500);
  };
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded-lg border border-border bg-surface px-2.5 py-1 text-xs text-text-secondary transition-colors hover:border-brand-secondary hover:text-text-primary"
    >
      {state === "done"
        ? "Скопировано"
        : state === "failed"
          ? "Не удалось"
          : (label ?? "Копировать")}
    </button>
  );
}

function Section({ title, hint, text, children }) {
  return (
    <section className="border-b border-divider py-4 last:border-0 last:pb-0 first:pt-0">
      <div className="mb-2 flex items-center justify-between gap-2">
        <h3 className="text-sm font-medium text-text-primary">
          {title}
          {hint && (
            <span className="ml-2 font-normal text-text-secondary">{hint}</span>
          )}
        </h3>
        <CopyButton text={text} />
      </div>
      {children}
    </section>
  );
}

export default function ResultCard({ card }) {
  const json = JSON.stringify(card, null, 2);
  return (
    <div className="min-w-0 overflow-hidden rounded-2xl border border-border bg-surface p-5 shadow-[0_10px_40px_-12px_rgba(114,47,55,0.15)]">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 text-base font-semibold text-text-primary">
          <span className="h-2 w-2 rounded-full bg-success" />
          Черновик карточки
        </h2>
        <div className="flex gap-2">
          <CopyButton text={json} label="JSON" />
          <CopyButton text={toMarkdown(card)} label="Markdown" />
          <CopyButton text={toText(card)} label="Текст" />
        </div>
      </div>

      <Section
        title="SEO-заголовок"
        hint={`${card.seo_title.length}/70`}
        text={card.seo_title}
      >
        <p className="min-w-0 break-all text-sm text-text-primary">
          {card.seo_title}
        </p>
      </Section>

      <Section
        title="SEO-описание"
        hint={`${card.seo_description.length} / 800–1200`}
        text={card.seo_description}
      >
        <p className="min-w-0 break-all text-sm leading-relaxed text-text-primary">
          {card.seo_description}
        </p>
      </Section>

      <Section
        title="Характеристики"
        text={card.characteristics
          .map((item) => `${item.name}: ${item.value}`)
          .join("\n")}
      >
        <dl className="divide-y divide-divider overflow-hidden rounded-lg border border-border">
          {card.characteristics.map((item, index) => (
            <div
              key={index}
              className="grid min-w-0 grid-cols-1 gap-0.5 bg-surface px-3 py-2 text-sm odd:bg-surface-secondary/40 sm:grid-cols-2 sm:gap-2"
            >
              <dt className="min-w-0 break-all text-text-secondary">
                {item.name}
              </dt>
              <dd
                className={
                  item.value === "данных нет"
                    ? "min-w-0 break-all text-warning"
                    : "min-w-0 break-all text-text-primary"
                }
              >
                {item.value}
              </dd>
            </div>
          ))}
        </dl>
      </Section>

      <Section title="Поисковые запросы" text={card.search_queries.join("\n")}>
        <div className="flex flex-wrap gap-2">
          {card.search_queries.map((query, index) => (
            <span
              key={index}
              className="break-all rounded-full bg-interactive-soft px-3 py-1 text-xs text-text-primary"
            >
              {query}
            </span>
          ))}
        </div>
      </Section>

      <Section title="Commercial-блок" text={card.commercial_block}>
        <p className="min-w-0 break-all text-sm leading-relaxed text-text-primary">
          {card.commercial_block}
        </p>
      </Section>

      {card.missing_data.length > 0 && (
        <div className="mt-4 rounded-lg border border-warning bg-surface p-3">
          <p className="text-sm font-medium text-warning">Не хватает данных</p>
          <ul className="mt-1 list-disc pl-5 text-xs text-text-secondary">
            {card.missing_data.map((item, index) => (
              <li key={index} className="break-all">
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
