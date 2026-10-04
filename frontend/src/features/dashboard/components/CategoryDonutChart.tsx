import { formatCurrency } from "../../transactions/format";
import type { DashboardCategoryNode } from "../../transactions/types";

interface CategoryDonutChartProps {
  data: DashboardCategoryNode[];
}

const FALLBACK_PALETTE = [
  "#3b82f6",
  "#22c55e",
  "#a855f7",
  "#f43f5e",
  "#f59e0b",
  "#06b6d4",
  "#ec4899",
  "#84cc16",
];

const RADIUS = 70;
const STROKE_WIDTH = 28;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export function CategoryDonutChart({ data }: CategoryDonutChartProps) {
  const total = data.reduce((sum, node) => sum + Number(node.total), 0);

  if (total <= 0) {
    return null;
  }

  let cumulative = 0;
  const segments = data.map((node, index) => {
    const value = Number(node.total);
    const fraction = value / total;
    const dash = fraction * CIRCUMFERENCE;
    const offset = cumulative * CIRCUMFERENCE;
    cumulative += fraction;
    return {
      ...node,
      value,
      pct: fraction * 100,
      color: node.color ?? FALLBACK_PALETTE[index % FALLBACK_PALETTE.length],
      dash,
      offset,
    };
  });

  return (
    <div className="category-donut">
      <svg
        viewBox="0 0 180 180"
        className="category-donut-svg"
        role="img"
        aria-label="Gasto por categoría en gráfica de dona"
      >
        <g transform="rotate(-90 90 90)">
          {segments.map((segment) => (
            <circle
              key={segment.category_id}
              cx="90"
              cy="90"
              r={RADIUS}
              fill="none"
              stroke={segment.color}
              strokeWidth={STROKE_WIDTH}
              strokeDasharray={`${segment.dash} ${CIRCUMFERENCE - segment.dash}`}
              strokeDashoffset={-segment.offset}
            />
          ))}
        </g>
        <text x="90" y="85" textAnchor="middle" className="category-donut-total-label">
          Total
        </text>
        <text x="90" y="105" textAnchor="middle" className="category-donut-total-value">
          {formatCurrency(total)}
        </text>
      </svg>

      <ul className="category-donut-legend">
        {segments.map((segment) => (
          <li key={segment.category_id} className="category-donut-legend-item">
            <span
              className="category-donut-legend-swatch"
              style={{ background: segment.color }}
              aria-hidden="true"
            />
            <span className="category-donut-legend-name">
              {segment.icon ? `${segment.icon} ` : ""}
              {segment.category_name}
            </span>
            <span className="category-donut-legend-pct">{segment.pct.toFixed(0)}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
