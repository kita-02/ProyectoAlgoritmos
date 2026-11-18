"""G1 - lógica común de la interfaz gráfica (no requiere pantalla)."""
from __future__ import annotations

import pytest

from rsa_edu.interfaz.comun import abreviar, comparar, leer_entero, medir, porcentaje_menos


@pytest.mark.parametrize("texto, valor", [
    ("65", 65), (" 3233 ", 3233), ("1_000", 1000), ("0x10", 16),
    ("2**61-1", 2 ** 61 - 1), ("2**10+3", 1027), ("2 ** 8", 256),
])
def test_G1_leer_entero_valido(texto, valor):
    assert leer_entero(texto) == valor


@pytest.mark.parametrize("texto", ["", "   ", "abc", "1.5", "2**x"])
def test_G1_leer_entero_invalido(texto):
    with pytest.raises(ValueError):
        leer_entero(texto, "n")


def test_G1_leer_entero_minimo():
    assert leer_entero("5", "n", 5) == 5
    with pytest.raises(ValueError, match="mayor o igual que 6"):
        leer_entero("5", "n", 6)


def test_G1_abreviar():
    assert abreviar(2790) == "2790"
    assert abreviar(True) == "primo" and abreviar(False) == "compuesto"
    assert abreviar([53, 61]) == "53 × 61"
    largo = abreviar(2 ** 512 + 1)
    assert "…" in largo and "(513 bits)" in largo


def test_G1_comparar_y_medir():
    filas, iguales = comparar({"a": lambda c: 7, "b": lambda c: 7})
    assert iguales and [f.alternativa for f in filas] == ["a", "b"]
    filas, iguales = comparar({"a": lambda c: 7, "b": lambda c: 8})
    assert not iguales
    r, ms, c = medir(lambda c: setattr(c, "mult_mod", 3) or 1)
    assert r == 1 and ms >= 0 and c.mult_mod == 3
    assert filas[0].celdas()[0] == "a"


def test_G1_porcentaje_menos():
    assert porcentaje_menos(200, 150) == 25.0
    assert porcentaje_menos(0, 5) == 0.0
