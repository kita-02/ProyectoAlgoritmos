"""G4 - pestaña de factorización y ataque (lógica, sin pantalla)."""
from __future__ import annotations

import math

import pytest

from rsa_edu.interfaz.pestana_factorizacion import (atacar, comparar_factorizacion,
                                                    semiprimo_aleatorio)


@pytest.mark.parametrize("n, factores", [(8051, [83, 97]), (3233, [53, 61]),
                                         (600851475143, [71, 839, 1471, 6857]), (97, [97])])
def test_G4_metodos_coinciden(n, factores):
    res = comparar_factorizacion(n)
    assert res.verificado and len(res.filas) == 3
    assert all(f.resultado == factores for f in res.filas)


def test_G4_semiprimo_reproducible():
    n, p, q = semiprimo_aleatorio(40, 2026)
    assert (n, p, q) == semiprimo_aleatorio(40, 2026)
    assert p * q == n and p < q and n.bit_length() == 40


def test_G4_numeros_grandes_omiten_division():
    n, p, q = semiprimo_aleatorio(64, 3)
    res = comparar_factorizacion(n)
    assert res.verificado and res.omitidas and len(res.filas) == 2
    assert res.filas[0].resultado == [p, q]


def test_G4_ataque_recupera_la_clave_del_informe():
    res = atacar(3233, 17, "brent")
    assert res.verificado
    c = res.clave
    assert (c.p, c.q, c.phi, c.d) == (53, 61, 3120, 2753)


@pytest.mark.parametrize("metodo", ["rho", "tentativa"])
def test_G4_ataque_otros_metodos(metodo):
    n, p, q = semiprimo_aleatorio(32, 5)
    phi = (p - 1) * (q - 1)
    e = next(x for x in (65537, 3, 5, 7, 11, 13, 17, 19, 23) if math.gcd(x, phi) == 1)
    assert atacar(n, e, metodo).verificado


def test_G4_entradas_invalidas():
    with pytest.raises(ValueError):
        comparar_factorizacion(1)
    with pytest.raises(ValueError):
        semiprimo_aleatorio(4)
    with pytest.raises(ValueError):
        atacar(2 ** 61 - 1, 3, "brent")             # n primo: no es p·q
    with pytest.raises(ValueError):
        atacar(2 ** 50 + 1, 3, "tentativa")
