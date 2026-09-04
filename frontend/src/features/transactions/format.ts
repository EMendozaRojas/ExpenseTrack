const currencyFormatter = new Intl.NumberFormat("es-ES", {
  style: "currency",
  currency: "EUR",
});

export function formatCurrency(amount: number): string {
  return currencyFormatter.format(amount);
}

export function formatSignedCurrency(amount: number): string {
  return currencyFormatter.format(Math.abs(amount));
}

export const MONTH_NAMES = [
  "enero",
  "febrero",
  "marzo",
  "abril",
  "mayo",
  "junio",
  "julio",
  "agosto",
  "septiembre",
  "octubre",
  "noviembre",
  "diciembre",
];

export function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

interface FlattenableCategory {
  id: number;
  name: string;
  children: FlattenableCategory[];
}

export interface FlatCategoryOption {
  id: number;
  label: string;
}

export function flattenCategories(categories: FlattenableCategory[]): FlatCategoryOption[] {
  const options: FlatCategoryOption[] = [];
  for (const root of categories) {
    options.push({ id: root.id, label: root.name });
    for (const child of root.children) {
      options.push({ id: child.id, label: `${root.name} · ${child.name}` });
    }
  }
  return options;
}
