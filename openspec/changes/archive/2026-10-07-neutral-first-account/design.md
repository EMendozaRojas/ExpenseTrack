## Context

`POST /accounts/` exige `type` (`checking`, `savings`, `credit_card`, `cash`, `wallet`). El formulario "Crea tu primera cuenta" de Movimientos no pregunta el tipo y envía `cash`, con "Efectivo" como texto de ejemplo del nombre. No hay pantalla de cuentas (ver la conversación del 2026-10-07; es una posible ficha futura).

## Goals / Non-Goals

**Goals:** que la primera cuenta no tenga un tipo que el usuario no eligió, ni en la pantalla ni en los datos.

**Non-Goals:** pantalla de gestión de cuentas; cambiar las cuentas ya existentes; usar el tipo para algo en la app.

## Decisions

### D1 — Tipo `general` por defecto en vez de tipo nulo
- Se añade `general` a los tipos y `AccountCreate.type` pasa a ser opcional con valor por defecto `general`. La columna sigue siendo `NOT NULL`, así que no hace falta migración ni tocar las respuestas (`type` siempre tiene valor).
- Alternativa descartada: `type` nullable. Obliga a migrar la columna y a tratar `null` en todos los clientes.

### D2 — El frontend no envía el tipo
- `createAccount` deja de mandar `type`; el backend aplica el valor por defecto. El texto de ejemplo del nombre pasa a "Mi cuenta".

## Risks / Trade-offs

- [Cuentas existentes creadas como `cash` por la app] → se dejan como están; el tipo no se muestra ni se usa hoy.

## Migration Plan

Sin migración.

## Open Questions

(ninguna)
