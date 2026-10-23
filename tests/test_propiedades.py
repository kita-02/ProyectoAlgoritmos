"""Pruebas basadas en propiedades con Hypothesis (miles de entradas aleatorias)."""
from __future__ import annotations

import random
from math import gcd, prod

from hypothesis import given, settings
from hypothesis import strategies as st
from sympy import isprime

from rsa_edu.aritmetica import (euclides_extendido, exp_modular_rapida,
                                exp_modular_ventana, inverso_modular)
from rsa_edu.factorizacion import factorizar
from rsa_edu.primalidad import es_primo
from rsa_edu.rsa import cifrar, descifrar, descifrar_crt, generar_claves

enteros = st.integers(min_value=0, max_value=2 ** 128)


@given(enteros, enteros)
def test_bezout(a, b):
    g, x, y = euclides_extendido(a, b)
    assert g == gcd(a, b) and a * x + b * y == g


@given(st.integers(1, 2 ** 64), st.integers(2, 2 ** 64))
def test_inverso(a, m):
    if gcd(a, m) == 1:
        assert a * inverso_modular(a, m) % m == 1 % m


@given(st.integers(-2 ** 64, 2 ** 64), st.integers(0, 2 ** 256), st.integers(1, 2 ** 128),
       st.integers(1, 8))
def test_exponenciaciones(b, e, m, k):
    assert exp_modular_rapida(b, e, m) == exp_modular_ventana(b, e, m, k=k) == pow(b, e, m)


@given(st.integers(-10, 2 ** 80))
def test_primalidad(n):
    assert es_primo(n) == isprime(n)


@settings(max_examples=60, deadline=None)
@given(st.integers(1, 2 ** 48))
def test_factorizacion(n):
    f = factorizar(n, "brent", rng=random.Random(n))
    assert prod(f) == n and all(isprime(p) for p in f)


primos_chicos = st.sampled_from([p for p in range(3, 3000) if isprime(p)])


@settings(max_examples=80, deadline=None)
@given(primos_chicos, primos_chicos, st.data())
def test_rsa_ida_y_vuelta(p, q, data):
    if p == q or (p - 1) * (q - 1) < 10:
        return
    kp = generar_claves(p, q)
    m = data.draw(st.integers(0, p * q - 1))
    c = cifrar(m, kp.publica)
    assert descifrar(c, kp.privada) == m == descifrar_crt(c, kp.privada)


@settings(max_examples=40, deadline=None)
@given(st.integers(0, 2 ** 32))
def test_generar_primo_determinista(semilla):
    from rsa_edu.primalidad import generar_primo
    p = generar_primo(48, random.Random(semilla))
    assert p == generar_primo(48, random.Random(semilla), criba=False)
    assert isprime(p) and p.bit_length() == 48
