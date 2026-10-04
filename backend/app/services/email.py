"""Envío de correo para notificaciones.

Sin proveedor real todavía: en local apunta a Mailhog (servicio
`mailhog` en docker-compose), que nunca entrega a internet y expone una
bandeja web en http://localhost:8025 para revisar lo enviado. Con
`smtp_host` vacío (default si no se configura) el envío queda deshabilitado
sin romper nada — así los tests no necesitan un servidor SMTP real.
"""

import smtplib
from email.message import EmailMessage

from app.core.config import get_settings


def send_email(to: str, subject: str, body: str) -> None:
    settings = get_settings()
    if not settings.smtp_host:
        return

    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=5) as server:
            server.send_message(message)
    except OSError:
        # Mejor esfuerzo: un correo que no sale no debe tumbar la petición
        # que lo disparó (crear un movimiento, una contribución, etc.).
        pass
