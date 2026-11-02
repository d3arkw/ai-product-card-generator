export default function ErrorBanner({ error }) {
  if (!error) return null;
  return (
    <div className="rounded-xl border border-error bg-surface p-4">
      <p className="text-sm font-medium text-error">{error.message}</p>
      {error.details?.length > 0 && (
        <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-text-secondary">
          {error.details.map((detail, index) => (
            <li key={index}>{detail}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
