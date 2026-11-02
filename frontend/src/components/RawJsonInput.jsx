export default function RawJsonInput({ value, onChange }) {
  return (
    <div>
      <p className="mb-2 text-sm font-medium text-text-primary">
        Товар в формате JSON
      </p>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        rows={12}
        spellCheck={false}
        placeholder={
          '{\n  "name": "Манометр показывающий DM 02",\n  "manufacturer": "Манотомь",\n  "specs": {},\n  "description": "..."\n}'
        }
        className="w-full rounded-lg border border-border bg-surface px-3 py-2.5 font-mono text-xs leading-relaxed outline-none placeholder:text-text-secondary focus:border-brand-secondary"
      />
    </div>
  );
}
