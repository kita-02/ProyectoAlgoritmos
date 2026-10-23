"""Casos F1-F9: producto = n, factores primos, comparación cruzada entre
métodos, oráculo sympy, límites, variante de Brent y ataque a RSA.
"""
from __future__ import annotations

import random
from math import prod

import pytest
from sympy import factorint, isprime, nextprime

from conftest import CARMICHAEL
from rsa_edu.ataque import romper_clave
from rsa_edu.contador import Contador
from rsa_edu.factorizacion import (METODOS, factorizar, factorizar_tentativa,
                                   pollard_rho, pollard_rho_brent)


def oraculo(n: int) -> list[int]:
    return sorted(factorint(n, multiple=True)) if n > 1 else []


# F1 - casos básicos resueltos a mano (Avance 1: 3233 = 53 x 61)
@pytest.mark.parametrize("metodo", METODOS)
@pytest.mark.parametrize("n,esperado", [(1, []), (2, [2]), (3233, [53, 61]),
                                        (561, [3, 11, 17]), (1024, [2] * 10),
                                        (600851475143, [71, 839, 1471, 6857])])
def test_F1_basicos(metodo, n, esperado):
    assert factorizar(n, metodo, rng=random.Random(1)) == esperado


# F2 - barrido [1, 3000] contra el oráculo sympy, para cada método
@pytest.mark.parametrize("metodo", METODOS)
def test_F2_barrido_oraculo(metodo):
    rng = random.Random(7)
    errores = [n for n in range(1, 3001) if factorizar(n, metodo, rng=rng) != oraculo(n)]
    assert errores == []


# F3 - producto de los factores = n y todos son primos (aleatorios hasta 2^60)
@pytest.mark.parametrize("semilla", range(8))
def test_F3_producto_y_primos(semilla):
    rng = random.Random(semilla)
    n = rng.randrange(2, 2 ** 60)
    f = factorizar(n, "brent", rng=rng)
    assert prod(f) == n and all(isprime(p) for p in f) and f == sorted(f)


# F4 - comparación cruzada: los tres métodos dan la misma factorización
@pytest.mark.parametrize("n", [2 ** 32 + 1, 10 ** 12 + 39 * 7, 999999000001, 2 ** 40 - 1] + CARMICHAEL[:6])
def test_F4_comparacion_cruzada(n):
    r = [factorizar(n, m, rng=random.Random(2)) for m in METODOS]
    assert r[0] == r[1] == r[2] == oraculo(n)


# F5 - semiprimos balanceados de hasta 80 bits (solo métodos rho)
@pytest.mark.parametrize("bits", [20, 32, 48, 64, 80])
def test_F5_semiprimos_balanceados(bits):
    p = nextprime(2 ** (bits // 2 - 1) + 12345)
    q = nextprime(p + 1000)
    n = p * q
    for m in ("rho", "brent"):
        assert factorizar(n, m, rng=random.Random(bits)) == [p, q]


# F6 - límites: cuadrados de primos, potencias, primos grandes
@pytest.mark.parametrize("n", [49, 7919 ** 2, 3 ** 30, 2 ** 61 - 1, (2 ** 31 - 1) ** 2])
def test_F6_limites(n):
    assert factorizar(n, "brent", rng=random.Random(5)) == oraculo(n)


# F7 - entradas inválidas y límite de iteraciones
@pytest.mark.parametrize("n", [0, -15])
def test_F7_n_invalido(n):
    with pytest.raises(ValueError):
        factorizar(n)


def test_F7_metodo_desconocido():
    with pytest.raises(ValueError):
        factorizar(15, "fermat")


@pytest.mark.parametrize("valor", [15.0, "15"])
def test_F7_tipo_invalido(valor):
    with pytest.raises(TypeError):
        factorizar(valor)


@pytest.mark.parametrize("f", [pollard_rho, pollard_rho_brent])
def test_F7_max_iter_agotado(f):
    n = nextprime(2 ** 40) * nextprime(2 ** 41)
    with pytest.raises(RuntimeError, match="max_iter"):
        f(n, rng=random.Random(0), max_iter=5)


@pytest.mark.parametrize("f", [pollard_rho, pollard_rho_brent])
def test_F7_rho_requiere_compuesto(f):
    with pytest.raises(ValueError):
        f(3)
    with pytest.raises(RuntimeError):
        f(101, max_reintentos=3, rng=random.Random(0))   # primo: no hay factor


def test_F7_tentativa_invalida():
    with pytest.raises(ValueError):
        factorizar_tentativa(0)


# F8 - Brent: factor no trivial, lotes distintos y menos mcd que Floyd
@pytest.mark.parametrize("lote", [1, 2, 16, 128, 1000])
def test_F8_brent_lotes(lote):
    n = 1000003 * 1000033
    d = pollard_rho_brent(n, rng=random.Random(lote), lote=lote)
    assert d in (1000003, 1000033)


def test_F8_brent_menos_mcd():
    n = nextprime(10 ** 9) * nextprime(2 * 10 ** 9)
    cf, cb = Contador(), Contador()
    pollard_rho(n, rng=random.Random(3), cont=cf)
    pollard_rho_brent(n, rng=random.Random(3), cont=cb)
    assert cb.mcd < cf.mcd


def test_F8_brent_lote_invalido():
    with pytest.raises(ValueError):
        pollard_rho_brent(15, lote=0)


def test_F8_pares():
    assert pollard_rho(1000) == pollard_rho_brent(1000) == 2


# F9 - ataque: romper_clave recupera d
@pytest.mark.parametrize("p,q,e", [(61, 53, 17), (89, 97, 5), (1009, 2003, 5),
                                   (nextprime(2 ** 30), nextprime(2 ** 31), 65537)])
def test_F9_romper_clave(p, q, e):
    from math import gcd
    phi = (p - 1) * (q - 1)
    if gcd(e, phi) != 1:
        e = 7 if gcd(7, phi) == 1 else 11
    r = romper_clave(p * q, e, rng=random.Random(0))
    assert (r.p, r.q) == tuple(sorted((p, q)))
    assert r.d == pow(e, -1, phi)
    m = 42
    assert pow(pow(m, e, p * q), r.d, p * q) == m


def test_F9_manual():
    r = romper_clave(3233, 17)
    assert (r.p, r.q, r.phi, r.d) == (53, 61, 3120, 2753)


@pytest.mark.parametrize("n,e", [(3233 * 7, 17), (49, 5), (4, 3), (3233, 6)])
def test_F9_ataque_invalido(n, e):
    with pytest.raises(ValueError):
        romper_clave(n, e)
