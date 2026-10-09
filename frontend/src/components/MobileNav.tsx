import { useEffect, useState } from "react";
import { NavLink, matchPath, useLocation } from "react-router";

import { NAV_ITEMS, NOTIFICATIONS_PATH } from "./navItems";

interface MobileNavProps {
  unreadCount: number;
}

const BAR_ITEMS = NAV_ITEMS.filter((item) => item.mobile === "bar");
const MORE_ITEMS = NAV_ITEMS.filter((item) => item.mobile === "more");
const MORE_PANEL_ID = "mobile-nav-more";

function navLinkClassName({ isActive }: { isActive: boolean }): string {
  return isActive ? "mobile-nav-item mobile-nav-active" : "mobile-nav-item";
}

/** Navegación del móvil: barra fija abajo con las secciones principales y
 * un botón «Más» que abre un panel con el resto. Solo se ve en pantallas
 * estrechas (lo decide el CSS). */
export function MobileNav({ unreadCount }: MobileNavProps) {
  const [moreOpen, setMoreOpen] = useState(false);
  const { pathname } = useLocation();
  const moreIsActive = MORE_ITEMS.some((item) => matchPath(item.to, pathname) !== null);

  useEffect(() => {
    if (!moreOpen) return;
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setMoreOpen(false);
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [moreOpen]);

  const closeMore = () => setMoreOpen(false);

  return (
    <div className="mobile-nav">
      {moreOpen && (
        <>
          <button
            type="button"
            className="mobile-nav-backdrop"
            aria-label="Cerrar más opciones"
            onClick={closeMore}
          />
          <div
            id={MORE_PANEL_ID}
            className="mobile-nav-sheet"
            role="dialog"
            aria-label="Más opciones"
          >
            <span className="mobile-nav-sheet-handle" aria-hidden="true" />
            {MORE_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  isActive ? "mobile-nav-sheet-item mobile-nav-active" : "mobile-nav-sheet-item"
                }
                onClick={closeMore}
              >
                <span className="app-nav-icon" aria-hidden="true">
                  {item.icon}
                </span>
                <span className="mobile-nav-sheet-label">{item.label}</span>
                {item.to === NOTIFICATIONS_PATH && unreadCount > 0 && (
                  <span className="app-nav-badge">{unreadCount}</span>
                )}
              </NavLink>
            ))}
          </div>
        </>
      )}

      <nav className="mobile-nav-bar" aria-label="Menú principal">
        {BAR_ITEMS.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.end} className={navLinkClassName}>
            <span className="app-nav-icon" aria-hidden="true">
              {item.icon}
            </span>
            {item.label}
          </NavLink>
        ))}
        <button
          type="button"
          className={
            moreIsActive || moreOpen ? "mobile-nav-item mobile-nav-active" : "mobile-nav-item"
          }
          aria-expanded={moreOpen}
          aria-controls={MORE_PANEL_ID}
          aria-label={unreadCount > 0 ? `Más (${unreadCount} notificaciones sin leer)` : "Más"}
          onClick={() => setMoreOpen((open) => !open)}
        >
          <span className="app-nav-icon mobile-nav-more-icon" aria-hidden="true">
            ⋯
          </span>
          Más
          {unreadCount > 0 && (
            <span className="app-nav-badge mobile-nav-badge" aria-hidden="true">
              {unreadCount}
            </span>
          )}
        </button>
      </nav>
    </div>
  );
}
