type BrandMarkVariant = "sidebar" | "topbar" | "hero";

interface BrandMarkProps {
  variant: BrandMarkVariant;
}

/** Mascota de ExpenseTrack con el nombre escrito al lado (o debajo).
 * La imagen es decorativa (`alt=""`) porque el nombre ya va como texto.
 * `hero` (inicio de sesión) añade el lema. */
export function BrandMark({ variant }: BrandMarkProps) {
  return (
    <div className={`brand-mark brand-mark-${variant}`}>
      <img className="brand-mark-mascot" src="/mascota.png" alt="" />
      <span className="brand-mark-name">
        Expense<span className="brand-mark-accent">Track</span>
      </span>
      {variant === "hero" && <span className="brand-mark-slogan">Tus gastos, siempre contigo</span>}
    </div>
  );
}
