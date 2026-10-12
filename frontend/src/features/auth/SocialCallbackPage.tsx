import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router";

import { useAuth } from "./useAuth";

export function SocialCallbackPage() {
  const { loginWithTokens } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const handled = useRef(false);

  useEffect(() => {
    if (handled.current) return;
    handled.current = true;

    // El backend pasa los tokens en el fragmento (#…); se borran de la barra
    // de direcciones y del historial en cuanto se leen.
    const params = new URLSearchParams(window.location.hash.slice(1));
    const accessToken = params.get("access_token");
    const refreshToken = params.get("refresh_token");
    window.history.replaceState(null, "", window.location.pathname);

    if (!accessToken) {
      setError("No se recibió un token de acceso válido.");
      return;
    }

    loginWithTokens(accessToken, refreshToken);
    navigate("/", { replace: true });
  }, [loginWithTokens, navigate]);

  return (
    <div className="auth-page">
      <div className="auth-form">
        <p className="page-status">{error ?? "Completando el inicio de sesión..."}</p>
      </div>
    </div>
  );
}
