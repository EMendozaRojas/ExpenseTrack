from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.import_batch import ImportBatch

CLASSIFICATIONS = ("NEW", "EXACT_DUPLICATE", "PROBABLE_DUPLICATE")


class ImportRow(Base):
    """Fila en staging de un extracto subido, con su clasificación de
    duplicidad frente a los movimientos ya existentes en la cuenta."""

    __tablename__ = "import_rows"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id"), nullable=False)
    posted_at: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    raw_description: Mapped[str] = mapped_column(String(255), nullable=False)
    external_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    classification: Mapped[str] = mapped_column(String(20), nullable=False)
    matched_transaction_id: Mapped[int | None] = mapped_column(
        ForeignKey("transactions.id"), nullable=True
    )
    created_transaction_id: Mapped[int | None] = mapped_column(
        ForeignKey("transactions.id"), nullable=True
    )

    batch: Mapped["ImportBatch"] = relationship(back_populates="rows")
