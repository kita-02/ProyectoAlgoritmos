"""G5 - pestañas RSA y Optimización (lógica, sin pantalla)."""
from __future__ import annotations

import pytest

from rsa_edu.interfaz.pestana_optimizacion import comparar_pipeline
from rsa_edu.interfaz.pestana_rsa import (claves_aleatorias, claves_manuales,
                                          comparar_descifrado, cifrar_mensaje,
                                          descifrar_mensaje, leer_bloques)


@pytest.fixture(scope="module")
def manual():
    return claves_manuales(61, 53, 17)


@pytest.fixture(scope="module")
def grande():
    return claves_aleatorias(512, 2026)


def test_G5_ejemplo_del_informe(manual):
    assert manual.privada.d == 2753
    c = cifrar_mensaje("65", manual, es_texto=False)
    assert c.como_texto() == "2790"
    for crt in (False, True):
        assert descifrar_mensaje("2790", manual, False, crt=crt).mensaje == "65"


@pytest.mark.parametrize("crt, ventana", [(False, False), (True, False), (True, True)])
def test_G5_texto_ida_y_vuelta(grande, crt, ventana):
    texto = "Algoritmos Avanzados – UNSAAC 2026 ñ"
    c = cifrar_mensaje(texto, grande, es_texto=True, ventana=ventana)
    assert descifrar_mensaje(c.como_texto(), grande, True, crt, ventana).mensaje == texto


def test_G5_claves_aleatorias_reproducibles():
    a, b = claves_aleatorias(256, 7), claves_aleatorias(256, 7, criba=False)
    assert a == b and a.publica.n.bit_length() == 256


def test_G5_comparar_descifrado(grande):
    c = cifrar_mensaje("123456789", grande, es_texto=False).como_texto()
    filas, iguales = comparar_descifrado(c, grande)
    assert iguales and filas[0].resultado == 123456789


def test_G5_entradas_invalidas(manual):
    with pytest.raises(ValueError):
        cifrar_mensaje("5000", manual, es_texto=False)          # m >= n
    with pytest.raises(ValueError):
        cifrar_mensaje("", manual, es_texto=True)
    with pytest.raises(ValueError):
        leer_bloques(" , ")
    with pytest.raises(ValueError):
        descifrar_mensaje("1,2", manual, es_texto=False)
    with pytest.raises(ValueError):
        claves_aleatorias(8)


def test_G5_optimizacion_mismo_resultado_y_menos_operaciones():
    res = comparar_pipeline(bits=256, cantidad=4, semilla=2026, repeticiones=1)
    assert res.correcto and len(res.comprobaciones) == 5
    claves, cifrar, descifrar = res.etapas
    assert claves.mult_opt < claves.mult_base
    assert cifrar.mult_opt == cifrar.mult_base               # e = 65537: nada que ahorrar
    assert descifrar.mult_opt < descifrar.mult_base
    assert res.total.ms_base == pytest.approx(sum(e.ms_base for e in res.etapas))


def test_G5_optimizacion_argumentos_invalidos():
    with pytest.raises(ValueError):
        comparar_pipeline(bits=63)
    with pytest.raises(ValueError):
        comparar_pipeline(bits=128, cantidad=0)
