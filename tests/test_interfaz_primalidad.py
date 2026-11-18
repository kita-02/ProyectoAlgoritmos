"""G3 - pestaña de primalidad (lógica, sin pantalla)."""
from __future__ import annotations

import pytest

from rsa_edu.interfaz.pestana_primalidad import (EJEMPLOS, comparar_generacion,
                                                 comparar_primalidad)
from rsa_edu.interfaz.comun import leer_entero


@pytest.mark.parametrize("n, primo", [(561, False), (2047, False), (3233, False),
                                      (1_000_000_007, True), (97, True), (1, False)])
def test_G3_pruebas_coinciden(n, primo):
    res = comparar_primalidad(n)
    assert res.iguales and res.es_primo == primo
    assert len(res.filas) == 3 and not res.omitidas


def test_G3_numeros_grandes_omiten_lo_inviable():
    res = comparar_primalidad(2 ** 61 - 1)
    assert res.es_primo and res.iguales and len(res.filas) == 2 and len(res.omitidas) == 1
    res = comparar_primalidad(2 ** 89 - 1)
    assert res.es_primo and len(res.filas) == 1 and len(res.omitidas) == 2


def test_G3_ejemplos_validos():
    for texto in EJEMPLOS.values():
        assert comparar_primalidad(leer_entero(texto)).iguales


def test_G3_generacion_con_y_sin_criba():
    res = comparar_generacion(256, 2026)
    assert res.mismo_primo
    assert res.filas[0].resultado.bit_length() == 256
    assert res.filas[1].mult < res.filas[0].mult and res.ahorro > 0


def test_G3_entradas_invalidas():
    with pytest.raises(ValueError):
        comparar_primalidad(-1)
    with pytest.raises(ValueError):
        comparar_generacion(4)
