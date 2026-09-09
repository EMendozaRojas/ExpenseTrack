"""Abstracción de almacenamiento de archivos, fuera de la base de datos.

`LocalStorageBackend` guarda en disco (montado como volumen Docker en
`docker-compose.yml`). Migrar a S3/compatible más adelante implica escribir
otro backend con la misma interfaz, sin tocar los routers.
"""

import shutil
from pathlib import Path
from typing import BinaryIO, Protocol

from app.core.config import get_settings


class StorageBackend(Protocol):
    def save(self, key: str, content: BinaryIO) -> None: ...
    def open(self, key: str) -> BinaryIO: ...
    def delete(self, key: str) -> None: ...


class LocalStorageBackend:
    def __init__(self, base_dir: str | None = None) -> None:
        self._base_dir = Path(base_dir or get_settings().attachments_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, key: str) -> Path:
        # `key` siempre es un uuid4 hex generado por el servidor (ver
        # routers/attachments.py), nunca un nombre de archivo del usuario,
        # así que no puede contener separadores de ruta.
        return self._base_dir / key

    def save(self, key: str, content: BinaryIO) -> None:
        with self._path_for(key).open("wb") as destination:
            shutil.copyfileobj(content, destination)

    def open(self, key: str) -> BinaryIO:
        return self._path_for(key).open("rb")

    def delete(self, key: str) -> None:
        self._path_for(key).unlink(missing_ok=True)


_backend: LocalStorageBackend | None = None


def get_storage_backend() -> LocalStorageBackend:
    global _backend
    if _backend is None:
        _backend = LocalStorageBackend()
    return _backend
