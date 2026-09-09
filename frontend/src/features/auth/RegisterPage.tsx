import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";

import { API_BASE_URL, ApiError } from "../../api/client";
import { googleLoginUrl } from "./api";
import { useAuth } from "./useAuth";

const MIN_PASSWORD_LENGTH = 8;

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => register({ email, password }),
    onSuccess: () => navigate("/", { replace: true }),
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setValidationError(null);

    if (password.length < MIN_PASSWORD_LENGTH) {
      setValidationError(`La contraseña debe tener al menos ${MIN_PASSWORD_LENGTH} caracteres.`);
      return;
    }
    if (password !== confirmPassword) {
      setValidationError("Las contraseñas no coinciden.");
      return;
    }

    mutation.mutate();
  }

  const errorMessage =
    validationError ??
    (mutation.isError
      ? mutation.error instanceof ApiError
        ? mutation.error.message
        : "No se pudo completar el registro."
      : null);

  return (
    <div className="auth-page">
      <form className="auth-form" onSubmit={handleSubmit}>
        <h1>Crear cuenta</h1>

        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />

        <label htmlFor="password">Contraseña</label>
        <input
          id="password"
          type="password"
          autoComplete="new-password"
          required
          minLength={MIN_PASSWORD_LENGTH}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />

        <label htmlFor="confirm-password">Confirmar contraseña</label>
        <input
          id="confirm-password"
          type="password"
          autoComplete="new-password"
          required
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
        />

        {errorMessage && (
          <p role="alert" className="form-error">
            {errorMessage}
          </p>
        )}

        <button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Creando cuenta..." : "Crear cuenta"}
        </button>

        <a className="button-secondary auth-google-button" href={googleLoginUrl(API_BASE_URL)}>
          Continuar con Google
        </a>

        <p className="auth-switch">
          ¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link>
        </p>
      </form>
    </div>
  );
}
