"""Aritmética modular (Entrega 1).

Contiene el algoritmo de Euclides (simple y extendido), el inverso modular
y la exponenciación modular rápida (cuadrado y multiplicación).

Pendiente para la Entrega 2: exp_modular_ingenua (solo sirve para comparar)
y el contador de operaciones.
"""
from __future__ import annotations


def mcd(a: int, b: int) -> int:
    """Máximo común divisor por el algoritmo de Euclides."""
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def euclides_extendido(a: int, b: int) -> tuple[int, int, int]:
    """Devuelve (g, x, y) tal que a*x + b*y = g = mcd(a, b).

    Versión iterativa. Invariante: si a0, b0 son los valores iniciales,
        a0*x0 + b0*y0 = a   y   a0*x1 + b0*y1 = b   en cada iteración.
    """
    if a < 0 or b < 0:
        raise ValueError("euclides_extendido requiere a, b >= 0")
    x0, x1, y0, y1 = 1, 0, 0, 1
    while b:
        q = a // b
        a, b = b, a - q * b
        x0, x1 = x1, x0 - q * x1
        y0, y1 = y1, y0 - q * y1
    return a, x0, y0


def inverso_modular(a: int, m: int) -> int:
    """Inverso de a módulo m (0 < resultado < m). Lanza ValueError si no existe."""
    if m <= 1:
        raise ValueError("el módulo debe ser mayor que 1")
    g, x, _ = euclides_extendido(a % m, m)
    if g != 1:
        raise ValueError(f"{a} no tiene inverso módulo {m} (mcd = {g})")
    return x % m


def exp_modular_rapida(base: int, exp: int, mod: int) -> int:
    """base^exp mod mod por cuadrado y multiplicación (bits de derecha a izquierda)."""
    if mod <= 0:
        raise ValueError("el módulo debe ser positivo")
    if exp < 0:
        raise ValueError("el exponente debe ser no negativo")
    if mod == 1:
        return 0
    resultado = 1
    base %= mod
    while exp > 0:
        if exp & 1:                      # bit actual = 1 -> multiplicar
            resultado = resultado * base % mod
        exp >>= 1
        if exp:                          # elevar al cuadrado para el siguiente bit
            base = base * base % mod
    return resultado
