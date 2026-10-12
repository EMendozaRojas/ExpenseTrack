"""Tipo real de un archivo según sus primeros bytes («firma» o *magic bytes*).

El `Content-Type` de una subida lo decide el navegador o quien hace la
petición, así que no basta para fiarse: un HTML puede declararse como
`image/png`. Solo hay cuatro tipos admitidos, por lo que se reconocen a mano
en vez de depender de `libmagic`.
"""

from urllib.parse import quote

_SIGNATURES: list[tuple[bytes, str]] = [
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"%PDF-", "application/pdf"),
]

MAX_FILENAME_LENGTH = 255


def detect_mime(content: bytes) -> str | None:
    """Devuelve el tipo detectado (`image/jpeg`, `image/png`, `image/webp` o
    `application/pdf`), o `None` si no es ninguno de ellos."""
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    for signature, mime_type in _SIGNATURES:
        if content.startswith(signature):
            return mime_type
    return None


def safe_filename(filename: str | None, default: str = "adjunto") -> str:
    """Nombre sin rutas y de como mucho 255 caracteres, conservando la extensión."""
    name = (filename or "").replace("\\", "/").rsplit("/", 1)[-1].strip() or default
    if len(name) <= MAX_FILENAME_LENGTH:
        return name
    base, dot, extension = name.rpartition(".")
    if not dot or len(extension) > 10:
        return name[:MAX_FILENAME_LENGTH]
    return base[: MAX_FILENAME_LENGTH - len(extension) - 1] + "." + extension


def content_disposition(filename: str) -> str:
    """Cabecera `Content-Disposition: inline` válida para cualquier nombre
    (RFC 6266): una versión ASCII sin comillas para clientes antiguos y el
    nombre real codificado en `filename*`."""
    ascii_name = filename.encode("ascii", "replace").decode("ascii")
    ascii_name = ascii_name.replace('"', "").replace("\\", "").replace("?", "_")
    return f"inline; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename, safe='')}"
