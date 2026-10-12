## 1. Contraseña

- [x] 1.1 `UserCreate`: máximo de 72 bytes en UTF-8 con mensaje claro
- [x] 1.2 `RegisterPage`: misma regla en bytes, sin `maxLength` en el input

## 2. Extractos

- [x] 2.1 `parse_csv`: recortar los conceptos a 255 caracteres

## 3. Tests

- [x] 3.1 Backend: 72 «ñ» → 422; 36 «ñ» → 201; CSV con un concepto de 300 caracteres se importa recortado
- [x] 3.2 Frontend: contraseña de más de 72 bytes avisa antes de enviar

## 4. Verificación

- [x] 4.1 `pre-commit run --all-files`, `pytest` y `vitest` en verde; CI en verde tras el push
