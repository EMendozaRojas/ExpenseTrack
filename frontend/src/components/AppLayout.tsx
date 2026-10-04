import { Navigate, NavLink, Outlet, useNavigate } from "react-router";

import { useAuth } from "../features/auth/useAuth";
import { useUnreadCount } from "../features/notifications/useUnreadCount";
import { useAvatarUrl } from "../features/profile/useAvatarUrl";

const NAV_ITEMS = [
  { to: "/", end: true, icon: "📊", label: "Estadísticas" },
  { to: "/transactions", icon: "💸", label: "Movimientos" },
  { to: "/imports", icon: "📥", label: "Importar" },
  { to: "/budgets", icon: "🎯", label: "Presupuestos" },
  { to: "/goals", icon: "🏁", label: "Metas" },
  { to: "/insights", icon: "💡", label: "Análisis" },
  { to: "/notifications", icon: "🔔", label: "Notificaciones" },
  { to: "/settings", icon: "⚙️", label: "Configuración" },
];

function navLinkClassName({ isActive }: { isActive: boolean }): string {
  return isActive ? "app-nav-active" : "";
}

export function AppLayout() {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();
  const avatarUrl = useAvatarUrl(token, user?.has_avatar ?? false);
  const unreadCount = useUnreadCount(token);

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  if (user && !user.full_name) {
    return <Navigate to="/onboarding" replace />;
  }

  const displayName = user?.full_name ?? user?.email ?? "";
  const initial = displayName ? displayName[0].toUpperCase() : "?";

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        {user && (
          <div className="app-sidebar-profile">
            {avatarUrl ? (
              <img className="app-sidebar-avatar-photo" src={avatarUrl} alt={displayName} />
            ) : (
              <div className="app-sidebar-avatar" aria-hidden="true">
                {initial}
              </div>
            )}
            <span className="app-sidebar-name">{displayName}</span>
          </div>
        )}

        <nav className="app-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={navLinkClassName}>
              <span className="app-nav-icon" aria-hidden="true">
                {item.icon}
              </span>
              {item.label}
              {item.to === "/notifications" && unreadCount > 0 && (
                <span className="app-nav-badge">{unreadCount}</span>
              )}
            </NavLink>
          ))}
        </nav>

        {user && (
          <button
            type="button"
            className="button-secondary app-sidebar-logout"
            onClick={handleLogout}
          >
            Cerrar sesión
          </button>
        )}

        <div className="app-sidebar-footer">
          <img className="app-sidebar-logo" src="/logo.png" alt="ExpenseTrack — Tus gastos, siempre contigo" />
        </div>
      </aside>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
