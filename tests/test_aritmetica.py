"""Casos A1-A8: mcd, Euclides extendido, inverso, exponenciaciones y contador."""
from __future__ import annotations

import math

import pytest

from rsa_edu.aritmetica import (euclides_extendido, exp_modular_ingenua,
                                exp_modular_rapida, exp_modular_ventana,
                                inverso_modular, mcd, mcm, ventana_optima)
from rsa_edu.contador import Contador

MOD64 = 18446744073709551557   # primo de 64 bits usado en E3


# A1 - mcd contra math.gcd (básicos, con cero y negativos)
@pytest.mark.parametrize("a,b", [(0, 0), (0, 7), (7, 0), (12, 18), (17, 31),
                                 (-12, 18), (2 ** 64, 2 ** 32 * 3), (3120, 17)])
def test_A1_mcd(a, b):
    assert mcd(a, b) == math.gcd(a, b)


def test_A1_mcm():
    assert mcm(60, 52) == 780 and mcm(0, 5) == 0


# A2 - Euclides extendido: identidad de Bézout y traza manual (17, 3120)
@pytest.mark.parametrize("a,b", [(17, 3120), (240, 46), (0, 5), (5, 0), (1, 1),
                                 (2 ** 61 - 1, 2 ** 31 - 1)])
def test_A2_bezout(a, b):
    g, x, y = euclides_extendido(a, b)
    assert g == math.gcd(a, b) and a * x + b * y == g


def test_A2_traza_manual():
    g, x, y = euclides_extendido(3120, 17)
    assert (g, x, y) == (1, 2, -367) and y % 3120 == 2753   # 17^(-1) mod 3120


def test_A2_negativos_rechazados():
    with pytest.raises(ValueError):
        euclides_extendido(-3, 5)


# A3 - inverso modular
@pytest.mark.parametrize("a,m,esperado", [(17, 3120, 2753), (3, 11, 4), (1, 2, 1)])
def test_A3_inverso(a, m, esperado):
    assert inverso_modular(a, m) == esperado == pow(a, -1, m)


@pytest.mark.parametrize("a,m", [(6, 9), (0, 7), (5, 1)])
def test_A3_inverso_inexistente(a, m):
    with pytest.raises(ValueError):
        inverso_modular(a, m)


# A4 - exponenciaciones contra pow (incluye bordes exp=0 y mod=1)
@pytest.mark.parametrize("b,e,m", [(65, 17, 3233), (2790, 2753, 3233), (0, 0, 7),
                                   (5, 0, 1), (7, 1, 13), (-3, 5, 11),
                                   (123456789, 65537, MOD64)])
def test_A4_exponenciaciones_vs_pow(b, e, m):
    ref = pow(b, e, m)
    assert exp_modular_rapida(b, e, m) == ref
    assert exp_modular_ventana(b, e, m) == ref
    if e < 10 ** 5:
        assert exp_modular_ingenua(b, e, m) == ref


# A5 - ventana deslizante para todos los anchos k = 1..8
@pytest.mark.parametrize("k", range(1, 9))
def test_A5_ventana_k(k):
    e = 0xD3B5_A1F0_0000_0001_FFFF
    assert exp_modular_ventana(3, e, MOD64, k=k) == pow(3, e, MOD64)


def test_A5_ventana_optima():
    assert ventana_optima(0) == 1
    assert ventana_optima(64) <= ventana_optima(512) <= ventana_optima(2048)
    assert ventana_optima(2048) in (6, 7)


# A6 - entradas inválidas
@pytest.mark.parametrize("f", [exp_modular_rapida, exp_modular_ingenua, exp_modular_ventana])
def test_A6_invalidos(f):
    with pytest.raises(ValueError):
        f(2, -1, 7)
    with pytest.raises(ValueError):
        f(2, 3, 0)


def test_A6_ventana_k_invalida():
    with pytest.raises(ValueError):
        exp_modular_ventana(2, 10, 7, k=0)


# A7 - cotas del contador
def test_A7_cota_rapida():
    c = Contador()
    e = 2 ** 1024 - 1
    exp_modular_rapida(3, e, MOD64, c)
    assert c.mult_mod <= 2 * e.bit_length()


def test_A7_ingenua_cuenta_e():
    c = Contador()
    exp_modular_ingenua(3, 1000, MOD64, c)
    assert c.mult_mod == 1000


def test_A7_ventana_menos_que_rapida():
    e = (1 << 2048) - 12345
    cr, cv = Contador(), Contador()
    exp_modular_rapida(3, e, MOD64, cr)
    exp_modular_ventana(3, e, MOD64, cont=cv)
    assert cv.mult_mod < cr.mult_mod


# A8 - el contador no altera el resultado y se reinicia
def test_A8_contador_neutral():
    c = Contador()
    assert exp_modular_rapida(65, 17, 3233, c) == exp_modular_rapida(65, 17, 3233) == 2790
    assert mcd(3120, 17, c) == 1 and c.mcd == 1
    c.reiniciar()
    assert c.como_dict() == {"mult_mod": 0, "div_mod": 0, "mcd": 0, "iteraciones": 0}
    c2 = Contador(mult_mod=2)
    c += c2
    assert c.total() == 2
