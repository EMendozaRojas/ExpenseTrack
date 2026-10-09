import { Navigate, NavLink, Outlet, useNavigate } from "react-router";

import { useAuth } from "../features/auth/useAuth";
import { useNotificationsCheck } from "../features/notifications/useNotificationsCheck";
import { useUnreadCount } from "../features/notifications/useUnreadCount";
import { useAvatarUrl } from "../features/profile/useAvatarUrl";
import { BrandMark } from "./BrandMark";
import { MobileNav } from "./MobileNav";
import { NAV_ITEMS, NOTIFICATIONS_PATH } from "./navItems";

function navLinkClassName({ isActive }: { isActive: boolean }): string {
  return isActive ? "app-nav-active" : "";
}

export function AppLayout() {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();
  const avatarUrl = useAvatarUrl(token, user?.has_avatar ?? false);
  const unreadCount = useUnreadCount(token);
  useNotificationsCheck(token);

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
              {item.to === NOTIFICATIONS_PATH && unreadCount > 0 && (
                <span className="app-nav-badge">{unreadCount}</span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="app-sidebar-footer">
          <BrandMark variant="sidebar" />
        </div>
      </aside>

      <div className="app-content">
        <header className="app-topbar">
          {/* En el móvil la marca va aquí; en el ordenador ya está en el menú lateral. */}
          <div className="app-topbar-brand">
            <BrandMark variant="topbar" />
          </div>
          {user && (
            <button type="button" className="button-secondary" onClick={handleLogout}>
              Cerrar sesión
            </button>
          )}
        </header>
        <main className="app-main">
          <Outlet />
        </main>
      </div>

      <MobileNav unreadCount={unreadCount} />
    </div>
  );
}
