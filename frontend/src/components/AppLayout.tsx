import { NavLink, Outlet, useNavigate } from "react-router";

import { useAuth } from "../features/auth/useAuth";

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="app-title">ExpenseTrack</span>
        <nav className="app-nav">
          <NavLink to="/" end className={({ isActive }) => (isActive ? "app-nav-active" : "")}>
            Dashboard
          </NavLink>
          <NavLink
            to="/transactions"
            className={({ isActive }) => (isActive ? "app-nav-active" : "")}
          >
            Movimientos
          </NavLink>
          <NavLink to="/imports" className={({ isActive }) => (isActive ? "app-nav-active" : "")}>
            Importar
          </NavLink>
          <NavLink to="/budgets" className={({ isActive }) => (isActive ? "app-nav-active" : "")}>
            Presupuestos
          </NavLink>
          <NavLink to="/insights" className={({ isActive }) => (isActive ? "app-nav-active" : "")}>
            Insights
          </NavLink>
        </nav>
        {user && (
          <div className="app-header-user">
            <span className="app-header-email">{user.email}</span>
            <button type="button" className="button-secondary" onClick={handleLogout}>
              Cerrar sesión
            </button>
          </div>
        )}
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
