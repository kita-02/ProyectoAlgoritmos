"""Ataque de factorización a RSA (Entrega 2). USO EDUCATIVO.

Dada una clave pública (n, e) con n pequeño, se factoriza n con
Pollard-Rho-Brent y se reconstruye la clave privada d = e^(-1) mod phi(n).
Muestra por qué el tamaño de n es la base de la seguridad de RSA.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from .aritmetica import inverso_modular, mcd
from .contador import Contador
from .factorizacion import factorizar


@dataclass(frozen=True)
class ClaveRota:
    n: int
    e: int
    p: int
    q: int
    phi: int
    d: int


def romper_clave(n: int, e: int, metodo: str = "brent",
                 rng: random.Random | None = None,
                 max_iter: int | None = None,
                 cont: Contador | None = None) -> ClaveRota:
    """Factoriza n = p*q y devuelve la clave privada reconstruida (p < q)."""
    if n < 6:
        raise ValueError("n debe ser el producto de dos primos distintos (n >= 6)")
    factores = factorizar(n, metodo, rng=rng, max_iter=max_iter, cont=cont)
    if len(factores) != 2 or factores[0] == factores[1]:
        raise ValueError(f"n = {n} no es producto de dos primos distintos: {factores}")
    p, q = factores
    phi = (p - 1) * (q - 1)
    if not (1 < e < phi) or mcd(e, phi) != 1:
        raise ValueError(f"e = {e} no es un exponente válido para phi(n) = {phi}")
    d = inverso_modular(e, phi)
    return ClaveRota(n, e, p, q, phi, d)
