"""Aritmética modular (Entregas 1 y 2).

Entrega 1: mcd, Euclides extendido, inverso modular y exponenciación rápida.
Entrega 2: exponenciación ingenua (solo para comparar en E3), exponenciación
por ventana deslizante (Algoritmo 1 del informe), cálculo de la ventana
óptima y conteo de operaciones con el parámetro opcional ``cont``.
"""
from __future__ import annotations

from .contador import Contador


def mcd(a: int, b: int, cont: Contador | None = None) -> int:
    """Máximo común divisor por el algoritmo de Euclides."""
    if cont is not None:
        cont.mcd += 1
    dividendo, divisor = abs(a), abs(b)
    while divisor != 0:
        residuo = dividendo % divisor
        if cont is not None:
            cont.div_mod += 1
            cont.iteraciones += 1
        dividendo = divisor
        divisor = residuo
    return dividendo


def mcm(a: int, b: int) -> int:
    """Mínimo común múltiplo (se usa en la función lambda de Carmichael)."""
    if a == 0 or b == 0:
        return 0
    return abs(a // mcd(a, b) * b)


def euclides_extendido(a: int, b: int,
                       cont: Contador | None = None) -> tuple[int, int, int]:
    """Devuelve (g, x, y) tal que a*x + b*y = g = mcd(a, b).

    Versión iterativa. Invariante: si a0, b0 son los valores iniciales,
        a0*x0 + b0*y0 = a   y   a0*x1 + b0*y1 = b   en cada iteración.
    """
    if a < 0 or b < 0:
        raise ValueError("euclides_extendido requiere a, b >= 0")
    if cont is not None:
        cont.mcd += 1

    coef_x_a, coef_x_b = 1, 0
    coef_y_a, coef_y_b = 0, 1

    while b != 0:
        cociente, residuo = divmod(a, b)
        if cont is not None:
            cont.div_mod += 1
            cont.iteraciones += 1
        a, b = b, residuo
        coef_x_a, coef_x_b = coef_x_b, coef_x_a - cociente * coef_x_b
        coef_y_a, coef_y_b = coef_y_b, coef_y_a - cociente * coef_y_b

    return a, coef_x_a, coef_y_a


def inverso_modular(a: int, m: int, cont: Contador | None = None) -> int:
    """Inverso de a módulo m (0 < resultado < m). Lanza ValueError si no existe."""
    if m < 2:
        raise ValueError("el módulo debe ser mayor que 1")

    divisor_comun, coeficiente, _ = euclides_extendido(a % m, m, cont)
    if divisor_comun != 1:
        raise ValueError(f"{a} no tiene inverso módulo {m} (mcd = {divisor_comun})")
    return coeficiente % m


def _validar_exp(exp: int, mod: int) -> None:
    if mod < 1:
        raise ValueError("el módulo debe ser positivo")
    if exp < 0:
        raise ValueError("el exponente debe ser no negativo")


def exp_modular_ingenua(base: int, exp: int, mod: int,
                        cont: Contador | None = None) -> int:
    """base^exp mod mod con exp multiplicaciones: O(e). Solo para comparar (E3)."""
    _validar_exp(exp, mod)
    if mod == 1:
        return 0
    base %= mod
    acumulado = 1
    for _ in range(exp):
        acumulado = (acumulado * base) % mod
        if cont is not None:
            cont.mult_mod += 1
            cont.iteraciones += 1
    return acumulado


def exp_modular_rapida(base: int, exp: int, mod: int,
                       cont: Contador | None = None) -> int:
    """base^exp mod mod por cuadrado y multiplicación (bits de derecha a izquierda).

    Costo: a lo más 2 * log2(exp) multiplicaciones modulares.
    """
    _validar_exp(exp, mod)
    if mod == 1:
        return 0

    acumulado = 1
    potencia = base % mod
    restante = exp

    while restante > 0:
        if cont is not None:
            cont.iteraciones += 1
        if restante % 2 == 1:            # bit actual = 1 -> multiplicar
            acumulado = (acumulado * potencia) % mod
            if cont is not None:
                cont.mult_mod += 1
        restante //= 2
        if restante > 0:                 # elevar al cuadrado para el siguiente bit
            potencia = (potencia * potencia) % mod
            if cont is not None:
                cont.mult_mod += 1

    return acumulado


def ventana_optima(bits: int, k_max: int = 8) -> int:
    """Ancho de ventana k que minimiza 2^(k-1) + bits / (k + 1).

    2^(k-1) es el costo de precalcular las potencias impares y bits/(k+1) es
    el número esperado de ventanas (multiplicaciones) en el recorrido.
    """
    if bits < 0:
        raise ValueError("bits debe ser no negativo")
    mejor_k, mejor_costo = 1, None
    for k in range(1, k_max + 1):
        costo = 2 ** (k - 1) + bits / (k + 1)
        if mejor_costo is None or costo < mejor_costo:
            mejor_k, mejor_costo = k, costo
    return mejor_k


def exp_modular_ventana(base: int, exp: int, mod: int, k: int | None = None,
                        cont: Contador | None = None) -> int:
    """base^exp mod mod por ventana deslizante de izquierda a derecha.

    Algoritmo 1 del informe (sección 1.2.1):
      1. Precalcular g^1, g^3, ..., g^(2^k - 1)  (potencias impares).
      2. Recorrer los bits de exp desde el más significativo:
         - bit 0: elevar al cuadrado y avanzar un bit;
         - bit 1: tomar la ventana más larga (<= k bits) que termina en 1,
           elevar al cuadrado tantas veces como su largo y multiplicar por
           la potencia impar precalculada.
    Si k es None se usa ventana_optima(exp.bit_length()).
    """
    _validar_exp(exp, mod)
    if k is None:
        k = ventana_optima(exp.bit_length())
    if not isinstance(k, int) or k < 1:
        raise ValueError("el ancho de ventana k debe ser un entero >= 1")
    if mod == 1:
        return 0
    if exp == 0:
        return 1

    def mul(a: int, b: int) -> int:
        if cont is not None:
            cont.mult_mod += 1
        return (a * b) % mod

    g = base % mod
    # Tabla de potencias impares: tabla[i] = g^(2i+1)
    tabla = [g]
    if k > 1:
        g2 = mul(g, g)
        for _ in range(2 ** (k - 1) - 1):
            tabla.append(mul(tabla[-1], g2))

    resultado = 1
    i = exp.bit_length() - 1
    primera = True                       # evita multiplicar 1 * 1 al inicio
    while i >= 0:
        if cont is not None:
            cont.iteraciones += 1
        if (exp >> i) & 1 == 0:
            if not primera:
                resultado = mul(resultado, resultado)
            i -= 1
            continue
        # Ventana [j, i] de largo <= k que termina en un bit 1
        j = max(i - k + 1, 0)
        while (exp >> j) & 1 == 0:
            j += 1
        largo = i - j + 1
        valor = (exp >> j) & ((1 << largo) - 1)   # impar
        if primera:
            resultado = tabla[valor >> 1]
            primera = False
        else:
            for _ in range(largo):
                resultado = mul(resultado, resultado)
            resultado = mul(resultado, tabla[valor >> 1])
        i = j - 1
    return resultado
