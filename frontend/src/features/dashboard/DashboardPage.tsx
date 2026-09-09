import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { useAuth } from "../auth/useAuth";
import { getDashboardSummary } from "../transactions/api";
import { MonthNavigator } from "../transactions/components/MonthNavigator";
import { StatTile } from "../transactions/components/StatTile";
import { formatCurrency } from "../transactions/format";

const today = new Date();

export function DashboardPage() {
  const { token } = useAuth();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);

  const summaryQuery = useQuery({
    queryKey: ["dashboard-summary", year, month],
    queryFn: () => getDashboardSummary(token as string, year, month),
    enabled: token !== null,
  });

  const summary = summaryQuery.data;

  return (
    <div className="dashboard-page">
      <MonthNavigator
        year={year}
        month={month}
        onChange={(newYear, newMonth) => {
          setYear(newYear);
          setMonth(newMonth);
        }}
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
            <StatTile label="Entradas" value={formatCurrency(Number(summary.income_total))} />
            <StatTile label="Salidas" value={formatCurrency(Number(summary.expense_total))} />
            <div
              className={`stat-tile dashboard-net dashboard-net-${summary.net_status}`}
            >
              <span className="stat-tile-label">
                Saldo neto · {summary.net_status === "a_favor" ? "A favor" : "En contra"}
              </span>
              <span className="stat-tile-value">{formatCurrency(Number(summary.net_total))}</span>
            </div>
          </section>

          <section className="dashboard-stats">
            <StatTile label="Gasto fijo" value={formatCurrency(Number(summary.fixed_total))} />
            <StatTile
              label="Gasto variable"
              value={formatCurrency(Number(summary.variable_total))}
            />
          </section>

          <section>
            <h2>Gasto por categoría</h2>
            {summary.by_category.length === 0 ? (
              <p className="page-status">Sin gastos clasificados este mes.</p>
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
