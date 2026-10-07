"""Factorización entera (Entrega 1).

* factorizar_tentativa -> exacta, O(sqrt(n)) divisiones en el peor caso.
* pollard_rho          -> probabilística (ciclos de Floyd), O(n^(1/4)) esperado.
* factorizar           -> factorización completa con cualquiera de los dos.
"""
from __future__ import annotations

import random
import secrets

from .aritmetica import mcd
from .primalidad import miller_rabin


def factorizar_tentativa(n: int) -> list[int]:
    """Factorización completa y ordenada por división de prueba (2, 3 y 6k +- 1)."""
    if n < 1:
        raise ValueError("n debe ser un entero positivo")
    factores: list[int] = []
    for p in (2, 3):
        while n % p == 0:
            factores.append(p)
            n //= p
    i = 5
    while i * i <= n:
        for c in (i, i + 2):
            while n % c == 0:
                factores.append(c)
                n //= c
        i += 6
    if n > 1:
        factores.append(n)          # el cofactor que queda es primo
    return factores


def pollard_rho(n: int, rng: random.Random | None = None,
                max_reintentos: int = 20,
                max_iter: int | None = None) -> int | None:
    """Devuelve un factor no trivial de n (compuesto) o None si no lo halla.

    f(x) = x^2 + c mod n; tortuga x avanza 1 paso y liebre y avanza 2.
    Si el mcd resulta n, se reinicia con otros (x0, c).
    ``max_iter`` limita las iteraciones de cada intento (None = sin límite).
    """
    if n < 4:
        raise ValueError("pollard_rho requiere n >= 4 compuesto")
    if n % 2 == 0:
        return 2
    rng = rng or secrets.SystemRandom()
    for _ in range(max_reintentos):
        c = rng.randrange(1, n - 2)          # evita c = 0 y c = -2
        x = y = rng.randrange(0, n)
        d, it = 1, 0
        while d == 1:
            x = (x * x + c) % n
            y = (y * y + c) % n
            y = (y * y + c) % n
            d = mcd(x - y, n)
            it += 1
            if max_iter is not None and it >= max_iter:
                return None              # límite agotado: se informa, no se cuelga
        if d != n:
            return d
    return None


def factorizar(n: int, metodo: str = "rho",
               rng: random.Random | None = None,
               max_iter: int | None = None) -> list[int]:
    """Factorización completa y ordenada. metodo = "tentativa" | "rho"."""
    if n < 1:
        raise ValueError("n debe ser un entero positivo")
    if metodo == "tentativa":
        return factorizar_tentativa(n)
    if metodo != "rho":
        raise ValueError(f"método desconocido: {metodo}")
    factores: list[int] = []
    pila = [n]                               # pila explícita en vez de recursión
    while pila:
        m = pila.pop()
        if m == 1:
            continue
        if miller_rabin(m, rng=rng):
            factores.append(m)
            continue
        d = pollard_rho(m, rng=rng, max_iter=max_iter)
        if d is None:
            raise RuntimeError(f"Pollard Rho no halló un factor de {m} "
                               f"dentro del límite de iteraciones")
        pila.extend((d, m // d))
    return sorted(factores)
