"""Casos R1-R12: ejemplo manual, ida y vuelta 16-2048 bits, FIPS 186-5,
lambda de Carmichael, TCR, texto en bloques y entradas inválidas.
"""
from __future__ import annotations

import random
from math import gcd, lcm

import pytest
from sympy import isprime

from conftest import C, D, E, M, P, Q
from rsa_edu.contador import Contador
from rsa_edu.rsa import (ClavePrivada, cifrar, cifrar_texto, descifrar, descifrar_crt,
                         descifrar_texto, elegir_e, generar_claves,
                         generar_claves_aleatorias, lambda_carmichael, tamano_bloque)


# R1 - instancia resuelta a mano: p=61, q=53, e=17, m=65 -> c=2790, d=2753
def test_R1_ejemplo_manual(clave_manual):
    pub, priv = clave_manual.publica, clave_manual.privada
    assert (pub.n, pub.e, priv.d) == (3233, E, D)
    assert cifrar(M, pub) == C
    assert descifrar(C, priv) == M
    assert descifrar_crt(C, priv) == M


def test_R1_parametros_tcr(clave_manual):
    priv = clave_manual.privada
    assert (priv.dp, priv.dq, priv.qinv) == (2753 % 60, 2753 % 52, pow(53, -1, 61))


# R2 - ida y vuelta para todos los m de una clave pequeña (exhaustivo)
def test_R2_exhaustivo_clave_pequena(clave_manual):
    pub, priv = clave_manual.publica, clave_manual.privada
    for m in range(pub.n):
        c = cifrar(m, pub)
        assert descifrar(c, priv) == m == descifrar_crt(c, priv)


# R3 - claves aleatorias de 16 a 2048 bits: tamaño exacto e ida y vuelta
@pytest.mark.parametrize("bits", [16, 32, 64, 128, 256, 512, 1024, 2048])
def test_R3_ida_y_vuelta(bits):
    rng = random.Random(bits)
    kp = generar_claves_aleatorias(bits, rng=rng)
    pub, priv = kp.publica, kp.privada
    assert pub.n.bit_length() == bits
    for _ in range(3):
        m = rng.randrange(pub.n)
        c = cifrar(m, pub)
        assert descifrar_crt(c, priv) == m
        if bits <= 1024:
            assert descifrar(c, priv) == m


# R4 - condiciones FIPS 186-5
def test_R4_fips(clave_512):
    pub, priv = clave_512.publica, clave_512.privada
    p, q, e, d = priv.p, priv.q, pub.e, priv.d
    assert isprime(p) and isprime(q)
    assert p.bit_length() == q.bit_length() == 256
    assert gcd(e, p - 1) == gcd(e, q - 1) == 1
    assert abs(p - q) > 2 ** (256 - 100)
    assert d > 2 ** 256
    assert e * d % lcm(p - 1, q - 1) == 1


def test_R4_reproducible_y_criba_neutral():
    a = generar_claves_aleatorias(256, rng=random.Random(11), criba=True)
    b = generar_claves_aleatorias(256, rng=random.Random(11), criba=False)
    assert a == b


# R5 - lambda de Carmichael
@pytest.mark.parametrize("p,q,esperado", [(61, 53, 780), (11, 13, 60), (3, 5, 4)])
def test_R5_lambda(p, q, esperado):
    assert lambda_carmichael(p, q) == esperado == lcm(p - 1, q - 1)


def test_R5_lambda_invalida():
    with pytest.raises(ValueError):
        lambda_carmichael(1, 7)


# R6 - TCR: mismo resultado y menos operaciones
def test_R6_crt_menos_operaciones(clave_512):
    pub, priv = clave_512.publica, clave_512.privada
    c = cifrar(123456789, pub)
    cn, cc = Contador(), Contador()
    assert descifrar(c, priv, cont=cn) == descifrar_crt(c, priv, cont=cc) == 123456789
    # Mismo número de productos, pero sobre números de la MITAD de bits:
    # cada producto cuesta ~1/4 (multiplicación cuadrática) -> ~4x más rápido.
    assert cc.mult_mod <= 1.1 * cn.mult_mod
    assert priv.dp.bit_length() <= 256 and priv.dq.bit_length() <= 256
    assert max(priv.p, priv.q).bit_length() * 2 == pub.n.bit_length()


@pytest.mark.parametrize("ventana", [False, True])
def test_R6_ventana_equivalente(clave_512, ventana):
    pub, priv = clave_512.publica, clave_512.privada
    c = cifrar(987654321, pub, ventana=ventana)
    assert c == cifrar(987654321, pub)
    assert descifrar(c, priv, ventana) == descifrar_crt(c, priv, ventana) == 987654321


# R7 - casos límite del mensaje: 0, 1, n-1
@pytest.mark.parametrize("m", [0, 1, 2, 3232])
def test_R7_mensajes_limite(clave_manual, m):
    pub, priv = clave_manual.publica, clave_manual.privada
    assert descifrar_crt(cifrar(m, pub), priv) == m


# R8 - texto en bloques (UTF-8, vacío, largo)
@pytest.mark.parametrize("texto", ["", "a", "Hola mundo", "Cusco ñandú ÁÉÍÓÚ 🚀",
                                   "x" * 1000])
def test_R8_texto(clave_512, texto):
    pub, priv = clave_512.publica, clave_512.privada
    bloques = cifrar_texto(texto, pub)
    assert descifrar_texto(bloques, priv) == texto
    assert descifrar_texto(bloques, priv, crt=True) == texto


def test_R8_texto_clave_pequena(clave_manual):
    assert tamano_bloque(3233) == 1
    b = cifrar_texto("RSA", clave_manual.publica)
    assert len(b) == 4 and descifrar_texto(b, clave_manual.privada) == "RSA"


def test_R8_texto_clave_incorrecta(clave_512):
    otra = generar_claves_aleatorias(512, rng=random.Random(99))
    bloques = cifrar_texto("secreto", clave_512.publica)
    with pytest.raises(ValueError):
        descifrar_texto(bloques, otra.privada)


# R10 - entradas inválidas
@pytest.mark.parametrize("p,q,e", [(61, 61, 17), (61, 51, 17), (60, 53, 17),
                                   (61, 53, 3120), (61, 53, 26), (61, 53, 1)])
def test_R10_generar_claves_invalidas(p, q, e):
    with pytest.raises(ValueError):
        generar_claves(p, q, e)


@pytest.mark.parametrize("m", [-1, 3233, 10 ** 9, 65.0, True])
def test_R10_mensaje_fuera_de_rango(clave_manual, m):
    with pytest.raises(ValueError):
        cifrar(m, clave_manual.publica)
    with pytest.raises(ValueError):
        descifrar(m, clave_manual.privada)
    with pytest.raises(ValueError):
        descifrar_crt(m, clave_manual.privada)


@pytest.mark.parametrize("bits,e", [(15, 65537), (17, 65537), (8, 65537), (64, 4), (64, 1),
                                    (16, 65537)])
def test_R10_parametros_aleatorias_invalidos(bits, e):
    with pytest.raises(ValueError):
        generar_claves_aleatorias(bits, e)


def test_R10_texto_n_pequeno():
    priv = ClavePrivada(15 * 1, 3, 3, 5)
    with pytest.raises(ValueError):
        tamano_bloque(priv.n)


def test_R10_texto_tipo_y_vacio(clave_manual):
    with pytest.raises(TypeError):
        cifrar_texto(b"bytes", clave_manual.publica)
    with pytest.raises(ValueError):
        descifrar_texto([], clave_manual.privada)


# R11 - elección automática de e
def test_R11_elegir_e():
    assert elegir_e(3120) == 7            # 65537 > phi -> menor impar coprimo (3, 5 dividen)
    assert elegir_e(10 ** 6 + 2) == 65537
    assert generar_claves(61, 53).publica.e == 7


# R12 - las claves son inmutables
def test_R12_inmutables(clave_manual):
    with pytest.raises(AttributeError):
        clave_manual.publica.n = 1
