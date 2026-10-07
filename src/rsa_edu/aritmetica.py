"""Aritmética modular necesaria para la entrega 1.

Contiene el algoritmo de Euclides (simple y extendido), el inverso modular
y la exponenciación modular rápida (cuadrado y multiplicación).

Posteriormente se implementará: exp_modular_ingenua (solo sirve para comparar)
y el contador de operaciones.
"""
from __future__ import annotations


def mcd(a: int, b: int) -> int:
    """Máximo común divisor por el algoritmo de Euclides."""
    dividendo, divisor = abs(a), abs(b)
    while divisor != 0:
        residuo = dividendo % divisor
        dividendo = divisor
        divisor = residuo
    return dividendo


def euclides_extendido(a: int, b: int) -> tuple[int, int, int]:
    """Devuelve (g, x, y) tal que a*x + b*y = g = mcd(a, b).

    Versión iterativa. Invariante: si a0, b0 son los valores iniciales,
        a0*x0 + b0*y0 = a   y   a0*x1 + b0*y1 = b   en cada iteración.
    """
    if a < 0 or b < 0:
        raise ValueError("euclides_extendido requiere a, b >= 0")

    # Coeficientes de Bézout asociados a (a, b) respectivamente
    coef_x_a, coef_x_b = 1, 0
    coef_y_a, coef_y_b = 0, 1

    while b != 0:
        cociente, residuo = divmod(a, b)
        a, b = b, residuo
        coef_x_a, coef_x_b = coef_x_b, coef_x_a - cociente * coef_x_b
        coef_y_a, coef_y_b = coef_y_b, coef_y_a - cociente * coef_y_b

    return a, coef_x_a, coef_y_a


def inverso_modular(a: int, m: int) -> int:
    """Inverso de a módulo m (0 < resultado < m). Lanza ValueError si no existe."""
    if m < 2:
        raise ValueError("el módulo debe ser mayor que 1")

    divisor_comun, coeficiente, _ = euclides_extendido(a % m, m)
    if divisor_comun != 1:
        raise ValueError(f"{a} no tiene inverso módulo {m} (mcd = {divisor_comun})")
    return coeficiente % m


def exp_modular_rapida(base: int, exp: int, mod: int) -> int:
    """base^exp mod mod por cuadrado y multiplicación (bits de derecha a izquierda)."""
    if mod < 1:
        raise ValueError("el módulo debe ser positivo")
    if exp < 0:
        raise ValueError("el exponente debe ser no negativo")
    if mod == 1:
        return 0

    acumulado = 1
    potencia = base % mod
    restante = exp

    while restante > 0:
        if restante % 2 == 1:            # bit actual = 1 -> multiplicar
            acumulado = (acumulado * potencia) % mod
        restante //= 2
        if restante > 0:                 # elevar al cuadrado para el siguiente bit
            potencia = (potencia * potencia) % mod

    return acumulado