const TIERS = [
  { value: "cheap", label: "Эконом" },
  { value: "medium", label: "Стандарт" },
  { value: "expensive", label: "Максимум" },
];

export default function TierSelect({ tier, onChange, models }) {
  return (
    <div>
      <p
        className="mb-2 text-sm font-medium text-text-primary"
        id="model-tier-label"
      >
        Модель
      </p>
      <div
        role="radiogroup"
        aria-labelledby="model-tier-label"
        className="grid grid-cols-3 gap-2"
      >
        {TIERS.map((option) => (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={tier === option.value}
            onClick={() => onChange(option.value)}
            className={`rounded-lg border px-3 py-2 text-left transition-all ${
              tier === option.value
                ? "border-transparent bg-gradient-to-b from-brand-primary to-brand-dark text-text-inverse shadow-md"
                : "border-border bg-surface text-text-primary hover:border-brand-secondary"
            }`}
          >
            <span className="block text-sm font-medium">{option.label}</span>
            <span
              className="mt-0.5 block truncate font-mono text-[11px] opacity-70"
              title={models?.[option.value] ?? ""}
            >
              {models?.[option.value] ?? "…"}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
