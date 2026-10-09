## 1. Formularios

- [x] 1.1 `TransactionForm`: pintar «Cuenta» solo con más de una cuenta
- [x] 1.2 `ImportsPage`: con una sola cuenta, elegirla automáticamente y no pintar «Cuenta»; con varias, sin cambios

## 2. Tests

- [x] 2.1 `TransactionForm`: sin campo «Cuenta» con una cuenta y el movimiento se guarda en ella; con dos, el campo aparece
- [x] 2.2 `ImportsPage`: con una cuenta, sin campo y se puede subir sin elegir; con dos, aparece «Selecciona una cuenta»

## 3. Datos del demo

- [x] 3.1 Copia de seguridad; traspasar los movimientos de «Cuenta Secundaria» a «Cuenta Principal» y eliminar la secundaria (usuario demo); comprobar que las cifras del dashboard no cambian

## 4. Verificación

- [x] 4.1 `tsc`, `eslint` y `vitest` en verde; Prettier sin avisos en los archivos tocados
- [ ] 4.2 Revisión en el navegador con el usuario demo: dashboard sin selector, formularios sin «Cuenta»; revisión de la autora
