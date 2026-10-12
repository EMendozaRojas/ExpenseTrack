from unittest.mock import MagicMock, patch

from app.services.email import send_email


def test_send_email_noop_without_smtp_host() -> None:
    with (
        patch("app.services.email.get_settings") as mock_settings,
        patch("smtplib.SMTP") as mock_smtp,
    ):
        mock_settings.return_value.smtp_host = ""
        send_email("user@example.com", "Asunto", "Cuerpo")
        mock_smtp.assert_not_called()


def test_send_email_sends_via_smtp_when_configured() -> None:
    with (
        patch("app.services.email.get_settings") as mock_settings,
        patch("smtplib.SMTP") as mock_smtp,
    ):
        mock_settings.return_value.smtp_host = "mailhog"
        mock_settings.return_value.smtp_port = 1025
        mock_settings.return_value.smtp_from = "notificaciones@expensetrack.local"
        server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = server

        send_email("user@example.com", "Asunto", "Cuerpo")

        mock_smtp.assert_called_once_with("mailhog", 1025, timeout=5)
        server.send_message.assert_called_once()
        sent_message = server.send_message.call_args[0][0]
        assert sent_message["To"] == "user@example.com"
        assert sent_message["Subject"] == "Asunto"


def test_send_email_swallows_connection_errors() -> None:
    with (
        patch("app.services.email.get_settings") as mock_settings,
        patch("smtplib.SMTP", side_effect=OSError("conexión rechazada")),
    ):
        mock_settings.return_value.smtp_host = "mailhog"
        mock_settings.return_value.smtp_port = 1025
        mock_settings.return_value.smtp_from = "notificaciones@expensetrack.local"

        send_email("user@example.com", "Asunto", "Cuerpo")
