"""normalize user emails (sin espacios y en minúsculas)

Desde el change `input-validation-limits` los emails se guardan y se comparan
en minúsculas. Esta migración normaliza los que ya existían. Si dos cuentas
solo se distinguen por mayúsculas, se detiene y las lista: fusionar cuentas
es una decisión manual, no algo que deba hacer una migración.

Revision ID: f1a6c2e8b4d7
Revises: e5a2b7c9d1f3
Create Date: 2026-10-12 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = 'f1a6c2e8b4d7'
down_revision: str | None = 'e5a2b7c9d1f3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    conflicts = bind.execute(
        sa.text(
            """
            SELECT lower(trim(email)) AS normalized, string_agg(email, ', ' ORDER BY id) AS emails
            FROM users
            GROUP BY lower(trim(email))
            HAVING count(*) > 1
            """
        )
    ).all()
    if conflicts:
        listed = "; ".join(row.emails for row in conflicts)
        raise RuntimeError(
            f"Hay cuentas cuyo email solo se distingue por mayúsculas: {listed}. "
            "Fusiónalas o renómbralas a mano antes de migrar."
        )
    bind.execute(sa.text("UPDATE users SET email = lower(trim(email)) WHERE email <> lower(trim(email))"))
    bind.execute(
        sa.text(
            "UPDATE auth_identities SET email = lower(trim(email)) "
            "WHERE email <> lower(trim(email))"
        )
    )


def downgrade() -> None:
    # Sin vuelta atrás de datos: la forma original de cada email no se guardó.
    pass
