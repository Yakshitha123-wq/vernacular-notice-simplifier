export function categoryStyle(category = "") {
  const c = category.toLowerCase();
  if (c.includes("health")) return { bg: "var(--teal-tint)", text: "var(--teal-dark)", dot: "var(--teal)" };
  if (c.includes("evict") || c.includes("relocation")) return { bg: "var(--amber-tint)", text: "#92400E", dot: "var(--amber)" };
  if (c.includes("financial") || c.includes("scheme") || c.includes("tax")) return { bg: "var(--indigo-tint)", text: "#3730A3", dot: "var(--indigo)" };
  return { bg: "var(--teal-tint)", text: "var(--teal-dark)", dot: "var(--teal)" };
}