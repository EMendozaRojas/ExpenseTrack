from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.category import Category
    from app.models.transaction import Transaction


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    # Nulo para usuarios dados de alta solo por login social (sin contraseña propia).
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Nulo hasta completar el onboarding (nombre obligatorio, foto opcional).
    full_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    avatar_storage_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    categories: Mapped[list["Category"]] = relationship(back_populates="owner")
    accounts: Mapped[list["Account"]] = relationship(back_populates="owner")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="owner")
