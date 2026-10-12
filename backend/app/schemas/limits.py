"""Límites compartidos de los datos de entrada.

Los importes se guardan en columnas `Numeric(14, 2)`: el máximo que cabe es
999.999.999.999,99. Acotarlos en el schema hace que un valor fuera de rango
dé 422 con el campo señalado, en vez de un 500 al guardarlo.
"""

from decimal import Decimal

MAX_AMOUNT = Decimal("1000000000000")
