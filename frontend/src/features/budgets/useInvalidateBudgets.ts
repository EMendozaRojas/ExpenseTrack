import { useQueryClient } from "@tanstack/react-query";

/** Tras cualquier cambio en presupuestos: un cambio "este mes y los
 * siguientes" afecta a varios meses, y puede crear avisos. */
export function useInvalidateBudgets(): () => void {
  const queryClient = useQueryClient();
  return () => {
    for (const key of [
      "budgets",
      "budget-copy-preview",
      "budget-recommendations",
      "notifications",
      "notifications-unread-count",
    ]) {
      void queryClient.invalidateQueries({ queryKey: [key] });
    }
  };
}
