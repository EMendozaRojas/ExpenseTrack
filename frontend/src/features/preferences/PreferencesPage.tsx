import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { useAuth } from "../auth/useAuth";
import { getInsightSettings, updateInsightSettings } from "../insights/api";
import { deleteAvatar, updateProfile, uploadAvatar } from "../profile/api";
import { useAvatarUrl } from "../profile/useAvatarUrl";
import { getPreferences, updatePreferences } from "./api";
import { SUPPORTED_CURRENCIES } from "./currencies";

const CURRENCY_CHANGE_WARNING =
  "Este cambio afectará a tus nuevos registros. Tus datos pasados mantendrán el valor numérico con el que fueron guardados.";

function ProfileSection() {
  const { token, user, refreshUser } = useAuth();
  const avatarUrl = useAvatarUrl(token, user?.has_avatar ?? false);
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [avatarFile, setAvatarFile] = useState<File | null>(null);

  const nameMutation = useMutation({
    mutationFn: () => updateProfile(token as string, fullName),
    onSuccess: () => void refreshUser(),
  });

  const avatarMutation = useMutation({
    mutationFn: () => uploadAvatar(token as string, avatarFile as File),
    onSuccess: () => {
      setAvatarFile(null);
      void refreshUser();
    },
  });

  const deleteAvatarMutation = useMutation({
    mutationFn: () => deleteAvatar(token as string),
    onSuccess: () => void refreshUser(),
  });

  return (
    <section className="preferences-form">
      <h2>Perfil</h2>

      <div className="profile-avatar-row">
        {avatarUrl ? (
          <img className="profile-avatar-preview" src={avatarUrl} alt={user?.full_name ?? ""} />
        ) : (
          <div className="profile-avatar-preview profile-avatar-placeholder" aria-hidden="true">
            {(user?.full_name ?? user?.email ?? "?")[0].toUpperCase()}
          </div>
        )}
        <div className="profile-avatar-actions">
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(event) => setAvatarFile(event.target.files?.[0] ?? null)}
          />
          <div className="profile-avatar-actions-buttons">
            <button
              type="button"
              disabled={!avatarFile || avatarMutation.isPending}
              onClick={() => avatarMutation.mutate()}
            >
              Subir foto
            </button>
            {user?.has_avatar && (
              <button
                type="button"
                className="button-secondary"
                disabled={deleteAvatarMutation.isPending}
                onClick={() => deleteAvatarMutation.mutate()}
              >
                Quitar foto
              </button>
            )}
          </div>
        </div>
      </div>

      <label htmlFor="profile-full-name">Nombre completo</label>
      <input
        id="profile-full-name"
        type="text"
        value={fullName}
        onChange={(event) => setFullName(event.target.value)}
      />
      <button
        type="button"
        disabled={!fullName.trim() || fullName === user?.full_name || nameMutation.isPending}
        onClick={() => nameMutation.mutate()}
      >
        Guardar nombre
      </button>
      {nameMutation.isSuccess && <p className="page-status">Nombre actualizado.</p>}
    </section>
  );
}

function AntSpendingSettingsSection() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState<{
    ant_max_amount: string;
    ant_min_occurrences: string;
    ant_min_aggregate: string;
  } | null>(null);

  const settingsQuery = useQuery({
    queryKey: ["insights-settings"],
    queryFn: () => getInsightSettings(token as string),
    enabled: token !== null,
  });

  const settingsMutation = useMutation({
    mutationFn: () =>
      updateInsightSettings(token as string, {
        ant_max_amount: draft!.ant_max_amount,
        ant_min_occurrences: Number(draft!.ant_min_occurrences),
        ant_min_aggregate: draft!.ant_min_aggregate,
      }),
    onSuccess: () => {
      setDraft(null);
      void queryClient.invalidateQueries({ queryKey: ["insights-settings"] });
    },
  });

  const settings = settingsQuery.data;

  return (
    <section className="preferences-form">
      <h2>Umbrales de gasto hormiga</h2>
      {settings && (
        <>
          <label htmlFor="ant-max-amount">Importe máximo por movimiento</label>
          <input
            id="ant-max-amount"
            type="number"
            step="0.01"
            value={draft?.ant_max_amount ?? settings.ant_max_amount}
            onChange={(event) =>
              setDraft({
                ant_max_amount: event.target.value,
                ant_min_occurrences: draft?.ant_min_occurrences ?? String(settings.ant_min_occurrences),
                ant_min_aggregate: draft?.ant_min_aggregate ?? settings.ant_min_aggregate,
              })
            }
          />

          <label htmlFor="ant-min-occurrences">Mínimo de movimientos</label>
          <input
            id="ant-min-occurrences"
            type="number"
            step="1"
            min="1"
            value={draft?.ant_min_occurrences ?? settings.ant_min_occurrences}
            onChange={(event) =>
              setDraft({
                ant_max_amount: draft?.ant_max_amount ?? settings.ant_max_amount,
                ant_min_occurrences: event.target.value,
                ant_min_aggregate: draft?.ant_min_aggregate ?? settings.ant_min_aggregate,
              })
            }
          />

          <label htmlFor="ant-min-aggregate">Mínimo acumulado en el mes</label>
          <input
            id="ant-min-aggregate"
            type="number"
            step="0.01"
            value={draft?.ant_min_aggregate ?? settings.ant_min_aggregate}
            onChange={(event) =>
              setDraft({
                ant_max_amount: draft?.ant_max_amount ?? settings.ant_max_amount,
                ant_min_occurrences: draft?.ant_min_occurrences ?? String(settings.ant_min_occurrences),
                ant_min_aggregate: event.target.value,
              })
            }
          />

          <button
            type="button"
            disabled={!draft || settingsMutation.isPending}
            onClick={() => settingsMutation.mutate()}
          >
            Guardar umbrales
          </button>
          {settingsMutation.isSuccess && !draft && (
            <p className="page-status">Umbrales actualizados.</p>
          )}
        </>
      )}
    </section>
  );
}

export function PreferencesPage() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const [selectedCurrency, setSelectedCurrency] = useState<string | null>(null);
  const [pendingCurrency, setPendingCurrency] = useState<string | null>(null);

  const preferencesQuery = useQuery({
    queryKey: ["preferences"],
    queryFn: () => getPreferences(token as string),
    enabled: token !== null,
  });

  useEffect(() => {
    if (preferencesQuery.data && selectedCurrency === null) {
      setSelectedCurrency(preferencesQuery.data.base_currency);
    }
  }, [preferencesQuery.data, selectedCurrency]);

  const mutation = useMutation({
    mutationFn: (currency: string) => updatePreferences(token as string, { base_currency: currency }),
    onSuccess: (updated) => {
      setSelectedCurrency(updated.base_currency);
      setPendingCurrency(null);
      void queryClient.invalidateQueries({ queryKey: ["preferences"] });
    },
  });

  const currentCurrency = preferencesQuery.data?.base_currency ?? null;

  function handleSelectChange(newCurrency: string) {
    setSelectedCurrency(newCurrency);
    if (currentCurrency && newCurrency !== currentCurrency) {
      setPendingCurrency(newCurrency);
    } else {
      setPendingCurrency(null);
    }
  }

  return (
    <div className="preferences-page">
      <h1>Configuración</h1>

      <ProfileSection />

      <section className="preferences-form">
        <h2>Moneda principal</h2>

        {preferencesQuery.isLoading && <p className="page-status">Cargando preferencias...</p>}

        {!preferencesQuery.isLoading && preferencesQuery.data?.has_transactions && (
          <p className="page-hint">
            Ya tienes movimientos registrados, así que la moneda principal no se puede cambiar.
          </p>
        )}

        {!preferencesQuery.isLoading && (
          <>
            <label htmlFor="preferences-base-currency">Moneda principal</label>
            <select
              id="preferences-base-currency"
              value={selectedCurrency ?? ""}
              disabled={preferencesQuery.data?.has_transactions}
              onChange={(event) => handleSelectChange(event.target.value)}
            >
              {SUPPORTED_CURRENCIES.map((currency) => (
                <option key={currency} value={currency}>
                  {currency}
                </option>
              ))}
            </select>

            {pendingCurrency && (
              <div role="alert" className="preferences-warning">
                <p>{CURRENCY_CHANGE_WARNING}</p>
                <div className="preferences-warning-actions">
                  <button
                    type="button"
                    disabled={mutation.isPending}
                    onClick={() => mutation.mutate(pendingCurrency)}
                  >
                    Confirmar cambio
                  </button>
                  <button
                    type="button"
                    className="button-secondary"
                    onClick={() => {
                      setSelectedCurrency(currentCurrency);
                      setPendingCurrency(null);
                    }}
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            )}

            {!pendingCurrency && mutation.isSuccess && (
              <p className="page-status">Moneda principal actualizada.</p>
            )}
          </>
        )}
      </section>

      <AntSpendingSettingsSection />
    </div>
  );
}
