import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router";

import { useAuth } from "../auth/useAuth";
import { getDashboardSummary } from "../transactions/api";
import { MonthNavigator } from "../transactions/components/MonthNavigator";
import { StatTile } from "../transactions/components/StatTile";
import { formatCurrency } from "../transactions/format";

const today = new Date();

function parseParam(value: string | null, min: number, max: number, fallback: number): number {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed >= min && parsed <= max ? parsed : fallback;
}

export function DashboardPage() {
  const { token } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const year = parseParam(searchParams.get("year"), 1, 9999, today.getFullYear());
  const month = parseParam(searchParams.get("month"), 1, 12, today.getMonth() + 1);

  function handleMonthChange(newYear: number, newMonth: number) {
    setSearchParams({ year: String(newYear), month: String(newMonth) });
  }

  const summaryQuery = useQuery({
    queryKey: ["dashboard-summary", year, month],
    queryFn: () => getDashboardSummary(token as string, year, month),
    enabled: token !== null,
    staleTime: 5 * 60 * 1000,
  });

  const summary = summaryQuery.data;

  return (
    <div className="dashboard-page">
      <MonthNavigator
        year={year}
        month={month}
        onChange={handleMonthChange}
      />

      {summaryQuery.isLoading && <p className="page-status">Cargando dashboard...</p>}

      {summary && (
        <>
          {summary.incomplete_data && (
            <div className="dashboard-banner" role="status">
              Datos incompletos:{" "}
              {summary.last_transaction_date
                ? `no hay movimientos posteriores al ${summary.last_transaction_date}.`
                : "todavía no hay movimientos registrados este mes."}
            </div>
          )}

          <section className="dashboard-stats">
            <StatTile
              label="Entradas"
              value={formatCurrency(Number(summary.income_total))}
              icon="⬆️"
              accent="income"
            />
            <StatTile
              label="Salidas"
              value={formatCurrency(Number(summary.expense_total))}
              icon="⬇️"
              accent="expense"
            />
            <div
              className={`stat-card dashboard-net dashboard-net-${summary.net_status}`}
            >
              <span
                className="stat-card-icon"
                aria-hidden="true"
                style={{
                  background:
                    summary.net_status === "a_favor"
                      ? "var(--accent-income-track)"
                      : "var(--accent-expense-track)",
                  color:
                    summary.net_status === "a_favor"
                      ? "var(--accent-income)"
                      : "var(--accent-expense)",
                }}
              >
                ⚖️
              </span>
              <div className="stat-card-body">
                <span className="stat-tile-label">
                  Saldo neto · {summary.net_status === "a_favor" ? "A favor" : "En contra"}
                </span>
                <span className="stat-tile-value">{formatCurrency(Number(summary.net_total))}</span>
              </div>
            </div>
          </section>

          <section className="dashboard-stats">
            <StatTile
              label="Gasto fijo"
              value={formatCurrency(Number(summary.fixed_total))}
              icon="📌"
              accent="neutral"
            />
            <StatTile
              label="Gasto variable"
              value={formatCurrency(Number(summary.variable_total))}
              icon="🔄"
              accent="info"
            />
          </section>

          <section>
            <h2>Gasto por categoría</h2>
            {summary.by_category.length === 0 ? (
              <div className="dashboard-empty-state">
                <span className="dashboard-empty-state-icon" aria-hidden="true">
                  🧾
                </span>
                <span className="dashboard-empty-state-title">
                  Todavía no hay gastos clasificados este mes
                </span>
                <span className="dashboard-empty-state-hint">
                  Registra tu primer movimiento para empezar a ver el desglose por categoría.
                </span>
                <Link to="/transactions" className="button-secondary">
                  Agregar movimiento
                </Link>
              </div>
            ) : (
              <div className="category-tree">
                {summary.by_category.map((node) => (
                  <details key={node.category_id} className="category-tree-root">
                    <summary>
                      <span className="category-tree-name">
                        {node.icon ? `${node.icon} ` : ""}
                        {node.category_name}
                      </span>
                      <span className="category-tree-total">
                        {formatCurrency(Number(node.total))}
                      </span>
                    </summary>
                    <ul>
                      {node.subcategories.map((sub) => (
                        <li key={sub.category_id} className="category-tree-sub">
                          <span>{sub.category_name}</span>
                          <span>{formatCurrency(Number(sub.total))}</span>
                        </li>
                      ))}
                    </ul>
                  </details>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
