/** Secciones de la app. Una sola lista para el menú lateral (ordenador) y
 * la barra inferior (móvil): `mobile` decide si en el móvil van en la barra
 * o dentro del panel «Más». */
export interface NavItem {
  to: string;
  end?: boolean;
  icon: string;
  label: string;
  mobile: "bar" | "more";
}

export const NAV_ITEMS: NavItem[] = [
  { to: "/", end: true, icon: "📊", label: "Estadísticas", mobile: "bar" },
  { to: "/transactions", icon: "💸", label: "Movimientos", mobile: "bar" },
  { to: "/budgets", icon: "🎯", label: "Presupuestos", mobile: "bar" },
  { to: "/goals", icon: "🏁", label: "Metas", mobile: "bar" },
  { to: "/insights", icon: "💡", label: "Análisis", mobile: "more" },
  { to: "/notifications", icon: "🔔", label: "Notificaciones", mobile: "more" },
  { to: "/settings", icon: "⚙️", label: "Configuración", mobile: "more" },
];

export const NOTIFICATIONS_PATH = "/notifications";
