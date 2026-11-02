export default function ProductForm({
  name,
  manufacturer,
  specs,
  description,
  onChange,
}) {
  const updateSpec = (index, field, text) => {
    const next = specs.map((row, i) =>
      i === index ? { ...row, [field]: text } : row,
    );
    onChange({ specs: next });
  };

  const addSpec = () => onChange({ specs: [...specs, { key: "", value: "" }] });

  const removeSpec = (index) => {
    if (specs.length === 1) {
      onChange({ specs: [{ key: "", value: "" }] });
      return;
    }
    onChange({ specs: specs.filter((_, i) => i !== index) });
  };

  const inputClass =
    "w-full rounded-lg border border-border bg-surface px-3 py-2.5 text-sm outline-none placeholder:text-text-secondary focus:border-brand-secondary";

  return (
    <div className="space-y-4">
      <div>
        <label
          htmlFor="product-name"
          className="mb-2 block text-sm font-medium text-text-primary"
        >
          Название товара
        </label>
        <input
          id="product-name"
          value={name}
          onChange={(event) => onChange({ name: event.target.value })}
          placeholder="Манометр показывающий DM 02"
          className={inputClass}
        />
      </div>
      <div>
        <label
          htmlFor="product-manufacturer"
          className="mb-2 block text-sm font-medium text-text-primary"
        >
          Производитель
        </label>
        <input
          id="product-manufacturer"
          value={manufacturer}
          onChange={(event) => onChange({ manufacturer: event.target.value })}
          placeholder="Манотомь"
          className={inputClass}
        />
      </div>
      <div>
        <p className="mb-2 text-sm font-medium text-text-primary">
          Характеристики
        </p>
        <div className="space-y-2">
          {specs.map((row, index) => (
            <div key={index} className="flex gap-2">
              <input
                value={row.key}
                onChange={(event) =>
                  updateSpec(index, "key", event.target.value)
                }
                placeholder="Параметр"
                aria-label={`Параметр ${index + 1}`}
                className={`${inputClass} min-w-0 flex-1`}
              />
              <input
                value={row.value}
                onChange={(event) =>
                  updateSpec(index, "value", event.target.value)
                }
                placeholder="Значение"
                aria-label={`Значение ${index + 1}`}
                className={`${inputClass} min-w-0 flex-1`}
              />
              <button
                type="button"
                onClick={() => removeSpec(index)}
                aria-label="Убрать строку"
                className="shrink-0 rounded-lg border border-border bg-surface px-3 text-text-secondary transition-colors hover:border-error hover:text-error"
              >
                ×
              </button>
            </div>
          ))}
        </div>
        <button
          type="button"
          onClick={addSpec}
          className="mt-2 rounded-lg border border-dashed border-border px-3 py-2 text-sm text-text-secondary transition-colors hover:border-brand-secondary hover:text-text-primary"
        >
          + Добавить строку
        </button>
      </div>
      <div>
        <label
          htmlFor="product-description"
          className="mb-2 block text-sm font-medium text-text-primary"
        >
          Описание или фрагмент паспорта
        </label>
        <textarea
          id="product-description"
          value={description}
          onChange={(event) => onChange({ description: event.target.value })}
          placeholder="Прибор предназначен для измерения…"
          rows={4}
          className={`${inputClass} resize-y`}
        />
      </div>
    </div>
  );
}
