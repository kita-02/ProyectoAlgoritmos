"""Tests de primalidad correspondientes a la Entrega 1.

Se incluyen dos métodos:

* division_tentativa: determinista y exacto. Realiza O(sqrt(n)) divisiones,
  probando solo los candidatos de la forma 6k - 1 y 6k + 1.
* miller_rabin: probabilístico. La probabilidad de declarar primo a un
  compuesto es a lo más 4^(-rondas).

Queda para la Entrega 2: miller_rabin_determinista (con 12 bases fijas).
"""
from __future__ import annotations

import random
import secrets

from .aritmetica import exp_modular_rapida


def division_tentativa(n: int) -> bool:
    """Decide de forma exacta si n es primo.

    Se descartan primero los múltiplos de 2 y de 3; luego basta probar los
    divisores 6k - 1 y 6k + 1 mientras no superen sqrt(n).
    """
    # Casos base: 0, 1 y negativos no son primos; 2 y 3 sí lo son
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False

    # Todo primo mayor que 3 es de la forma 6k - 1 o 6k + 1
    candidato = 5
    while candidato * candidato <= n:
        if n % candidato == 0 or n % (candidato + 2) == 0:
            return False
        candidato += 6
    return True


def descomponer(n: int) -> tuple[int, int]:
    """Factoriza n - 1 como 2^s * d, con d impar, y devuelve el par (s, d)."""
    d, s = n - 1, 0
    # Se extraen los factores 2 de n - 1 uno por uno
    while d % 2 == 0:
        d //= 2
        s += 1
    return s, d


def es_testigo(a: int, s: int, d: int, n: int) -> bool:
    """Indica si la base a es testigo de que n es compuesto.

    Devuelve True cuando a PRUEBA que n no es primo, y False cuando n pasa
    la prueba para esa base (n es primo o a es un "mentiroso fuerte").
    """
    x = exp_modular_rapida(a, d, n)
    # Primera condición: a^d = 1 o a^d = -1 (mod n)
    if x == 1 or x == n - 1:
        return False
    # Segunda condición: algún a^(2^r * d) = -1 (mod n), con 0 < r < s
    for _ in range(s - 1):
        x = x * x % n
        if x == n - 1:
            return False
    return True


def miller_rabin(n: int, rondas: int = 20,
                 rng: random.Random | None = None) -> bool:
    """Test de Miller-Rabin con bases aleatorias.

    Devuelve False si n es compuesto (resultado seguro) y True si n es
    "probablemente primo".

    En cada ronda se toma una base al azar en el intervalo [2, n-2]. Si se
    pasa un generador en ``rng`` (por ejemplo random.Random(2026)), el
    resultado se puede reproducir.
    """
    # Casos triviales que no necesitan el test
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False
    if rondas < 1:
        raise ValueError("se requiere al menos una ronda")

    # Sin generador explícito se usa uno criptográficamente seguro
    rng = rng or secrets.SystemRandom()
    s, d = descomponer(n)
    for _ in range(rondas):
        a = rng.randint(2, n - 2)
        if es_testigo(a, s, d, n):
            return False
    return True
