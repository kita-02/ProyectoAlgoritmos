"""Casos I1-I6: integración de módulos, pipeline con sus 6 configuraciones,
CLI (incluida la demostración en vivo) y scripts.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from rsa_edu.__main__ import main
from rsa_edu.pipeline import (ConfigPipeline, configuraciones_estandar,
                              ejecutar_pipeline, gmpy2_disponible)

RAIZ = Path(__file__).resolve().parents[1]
CONFIGS = configuraciones_estandar(bits=512, semilla=2026)


# I1 - las 6 configuraciones del pipeline: misma clave, cifrado = descifrado
@pytest.fixture(scope="module")
def resultados():
    return [ejecutar_pipeline(c, cantidad=5) for c in CONFIGS]


@pytest.mark.parametrize("i", range(len(CONFIGS)), ids=[c.nombre() for c in CONFIGS])
def test_I1_configuracion_correcta(resultados, i):
    r = resultados[i]
    assert r.correcto
    assert r.claves.publica.n.bit_length() == 512
    assert set(r.tiempos) == {"claves", "cifrado", "descifrado"}


def test_I1_misma_clave_y_cifrados(resultados):
    base = resultados[0]
    for r in resultados[1:]:
        assert r.claves == base.claves
        assert r.mensajes == base.mensajes and r.cifrados == base.cifrados


def test_I1_gmpy2_aviso():
    r = ejecutar_pipeline(ConfigPipeline(128, semilla=1, gmpy2=True), cantidad=2)
    assert r.correcto and r.gmpy2_usado == gmpy2_disponible()
    assert bool(r.avisos) != gmpy2_disponible()


def test_I1_mensajes_invalidos():
    with pytest.raises(ValueError):
        ejecutar_pipeline(ConfigPipeline(64, semilla=1), mensajes=[-1])


# I2 - CLI: la demostración presencial (p=61, q=53, e=17, m=65)
def test_I2_demo_en_vivo(tmp_path, capsys):
    k = str(tmp_path / "clave.json")
    assert main(["claves", "-p", "61", "-q", "53", "-e", "17", "-salida", k]) == 0
    assert "d = 2753" in capsys.readouterr().out
    assert main(["cifrar", "65", "-claves", k]) == 0
    assert capsys.readouterr().out.strip() == "2790"
    assert main(["descifrar", "2790", "-claves", k]) == 0
    assert capsys.readouterr().out.strip() == "65"
    assert main(["descifrar", "2790", "-claves", k, "-crt"]) == 0
    assert capsys.readouterr().out.strip() == "65"


# I3 - CLI: ataque
def test_I3_atacar(capsys):
    assert main(["atacar", "-n", "3233", "-e", "17"]) == 0
    out = capsys.readouterr().out
    assert "53 × 61" in out and "d = 2753" in out


# I4 - CLI: entradas inválidas devuelven código 1 y un mensaje claro
@pytest.mark.parametrize("args", [
    ["claves", "-p", "61", "-q", "51"],
    ["primo", "abc"],
    ["factorizar", "0"],
    ["cifrar", "65", "--claves", "no_existe.json"],
    ["atacar", "-n", "49", "-e", "5"],
    ["comando_inexistente"],
])
def test_I4_cli_invalidos(args, capsys):
    assert main(args) == 1


# I5 - CLI: subcomandos de comparación, texto, primo y pipeline
def test_I5_comparar_y_texto(tmp_path, capsys):
    for args in (["comparar", "primalidad", "561"],
                 ["comparar", "factorizacion", "600851475143"],
                 ["comparar", "exponenciacion", "1000"],
                 ["primo", "--generar", "64", "--semilla", "1"],
                 ["factorizar", "3233", "--metodo", "tentativa"],
                 ["pipeline", "--bits", "128", "--mensajes", "3", "--crt", "--ventana"]):
        assert main(args) == 0, args
    k = str(tmp_path / "k.json")
    assert main(["claves", "--bits", "256", "--semilla", "3", "--salida", k]) == 0
    assert main(["comparar", "descifrado", "12345", "--claves", k]) == 0
    capsys.readouterr()
    assert main(["cifrar", "--texto", "Hola UNSAAC", "--claves", k]) == 0
    bloques = capsys.readouterr().out.strip()
    assert main(["descifrar", "--texto", bloques, "--claves", k, "--crt"]) == 0
    assert capsys.readouterr().out.strip() == "Hola UNSAAC"


# I6 - ejecución real como módulo y scripts del repositorio
def test_I6_python_m(tmp_path):
    env = {**os.environ, "PYTHONPATH": str(RAIZ / "src"), "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([sys.executable, "-m", "rsa_edu", "atacar", "-n", "3233", "-e", "17"],
                       capture_output=True, text=True, encoding="utf-8", env=env, cwd=tmp_path)
    assert r.returncode == 0 and "2753" in r.stdout


@pytest.mark.parametrize("script,args", [("traza_instancia.py", []),
                                         ("generar_instancias.py", ["--salida", "{tmp}"])])
def test_I6_scripts(tmp_path, script, args):
    args = [a.replace("{tmp}", str(tmp_path)) for a in args]
    r = subprocess.run([sys.executable, str(RAIZ / "scripts" / script), *args],
                       capture_output=True, text=True, encoding="utf-8",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    assert r.returncode == 0, r.stderr
