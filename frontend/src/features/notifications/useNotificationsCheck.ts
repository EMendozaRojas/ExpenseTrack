import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";

import { checkNotifications } from "./api";

/** Llama a `POST /notifications/check` una vez por carga de la app
 * autenticada (login o recarga) y refresca el contador de no leídas. */
export function useNotificationsCheck(token: string | null): void {
  const queryClient = useQueryClient();
  const checkedToken = useRef<string | null>(null);

  useEffect(() => {
    if (token === null || checkedToken.current === token) return;
    checkedToken.current = token;
    checkNotifications(token)
      .then(async () => {
        // Si la primera carga del contador sigue en curso, invalidar la
        // reutilizaría (y no vería los avisos recién creados): se cancela antes.
        for (const queryKey of [["notifications-unread-count"], ["notifications"]]) {
          await queryClient.cancelQueries({ queryKey });
          void queryClient.invalidateQueries({ queryKey });
        }
      })
      .catch(() => {
        // La revisión es best-effort: si falla, los avisos llegarán con la
        // siguiente acción o la próxima vez que se entre.
      });
  }, [token, queryClient]);
}
