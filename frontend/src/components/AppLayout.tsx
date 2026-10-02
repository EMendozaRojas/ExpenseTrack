import { NavLink, Outlet, useNavigate } from "react-router";

import { useAuth } from "../features/auth/useAuth";

const NAV_ITEMS = [
  { to: "/", end: true, icon: "📊", label: "Dashboard" },
  { to: "/transactions", icon: "💸", label: "Movimientos" },
  { to: "/imports", icon: "📥", label: "Importar" },
  { to: "/budgets", icon: "🎯", label: "Presupuestos" },
  { to: "/goals", icon: "🏁", label: "Metas" },
  { to: "/insights", icon: "💡", label: "Insights" },
  { to: "/trash", icon: "🗑️", label: "Papelera" },
  { to: "/settings", icon: "⚙️", label: "Configuración" },
];

function navLinkClassName({ isActive }: { isActive: boolean }): string {
  return isActive ? "app-nav-active" : "";
}

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  const initial = user?.email ? user.email[0].toUpperCase() : "?";

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        {user && (
          <div className="app-sidebar-profile">
            <div className="app-sidebar-avatar" aria-hidden="true">
              {initial}
            </div>
            <span className="app-sidebar-name">{user.email}</span>
          </div>
        )}

        <nav className="app-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={navLinkClassName}>
              <span className="app-nav-icon" aria-hidden="true">
                {item.icon}
              </span>
              {item.label}
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
