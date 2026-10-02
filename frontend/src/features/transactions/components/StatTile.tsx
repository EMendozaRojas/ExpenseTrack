export type StatAccent = "income" | "expense" | "neutral" | "info";

interface StatTileProps {
  label: string;
  value: string;
  icon?: string;
  accent?: StatAccent;
}

export function StatTile({ label, value, icon, accent = "neutral" }: StatTileProps) {
  return (
    <div className={`stat-card stat-card-${accent}`}>
      {icon && (
        <span className="stat-card-icon" aria-hidden="true">
          {icon}
        </span>
      )}
      <div className="stat-card-body">
        <span className="stat-tile-label">{label}</span>
        <span className="stat-tile-value">{value}</span>
      </div>
    </div>
  );
}
