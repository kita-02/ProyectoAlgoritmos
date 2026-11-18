"""I7 - demostración de optimización: base y optimizado dan el mismo resultado."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("demo_optimizacion",
                                               RAIZ / "scripts" / "demo_optimizacion.py")
demo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(demo)


@pytest.mark.parametrize("bits", [64, 256])
def test_I7_base_y_optimizado_equivalentes(bits):
    rb = demo.medir(bits, 5, 2026, 1, **demo.CONFIGURACIONES["base"])
    ro = demo.medir(bits, 5, 2026, 1, **demo.CONFIGURACIONES["optimizado"])
    assert rb[0] == ro[0]                      # misma clave
    assert rb[2] == ro[2]                      # mismos cifrados
    assert rb[3] == rb[1] and ro[3] == ro[1]   # ambos recuperan los mensajes


def test_I7_criba_reduce_operaciones_al_generar_claves():
    rb = demo.medir(256, 1, 7, 1, **demo.CONFIGURACIONES["base"])
    ro = demo.medir(256, 1, 7, 1, **demo.CONFIGURACIONES["optimizado"])
    assert ro[5]["Generar claves"].mult_mod < rb[5]["Generar claves"].mult_mod


def test_I7_main(capsys):
    assert demo.main(["--bits", "128", "--mensajes", "3", "--rep", "1"]) == 0
    salida = capsys.readouterr().out
    assert "RESULTADO: mismo resultado [OK]" in salida


def test_I7_argumentos_invalidos():
    with pytest.raises(SystemExit):
        demo.main(["--rep", "0"])
