const OPTIONS = [
  { value: "openai", label: "OpenAI" },
  { value: "gemini", label: "Gemini" },
  { value: "routerai", label: "RouterAI" },
];

export default function ProviderSelect({ value, onChange }) {
  return (
    <div>
      <p
        className="mb-2 text-sm font-medium text-text-primary"
        id="provider-label"
      >
        Провайдер
      </p>
      <div
        role="radiogroup"
        aria-labelledby="provider-label"
        className="grid grid-cols-3 gap-2"
      >
        {OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={value === option.value}
            onClick={() => onChange(option.value)}
            className={`rounded-lg border px-4 py-2.5 text-sm font-medium transition-all ${
              value === option.value
                ? "border-transparent bg-gradient-to-b from-brand-primary to-brand-dark text-text-inverse shadow-md"
                : "border-border bg-surface text-text-primary hover:border-brand-secondary"
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}
