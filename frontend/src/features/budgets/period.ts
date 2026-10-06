import { MONTH_NAMES, pad2 } from "../transactions/format";

/** "YYYY-MM", el formato de mes que usa la API de presupuestos. */
export function toPeriod(year: number, month: number): string {
  return `${year}-${pad2(month)}`;
}

export function formatPeriod(period: string): string {
  const [year, month] = period.split("-").map(Number);
  return `${MONTH_NAMES[month - 1]} de ${year}`;
}

export function isPastMonth(year: number, month: number, today: Date = new Date()): boolean {
  return year * 12 + month < today.getFullYear() * 12 + today.getMonth() + 1;
}

export function currentYearMonth(today: Date = new Date()): { year: number; month: number } {
  return { year: today.getFullYear(), month: today.getMonth() + 1 };
}
