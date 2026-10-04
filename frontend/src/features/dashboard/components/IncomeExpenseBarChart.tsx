import { formatCurrency } from "../../transactions/format";

interface IncomeExpenseBarChartProps {
  income: number;
  expense: number;
}

export function IncomeExpenseBarChart({ income, expense }: IncomeExpenseBarChartProps) {
  const max = Math.max(income, expense, 1);

  return (
    <div className="income-expense-chart" role="img" aria-label="Entradas comparadas con salidas">
      <div className="income-expense-chart-row">
        <span className="income-expense-chart-label">Entradas</span>
        <div className="income-expense-chart-track">
          <div
            className="income-expense-chart-bar income-expense-chart-bar-income"
            style={{ width: `${(income / max) * 100}%` }}
          />
        </div>
        <span className="income-expense-chart-value">{formatCurrency(income)}</span>
      </div>
      <div className="income-expense-chart-row">
        <span className="income-expense-chart-label">Salidas</span>
        <div className="income-expense-chart-track">
          <div
            className="income-expense-chart-bar income-expense-chart-bar-expense"
            style={{ width: `${(expense / max) * 100}%` }}
          />
        </div>
        <span className="income-expense-chart-value">{formatCurrency(expense)}</span>
      </div>
    </div>
  );
}
