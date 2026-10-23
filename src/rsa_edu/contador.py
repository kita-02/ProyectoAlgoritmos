"""Contador de operaciones elementales (Entrega 2).

Acumula multiplicaciones modulares, divisiones (residuos), llamadas a mcd e
iteraciones para medir el costo de cada algoritmo sin depender del hardware.

Se pasa como parámetro opcional ``cont`` a las funciones de la biblioteca.
Si ``cont`` es None no se cuenta nada, de modo que el contador no altera el
resultado ni (de forma apreciable) el tiempo de ejecución.

Diseño: informe/entrega1.tex, sección 7.3 (Estructuras de datos).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class Contador:
    """Contadores de operaciones elementales."""

    mult_mod: int = 0      # productos (a * b) % m
    div_mod: int = 0       # divisiones / residuos (a % b, divmod)
    mcd: int = 0           # llamadas a mcd
    iteraciones: int = 0   # iteraciones del bucle principal del algoritmo

    def reiniciar(self) -> None:
        self.mult_mod = self.div_mod = self.mcd = self.iteraciones = 0

    def total(self) -> int:
        """Total de operaciones aritméticas (mult_mod + div_mod)."""
        return self.mult_mod + self.div_mod

    def como_dict(self) -> dict[str, int]:
        return asdict(self)

    def __iadd__(self, otro: "Contador") -> "Contador":
        self.mult_mod += otro.mult_mod
        self.div_mod += otro.div_mod
        self.mcd += otro.mcd
        self.iteraciones += otro.iteraciones
        return self
