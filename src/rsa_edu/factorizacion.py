"""Factorización entera (Entregas 1 y 2).

* factorizar_tentativa -> exacta, O(sqrt(n)) divisiones en el peor caso.
* pollard_rho          -> probabilística (ciclos de Floyd), O(n^(1/4)) esperado.
* pollard_rho_brent    -> variante de Brent con lotes de L = 128 productos:
                          un solo mcd por lote (Algoritmo 3 del informe).
* factorizar           -> factorización completa con cualquiera de los tres.
"""
from __future__ import annotations

import random
import secrets
from math import isqrt

from .aritmetica import mcd
from .contador import Contador
from .primalidad import es_primo

METODOS = ("tentativa", "rho", "brent")


def factorizar_tentativa(n: int, cont: Contador | None = None) -> list[int]:
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
        if cont is not None:
            cont.iteraciones += 1
            cont.div_mod += 2
        for c in (i, i + 2):
            while n % c == 0:
                factores.append(c)
                n //= c
        i += 6
    if n > 1:
        factores.append(n)          # el cofactor que queda es primo
    return factores


def _validar_compuesto(n: int, nombre: str) -> None:
    if n < 4:
        raise ValueError(f"{nombre} requiere n >= 4 compuesto")


def _factor_trivial(n: int) -> int | None:
    """Casos en que rho falla o es innecesario: n par o n cuadrado perfecto.

    Si n = r^2, la sucesión x^2 + c tiene el mismo período módulo r y
    módulo n con alta frecuencia (mcd = n), por eso se detecta aparte.
    """
    if n % 2 == 0:
        return 2
    r = isqrt(n)
    return r if r * r == n else None


def pollard_rho(n: int, rng: random.Random | None = None,
                max_reintentos: int = 20,
                max_iter: int | None = None,
                cont: Contador | None = None) -> int:
    """Devuelve un factor no trivial de n (compuesto).

    f(x) = x^2 + c mod n; tortuga x avanza 1 paso y liebre y avanza 2.
    Si el mcd resulta n, se reinicia con otros (x0, c).
    ``max_iter`` limita las iteraciones de cada intento (None = sin límite);
    si se agota el límite o los reintentos se lanza RuntimeError informativo.
    """
    _validar_compuesto(n, "pollard_rho")
    trivial = _factor_trivial(n)
    if trivial is not None:
        return trivial
    rng = rng or secrets.SystemRandom()
    for _ in range(max_reintentos):
        c = rng.randrange(1, n - 2)          # evita c = 0 y c = -2
        x = y = rng.randrange(0, n)
        d, it = 1, 0
        while d == 1:
            x = (x * x + c) % n
            y = (y * y + c) % n
            y = (y * y + c) % n
            d = mcd(x - y, n, cont)
            it += 1
            if cont is not None:
                cont.mult_mod += 3
                cont.iteraciones += 1
            if max_iter is not None and it >= max_iter and d == 1:
                raise RuntimeError(
                    f"pollard_rho: se agotaron max_iter = {max_iter} iteraciones "
                    f"sin hallar un factor de n = {n}")
        if d != n:
            return d
    raise RuntimeError(f"pollard_rho: no se halló un factor de n = {n} "
                       f"en {max_reintentos} reintentos (¿n es primo?)")


def pollard_rho_brent(n: int, rng: random.Random | None = None,
                      lote: int = 128, max_reintentos: int = 20,
                      max_iter: int | None = None,
                      cont: Contador | None = None) -> int:
    """Variante de Brent de Pollard Rho (Algoritmo 3 del informe).

    * Detección de ciclos de Brent: y se fija en potencias de 2 (r = 1, 2, 4, ...)
      y x avanza r pasos; se evalúa f una vez por paso (Floyd evalúa 3).
    * En lugar de un mcd por paso se acumula q = prod |x - y| mod n en lotes
      de ``lote`` pasos y se calcula un solo mcd(q, n) por lote.
    * Si el mcd del lote da n (se saltó el factor) se retrocede paso a paso
      desde el inicio del lote (backtracking) con mcd individuales.
    """
    _validar_compuesto(n, "pollard_rho_brent")
    if lote < 1:
        raise ValueError("el tamaño de lote debe ser >= 1")
    trivial = _factor_trivial(n)
    if trivial is not None:
        return trivial
    rng = rng or secrets.SystemRandom()

    def mul(a: int, b: int) -> int:
        if cont is not None:
            cont.mult_mod += 1
        return a * b % n

    for _ in range(max_reintentos):
        y = rng.randrange(1, n)
        c = rng.randrange(1, n - 2)
        g, r, q = 1, 1, 1
        it = 0
        x = ys = y
        while g == 1:
            x = y
            for _ in range(r):
                y = (mul(y, y) + c) % n
            k = 0
            while k < r and g == 1:
                ys = y
                for _ in range(min(lote, r - k)):
                    y = (mul(y, y) + c) % n
                    q = mul(q, abs(x - y))
                    it += 1
                    if cont is not None:
                        cont.iteraciones += 1
                g = mcd(q, n, cont)
                k += lote
                if max_iter is not None and it >= max_iter and g == 1:
                    raise RuntimeError(
                        f"pollard_rho_brent: se agotaron max_iter = {max_iter} "
                        f"iteraciones sin hallar un factor de n = {n}")
            r *= 2
        if g == n:                                   # backtracking
            g = 1
            while g == 1:
                ys = (mul(ys, ys) + c) % n
                g = mcd(abs(x - ys), n, cont)
        if g != n:
            return g
    raise RuntimeError(f"pollard_rho_brent: no se halló un factor de n = {n} "
                       f"en {max_reintentos} reintentos (¿n es primo?)")


def factorizar(n: int, metodo: str = "rho",
               rng: random.Random | None = None,
               max_iter: int | None = None,
               cont: Contador | None = None) -> list[int]:
    """Factorización completa y ordenada. metodo = "tentativa" | "rho" | "brent"."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("n debe ser un entero")
    if n < 1:
        raise ValueError("n debe ser un entero positivo")
    if metodo not in METODOS:
        raise ValueError(f"método desconocido: {metodo} (use {', '.join(METODOS)})")
    if metodo == "tentativa":
        return factorizar_tentativa(n, cont)
    buscar = pollard_rho if metodo == "rho" else pollard_rho_brent
    factores: list[int] = []
    pila = [n]                               # pila explícita en vez de recursión
    while pila:
        m = pila.pop()
        if m == 1:
            continue
        if es_primo(m, rng=rng):
            factores.append(m)
            continue
        d = buscar(m, rng=rng, max_iter=max_iter, cont=cont)
        pila.extend((d, m // d))
    return sorted(factores)
