import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Modal } from "../../components/Modal";
import { useAuth } from "../auth/useAuth";
import { formatCurrency } from "../transactions/format";
import type { SavingsGoal } from "../transactions/types";
import { addContribution, createGoal, deleteGoal, getProjection, listGoals } from "./api";

const STATUS_LABELS: Record<string, string> = {
  active: "En marcha",
  completed: "Completada",
  archived: "Archivada",
};

function GoalCard({ goal }: { goal: SavingsGoal }) {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [contributionAmount, setContributionAmount] = useState("");
  const [showProjection, setShowProjection] = useState(false);

  const projectionQuery = useQuery({
    queryKey: ["goal-projection", goal.id],
    queryFn: () => getProjection(token as string, goal.id),
    enabled: token !== null && showProjection,
  });

  const contributeMutation = useMutation({
    mutationFn: () =>
      addContribution(token as string, goal.id, {
        amount: contributionAmount,
        contributed_at: new Date().toISOString().slice(0, 10),
      }),
    onSuccess: () => {
      setContributionAmount("");
      void queryClient.invalidateQueries({ queryKey: ["goals"] });
      void queryClient.invalidateQueries({ queryKey: ["goal-projection", goal.id] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteGoal(token as string, goal.id),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["goals"] }),
  });

  const widthPercent = Math.min(goal.pct, 100);

  return (
    <div className={`goal-card goal-card-${goal.status}`}>
      <div className="goal-card-header">
        <span className="goal-card-name">{goal.name}</span>
        <span className="goal-card-status">{STATUS_LABELS[goal.status]}</span>
      </div>
      <div className="goal-card-amounts">
        {formatCurrency(Number(goal.current_amount))} / {formatCurrency(Number(goal.target_amount))}
        {goal.target_date && <span className="page-status"> · objetivo: {goal.target_date}</span>}
      </div>
      <div className="budget-card-track">
        <div className="budget-card-bar" style={{ width: `${widthPercent}%` }} />
      </div>

      {goal.status === "active" && (
        <div className="goal-card-actions">
          <input
            type="number"
            min="0.01"
            step="0.01"
            placeholder="Importe"
            value={contributionAmount}
            onChange={(event) => setContributionAmount(event.target.value)}
          />
          <button
            type="button"
            disabled={!contributionAmount || contributeMutation.isPending}
            onClick={() => contributeMutation.mutate()}
          >
            Aportar
          </button>
          <button
            type="button"
            className="button-secondary"
            onClick={() => setShowProjection((value) => !value)}
          >
            {showProjection ? "Ocultar proyección" : "Ver proyección"}
          </button>
          <button
            type="button"
            className="button-secondary"
            onClick={() => deleteMutation.mutate()}
            disabled={deleteMutation.isPending}
          >
            Borrar
          </button>
        </div>
      )}

      {showProjection && projectionQuery.data && (
        <p className="page-status">
          {projectionQuery.data.has_enough_data
            ? `Al ritmo actual (${formatCurrency(Number(projectionQuery.data.monthly_pace))}/mes), la alcanzarías el ${projectionQuery.data.projected_date}.`
            : "Sin ritmo de aportación suficiente todavía para proyectar una fecha."}
        </p>
      )}
    </div>
  );
}

export function GoalsPage() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [targetAmount, setTargetAmount] = useState("");
  const [targetDate, setTargetDate] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const goalsQuery = useQuery({
    queryKey: ["goals"],
    queryFn: () => listGoals(token as string),
    enabled: token !== null,
  });

  const createMutation = useMutation({
    mutationFn: () =>
      createGoal(token as string, {
        name,
        target_amount: targetAmount,
        target_date: targetDate || null,
      }),
    onSuccess: () => {
      setName("");
      setTargetAmount("");
      setTargetDate("");
      setFormError(null);
      setShowCreateModal(false);
      void queryClient.invalidateQueries({ queryKey: ["goals"] });
    },
    onError: (error: Error) => setFormError(error.message),
  });

  const goals = goalsQuery.data ?? [];
  const hasGoals = goals.length > 0;

  const goalForm = (
    <div className="budget-form">
      <div className="budget-form-grid">
        <label htmlFor="goal-name">Nombre</label>
        <input id="goal-name" value={name} onChange={(event) => setName(event.target.value)} />

        <label htmlFor="goal-amount">Importe objetivo</label>
        <input
          id="goal-amount"
          type="number"
          min="0.01"
          step="0.01"
          value={targetAmount}
          onChange={(event) => setTargetAmount(event.target.value)}
        />

        <label htmlFor="goal-date">Fecha objetivo (opcional)</label>
        <input
          id="goal-date"
          type="date"
          value={targetDate}
          onChange={(event) => setTargetDate(event.target.value)}
        />
      </div>
      <button
        type="button"
        disabled={!name || !targetAmount || createMutation.isPending}
        onClick={() => createMutation.mutate()}
      >
        Crear meta
      </button>
      {formError && <p className="form-error">{formError}</p>}
    </div>
  );

  return (
    <div className="goals-page">
      {hasGoals && (
        <div className="expenses-toolbar expenses-toolbar-end">
          <div className="expenses-toolbar-actions">
            <button type="button" onClick={() => setShowCreateModal(true)}>
              + Nueva meta
            </button>
          </div>
        </div>
      )}

      {!goalsQuery.isLoading && !hasGoals && (
        <section>
          <h2>Nueva meta de ahorro</h2>
          {goalForm}
        </section>
      )}

      <section className="goal-list">
        <h2>Tus metas</h2>
        {goalsQuery.isLoading && <p className="page-status">Cargando metas...</p>}
        {!goalsQuery.isLoading && goals.length === 0 && (
          <p className="page-status">Todavía no tienes metas de ahorro.</p>
        )}
        {goals.map((goal) => (
          <GoalCard key={goal.id} goal={goal} />
        ))}
      </section>

      {showCreateModal && (
        <Modal title="Nueva meta de ahorro" onClose={() => setShowCreateModal(false)}>
          {goalForm}
        </Modal>
      )}
    </div>
  );
}
