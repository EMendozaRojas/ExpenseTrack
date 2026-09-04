import { formatCurrency } from "../format";
import type { CategorySummary } from "../types";

interface CategoryBarChartProps {
  data: CategorySummary[];
}

export function CategoryBarChart({ data }: CategoryBarChartProps) {
  if (data.length === 0) {
    return <p className="page-status">Sin gastos clasificados este mes.</p>;
  }

  const sorted = [...data].sort((a, b) => Number(b.total) - Number(a.total));
  const maxValue = Math.max(...sorted.map((item) => Number(item.total)));

  return (
    <div
      className="category-chart"
      role="img"
      aria-label="Gastos del mes clasificados por categoría"
    >
      {sorted.map((item) => {
        const value = Number(item.total);
        const widthPercent = maxValue > 0 ? (value / maxValue) * 100 : 0;
        return (
          <div className="category-chart-row" key={item.category_id} tabIndex={0}>
            <span className="category-chart-label">{item.category_name}</span>
            <div className="category-chart-track">
              <div className="category-chart-bar" style={{ width: `${widthPercent}%` }} />
            </div>
            <span className="category-chart-value">{formatCurrency(value)}</span>
          </div>
        );
      })}
    </div>
  );
}
