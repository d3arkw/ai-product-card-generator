export async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return copyViaTextarea(text);
  }
}

function copyViaTextarea(text) {
  try {
    const area = document.createElement("textarea");
    area.value = text;
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(area);
    return ok;
  } catch {
    return false;
  }
}

export function toMarkdown(card) {
  const lines = [
    `# ${card.seo_title}`,
    "",
    card.seo_description,
    "",
    "## Характеристики",
    "",
    ...card.characteristics.map((item) => `- **${item.name}:** ${item.value}`),
    "",
    "## Поисковые запросы",
    "",
    ...card.search_queries.map((query) => `- ${query}`),
    "",
    "## Commercial",
    "",
    card.commercial_block,
  ];
  if (card.missing_data.length > 0) {
    lines.push(
      "",
      "## Не хватает данных",
      "",
      ...card.missing_data.map((item) => `- ${item}`),
    );
  }
  return lines.join("\n");
}

export function toText(card) {
  const parts = [
    card.seo_title,
    "",
    card.seo_description,
    "",
    "Характеристики:",
    ...card.characteristics.map((item) => `${item.name}: ${item.value}`),
    "",
    `Поисковые запросы: ${card.search_queries.join("; ")}`,
    "",
    card.commercial_block,
  ];
  if (card.missing_data.length > 0) {
    parts.push("", `Не хватает данных: ${card.missing_data.join("; ")}`);
  }
  return parts.join("\n");
}
