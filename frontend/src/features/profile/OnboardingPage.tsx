import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router";

import { useAuth } from "../auth/useAuth";
import { ApiError } from "../../api/client";
import { updateProfile, uploadAvatar } from "./api";

export function OnboardingPage() {
  const { token, user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [avatarFile, setAvatarFile] = useState<File | null>(null);

  if (user?.full_name) {
    return <Navigate to="/" replace />;
  }

  const mutation = useMutation({
    mutationFn: async () => {
      await updateProfile(token as string, fullName);
      if (avatarFile) {
        await uploadAvatar(token as string, avatarFile);
      }
      await refreshUser();
    },
    onSuccess: () => navigate("/", { replace: true }),
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    mutation.mutate();
  }

  const errorMessage =
    mutation.isError && mutation.error instanceof ApiError
      ? mutation.error.message
      : mutation.isError
        ? "No se pudo guardar tu perfil."
        : null;

  return (
    <div className="auth-page">
      <form className="auth-form" onSubmit={handleSubmit}>
        <h1>¡Bienvenido/a!</h1>
        <p className="page-hint">Cuéntanos cómo te llamas para personalizar tu cuenta.</p>

        <label htmlFor="onboarding-name">Nombre</label>
        <input
          id="onboarding-name"
          type="text"
          required
          value={fullName}
          onChange={(event) => setFullName(event.target.value)}
        />

        <label htmlFor="onboarding-avatar">Foto de perfil (opcional)</label>
        <input
          id="onboarding-avatar"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={(event) => setAvatarFile(event.target.files?.[0] ?? null)}
        />

        {errorMessage && (
          <p role="alert" className="form-error">
            {errorMessage}
          </p>
        )}

        <button type="submit" disabled={!fullName.trim() || mutation.isPending}>
          {mutation.isPending ? "Guardando..." : "Continuar"}
        </button>
      </form>
    </div>
  );
}
