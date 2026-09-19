export function categoryStyle(category = "") {
  const c = category.toLowerCase();
  if (c.includes("health")) return { bg: "var(--rust-tint)", text: "var(--rust-dark)", dot: "var(--rust)" };
  if (c.includes("evict") || c.includes("relocation")) return { bg: "var(--forest-tint)", text: "#92400E", dot: "var(--forest)" };
  if (c.includes("financial") || c.includes("scheme") || c.includes("tax")) return { bg: "var(--indigo-tint)", text: "#3730A3", dot: "var(--indigo)" };
  return { bg: "var(--rust-tint)", text: "var(--rust-dark)", dot: "var(--rust)" };
}