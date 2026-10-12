"""Parseo de extractos bancarios en CSV.

XLSX y PDF quedan fuera de este primer corte (igual que el mapeo manual de
columnas persistente por banco); si el archivo no encaja con los alias de
cabecera reconocidos, se rechaza con un error explícito en vez de adivinar.
"""

import csv
import io
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

DATE_ALIASES = {"fecha", "date", "fecha valor", "fecha operacion", "fecha operación"}
AMOUNT_ALIASES = {"importe", "amount", "importe (eur)", "importe eur"}
DEBIT_ALIASES = {"debe", "cargo", "debit"}
CREDIT_ALIASES = {"haber", "abono", "credit"}
DESCRIPTION_ALIASES = {
    "concepto",
    "descripcion",
    "descripción",
    "description",
    "detalle",
    "concepto/descripcion",
}
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y")


MAX_DESCRIPTION_LENGTH = 255


class StatementParseError(Exception):
    pass


@dataclass
class ParsedRow:
    posted_at: date
    amount: Decimal
    raw_description: str


def _normalize_header(header: str) -> str:
    return header.strip().lower()


def _parse_amount(raw: str) -> Decimal:
    cleaned = raw.strip().replace("€", "").replace(" ", "")
    if not cleaned:
        raise InvalidOperation("importe vacío")
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    return Decimal(cleaned)


def _parse_date(raw: str) -> date:
    raw = raw.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise StatementParseError(f"Fecha no reconocida: '{raw}'")


def _find_column(header_map: dict[str, str], aliases: set[str]) -> str | None:
    for alias in aliases:
        if alias in header_map:
            return header_map[alias]
    return None


def parse_csv(content: bytes) -> list[ParsedRow]:
    text = content.decode("utf-8-sig", errors="replace")
    sample = text[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,")
    except csv.Error:
        dialect = csv.excel
        dialect.delimiter = ";" if sample.count(";") > sample.count(",") else ","

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if not reader.fieldnames:
        raise StatementParseError("El archivo no tiene una cabecera reconocible")

    header_map = {_normalize_header(h): h for h in reader.fieldnames}
    date_col = _find_column(header_map, DATE_ALIASES)
    amount_col = _find_column(header_map, AMOUNT_ALIASES)
    debit_col = _find_column(header_map, DEBIT_ALIASES)
    credit_col = _find_column(header_map, CREDIT_ALIASES)
    desc_col = _find_column(header_map, DESCRIPTION_ALIASES)

    if (
        date_col is None
        or desc_col is None
        or (amount_col is None and not (debit_col or credit_col))
    ):
        raise StatementParseError(
            "No se reconocen las columnas de fecha/importe/descripción de este archivo. "
            "El mapeo manual de columnas todavía no está disponible."
        )

    rows: list[ParsedRow] = []
    for raw_row in reader:
        if not any((value or "").strip() for value in raw_row.values()):
            continue
        try:
            posted_at = _parse_date(raw_row[date_col])
            if amount_col:
                amount = _parse_amount(raw_row[amount_col])
            else:
                debit = (raw_row.get(debit_col) or "").strip() if debit_col else ""
                credit = (raw_row.get(credit_col) or "").strip() if credit_col else ""
                if debit:
                    amount = -abs(_parse_amount(debit))
                elif credit:
                    amount = abs(_parse_amount(credit))
                else:
                    continue
        except (InvalidOperation, StatementParseError) as exc:
            raise StatementParseError(f"Fila inválida ({raw_row}): {exc}") from exc

        if amount == 0:
            continue
        # Recortado al tamaño de la columna: un concepto largo del banco no debe
        # impedir importar el extracto entero.
        description = (raw_row.get(desc_col) or "").strip()[:MAX_DESCRIPTION_LENGTH]
        rows.append(ParsedRow(posted_at=posted_at, amount=amount, raw_description=description))

    if not rows:
        raise StatementParseError("El archivo no contiene movimientos válidos")
    return rows
