"""Casos P1-P11: barrido exhaustivo, Carmichael, pseudoprimos fuertes, criba y
generación de primos. Oráculo de referencia: sympy.isprime.
"""
from __future__ import annotations

import random

import pytest
from sympy import isprime

from conftest import CARMICHAEL, PRIMOS_CONOCIDOS, PSEUDOPRIMOS_FUERTES
from rsa_edu.contador import Contador
from rsa_edu.primalidad import (BASES_DETERMINISTAS, LIMITE_DETERMINISTA,
                                PRIMOS_PEQUENOS, criba_eratostenes, descomponer,
                                division_tentativa, es_primo, es_testigo,
                                generar_primo, miller_rabin,
                                miller_rabin_determinista, pasa_criba)

BARRIDO = range(0, 20001)


# P1 - barrido exhaustivo [0, 20000]: las cuatro funciones coinciden con el oráculo
@pytest.mark.parametrize("f", [division_tentativa, miller_rabin_determinista, es_primo,
                               lambda n: miller_rabin(n, rng=random.Random(n))],
                         ids=["tentativa", "mr_determinista", "es_primo", "mr_aleatorio"])
def test_P1_barrido(f):
    errores = [n for n in BARRIDO if f(n) != isprime(n)]
    assert errores == []


# P2 - casos límite: negativos, 0, 1, 2, 3, 4
@pytest.mark.parametrize("n,esperado", [(-7, False), (-1, False), (0, False), (1, False),
                                        (2, True), (3, True), (4, False)])
def test_P2_bordes(n, esperado):
    assert division_tentativa(n) is esperado
    assert miller_rabin(n) is esperado
    assert miller_rabin_determinista(n) is esperado


# P3 - números de Carmichael: Miller-Rabin no se deja engañar
@pytest.mark.parametrize("n", CARMICHAEL)
def test_P3_carmichael(n):
    assert not miller_rabin(n, rng=random.Random(1))
    assert not miller_rabin_determinista(n)
    assert not division_tentativa(n)


# P4 - pseudoprimos fuertes: engañan a algunas bases pero no a las 12 fijas
@pytest.mark.parametrize("n", PSEUDOPRIMOS_FUERTES)
def test_P4_pseudoprimos_fuertes(n):
    assert not miller_rabin_determinista(n)
    assert not es_primo(n)


def test_P4_2047_engana_a_base_2():
    s, d = descomponer(2047)
    assert not es_testigo(2, s, d, 2047)       # 2 es "mentiroso fuerte" de 2047
    assert es_testigo(3, s, d, 2047)


# P5 - primos conocidos (hasta Mersenne 2^127 - 1)
@pytest.mark.parametrize("p", PRIMOS_CONOCIDOS)
def test_P5_primos_conocidos(p):
    assert es_primo(p)
    assert miller_rabin(p, rng=random.Random(0))


# P6 - compuestos grandes (producto de primos conocidos y Mersenne compuesto)
@pytest.mark.parametrize("n", [2 ** 67 - 1, (2 ** 61 - 1) * (2 ** 31 - 1),
                               (2 ** 127 - 1) * 3, 10 ** 30 + 1])
def test_P6_compuestos_grandes(n):
    assert not es_primo(n)


# P7 - descomposición n - 1 = 2^s d
@pytest.mark.parametrize("n,s,d", [(3, 1, 1), (61, 2, 15), (561, 4, 35), (2047, 1, 1023)])
def test_P7_descomponer(n, s, d):
    assert descomponer(n) == (s, d) and d % 2 == 1 and 2 ** s * d == n - 1


def test_P7_descomponer_invalido():
    with pytest.raises(ValueError):
        descomponer(2)


# P8 - cota 1/4: la fracción de bases mentirosas fuertes de un compuesto es <= 1/4
@pytest.mark.parametrize("n", [561, 2047, 1105, 8911, 65])
def test_P8_cota_un_cuarto(n):
    s, d = descomponer(n)
    mentirosos = sum(1 for a in range(2, n - 1) if not es_testigo(a, s, d, n))
    assert mentirosos <= (n - 3) / 4


# P9 - criba de Eratóstenes y filtro de candidatos
def test_P9_criba():
    assert len(PRIMOS_PEQUENOS) == 303 and PRIMOS_PEQUENOS[-1] == 1999
    assert criba_eratostenes(30) == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    assert criba_eratostenes(1) == []


@pytest.mark.parametrize("n,esperado", [(0, False), (1, False), (2, True), (1999, True),
                                        (2001, False), (1999 * 1997, False),
                                        (2003 * 2011, True), (2 ** 61 - 1, True)])
def test_P9_pasa_criba(n, esperado):
    assert pasa_criba(n) is esperado


# P10 - generar_primo: exactamente b bits, primo, reproducible, criba no cambia el resultado
@pytest.mark.parametrize("bits", [2, 3, 8, 16, 32, 64, 128, 256, 512, 1024])
def test_P10_generar_primo(bits):
    p = generar_primo(bits, random.Random(bits))
    assert p.bit_length() == bits and isprime(p)
    assert p == generar_primo(bits, random.Random(bits), criba=False)


def test_P10_dos_bits_altos():
    p = generar_primo(64, random.Random(3), dos_bits_altos=True)
    assert p >> 62 == 0b11 and isprime(p)


def test_P10_criba_reduce_pruebas_mr():
    con, sin = Contador(), Contador()
    p1 = generar_primo(512, random.Random(9), criba=True, cont=con)
    p2 = generar_primo(512, random.Random(9), criba=False, cont=sin)
    assert p1 == p2                                     # mismos candidatos, mismo primo
    assert con.mult_mod < sin.mult_mod                  # menos exponenciaciones


@pytest.mark.parametrize("bits", [0, 1, -5])
def test_P10_bits_invalidos(bits):
    with pytest.raises(ValueError):
        generar_primo(bits)


# P11 - entradas inválidas y límites de la versión determinista
def test_P11_rondas_invalidas():
    with pytest.raises(ValueError):
        miller_rabin(101, rondas=0)


def test_P11_limite_determinista():
    assert BASES_DETERMINISTAS == (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    with pytest.raises(ValueError):
        miller_rabin_determinista(LIMITE_DETERMINISTA + 2)
    # Por encima del límite es_primo pasa a la versión aleatoria
    assert es_primo(2 ** 89 - 1) and es_primo(2 ** 127 - 1, rng=random.Random(4))


@pytest.mark.parametrize("valor", [7.0, "7", None])
def test_P11_tipo_invalido(valor):
    with pytest.raises(TypeError):
        es_primo(valor)
