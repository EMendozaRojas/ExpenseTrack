"""Guarda: los tests nunca usan la base de desarrollo ni envían correo."""

from sqlalchemy.engine import make_url

from app.core.config import get_settings


def test_tests_use_their_own_database() -> None:
    database = make_url(get_settings().database_url).database or ""
    assert database.endswith("_test"), (
        f"Los tests apuntan a '{database}': deben usar una base terminada en _test "
        "(lo fija tests/conftest.py antes de importar la app)."
    )


def test_tests_do_not_send_email() -> None:
    assert get_settings().smtp_host == "", "El SMTP debe estar desactivado durante los tests."
