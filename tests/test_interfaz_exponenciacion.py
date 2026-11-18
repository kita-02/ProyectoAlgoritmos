"""G2 - pestaña de exponenciación modular (lógica, sin pantalla)."""
from __future__ import annotations

import pytest

from rsa_edu.interfaz.pestana_exponenciacion import (comparar_exponenciacion,
                                                     numeros_aleatorios, traza_binaria)


def test_G2_ejemplo_del_informe():
    res = comparar_exponenciacion(65, 17, 3233)
    assert res.correcto and res.referencia == 2790
    assert [f.resultado for f in res.filas] == [2790, 2790, 2790]
    assert res.filas[2].mult == 17                       # ingenua: e multiplicaciones


def test_G2_ventana_ahorra_multiplicaciones():
    base, exp, mod = numeros_aleatorios(1024, 2026)
    res = comparar_exponenciacion(base, exp, mod)
    assert res.correcto and len(res.filas) == 2          # sin ingenua (exponente enorme)
    assert res.filas[1].mult < res.filas[0].mult
    assert res.ahorro_ventana > 10


def test_G2_traza_binaria_coincide_con_el_informe():
    pasos = traza_binaria(65, 17, 3233)
    assert [(p.bit, p.r_antes, p.potencia, p.r_despues) for p in pasos] == [
        (1, 1, 65, 65), (0, 65, 992, 65), (0, 65, 1232, 65), (0, 65, 1547, 65),
        (1, 65, 789, 2790)]


@pytest.mark.parametrize("base, exp, mod", [(3, 0, 7), (5, 1, 1), (2, 100, 97), (10, 77, 2)])
def test_G2_traza_y_comparacion_casos_limite(base, exp, mod):
    pasos = traza_binaria(base, exp, mod)
    final = pasos[-1].r_despues if pasos else 1 % mod
    assert final == pow(base, exp, mod)
    assert comparar_exponenciacion(base, exp, mod).correcto


def test_G2_numeros_reproducibles():
    assert numeros_aleatorios(256, 7) == numeros_aleatorios(256, 7)
    assert numeros_aleatorios(256, 7) != numeros_aleatorios(256, 8)
    _, _, mod = numeros_aleatorios(64, 1)
    assert mod.bit_length() == 64 and mod % 2 == 1


def test_G2_entradas_invalidas():
    with pytest.raises(ValueError):
        comparar_exponenciacion(2, -1, 7)
    with pytest.raises(ValueError):
        comparar_exponenciacion(2, 3, 0)
    with pytest.raises(ValueError):
        traza_binaria(2, 3, 0)
    with pytest.raises(ValueError):
        numeros_aleatorios(2, 1)
