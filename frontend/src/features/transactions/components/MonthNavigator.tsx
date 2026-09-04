import { MONTH_NAMES } from "../format";

interface MonthNavigatorProps {
  year: number;
  month: number;
  onChange: (year: number, month: number) => void;
}

export function MonthNavigator({ year, month, onChange }: MonthNavigatorProps) {
  function goToPrevious() {
    if (month === 1) {
      onChange(year - 1, 12);
    } else {
      onChange(year, month - 1);
    }
  }

  function goToNext() {
    if (month === 12) {
      onChange(year + 1, 1);
    } else {
      onChange(year, month + 1);
    }
  }

  return (
    <div className="month-navigator">
      <button type="button" onClick={goToPrevious} aria-label="Mes anterior">
        ←
      </button>
      <span className="month-navigator-label">
        {MONTH_NAMES[month - 1]} {year}
      </span>
      <button type="button" onClick={goToNext} aria-label="Mes siguiente">
        →
      </button>
    </div>
  );
}
