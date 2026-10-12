## 1. Contraseña

- [ ] 1.1 `UserCreate`: máximo de 72 bytes en UTF-8 con mensaje claro
- [ ] 1.2 `RegisterPage`: misma regla en bytes, sin `maxLength` en el input

## 2. Extractos

- [ ] 2.1 `parse_csv`: recortar los conceptos a 255 caracteres

## 3. Tests

- [ ] 3.1 Backend: 72 «ñ» → 422; 36 «ñ» → 201; CSV con un concepto de 300 caracteres se importa recortado
- [ ] 3.2 Frontend: contraseña de más de 72 bytes avisa antes de enviar

## 4. Verificación

- [ ] 4.1 `pre-commit run --all-files`, `pytest` y `vitest` en verde; CI en verde tras el push
