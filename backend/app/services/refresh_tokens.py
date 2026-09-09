import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.refresh_token import RefreshToken


def _hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def issue_refresh_token(db: Session, user_id: int) -> str:
    settings = get_settings()
    raw_token = secrets.token_urlsafe(48)
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    db.add(RefreshToken(user_id=user_id, token_hash=_hash(raw_token), expires_at=expires_at))
    db.commit()
    return raw_token


def get_valid_refresh_token(db: Session, raw_token: str) -> RefreshToken | None:
    record = db.query(RefreshToken).filter(RefreshToken.token_hash == _hash(raw_token)).first()
    if record is None:
        return None
    if record.revoked_at is not None:
        return None
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at < datetime.now(UTC):
        return None
    return record


def revoke_refresh_token(db: Session, record: RefreshToken) -> None:
    record.revoked_at = datetime.now(UTC)
    db.commit()
