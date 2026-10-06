"""Pruebas de primalidad (Entrega 1).

* division_tentativa -> exacta, O(sqrt(n)) divisiones (candidatos 6k +- 1).
* miller_rabin       -> probabilística, error <= 4^(-rondas).

Pendiente para la Entrega 2: miller_rabin_determinista (12 bases fijas).
"""
from __future__ import annotations

import random
import secrets

from .aritmetica import exp_modular_rapida


def division_tentativa(n: int) -> bool:
    """Primalidad exacta probando 2, 3 y los candidatos 6k +- 1 hasta sqrt(n)."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def descomponer(n: int) -> tuple[int, int]:
    """Escribe n - 1 = 2^s * d con d impar. Devuelve (s, d)."""
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    return s, d


def es_testigo(a: int, s: int, d: int, n: int) -> bool:
    """True si la base a DEMUESTRA que n es compuesto."""
    x = exp_modular_rapida(a, d, n)
    if x == 1 or x == n - 1:
        return False
    for _ in range(s - 1):
        x = x * x % n
        if x == n - 1:
            return False
    return True


def miller_rabin(n: int, rondas: int = 20,
                 rng: random.Random | None = None) -> bool:
    """False si n es compuesto con certeza; True si es "probablemente primo".

    Las bases se eligen al azar en [2, n-2]. Con ``rng`` (p. ej.
    random.Random(2026)) la ejecución es reproducible.
    """
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False
    if rondas < 1:
        raise ValueError("se requiere al menos una ronda")
    rng = rng or secrets.SystemRandom()
    s, d = descomponer(n)
    for _ in range(rondas):
        a = rng.randint(2, n - 2)
        if es_testigo(a, s, d, n):
            return False
    return True
