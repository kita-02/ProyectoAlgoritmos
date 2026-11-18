"""X1-X6: procedimiento experimental (Avance 6).

Comprueban con una configuración diminuta que el benchmark produce datos
correctos y con el formato esperado, que dos corridas dan exactamente los
mismos conteos (reproducibilidad), y que los scripts de figuras, ajuste de
complejidad y demos terminan bien.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SCRIPTS = RAIZ / "scripts"


def _modulo(nombre: str):
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(nombre, SCRIPTS / f"{nombre}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


benchmark = _modulo("benchmark")

CONFIG_MINIMA = {
    "nombre": "prueba", "semilla": 7, "repeticiones": 2, "calentamiento": 0,
    "instancias": "data/instancias",
    "E1_primalidad": {"algoritmos": ["division_tentativa", "miller_rabin",
                                     "miller_rabin_determinista"],
                      "rondas_mr": 5, "max_bits_tentativa": 24, "max_bits": 32},
    "E2_factorizacion": {"algoritmos": ["tentativa", "rho", "brent"],
                         "max_bits_tentativa": 24, "max_bits": 28},
    "E3_exponenciacion": {"algoritmos": ["binaria", "ventana"], "bits": [64, 128, 256],
                          "instancias_por_tamano": 1},
    "E4_descifrado": {"bits": [512], "claves_por_tamano": 1, "mensajes_por_clave": 2},
    "E5_generacion_primos": {"bits": [64], "instancias_por_tamano": 1},
    "E6_pipeline": {"bits": [512], "semillas_por_tamano": 1, "mensajes": 2},
}


@pytest.fixture(scope="module")
def corrida(tmp_path_factory):
    base = tmp_path_factory.mktemp("exp")
    cfg = base / "config.json"
    cfg.write_text(json.dumps(CONFIG_MINIMA), encoding="utf-8")
    salida = benchmark.ejecutar(cfg, base / "r1", silencioso=True)
    return cfg, salida


def _filas(carpeta: Path) -> list[dict]:
    filas = []
    for ruta in sorted(carpeta.glob("E*.csv")):
        with ruta.open(newline="", encoding="utf-8") as fh:
            filas += list(csv.DictReader(fh))
    return filas


# X1 - formato de almacenamiento: seis CSV con las columnas acordadas + metadatos
def test_X1_formato(corrida):
    _, salida = corrida
    assert sorted(p.name for p in salida.glob("E*.csv")) == [f"E{i}.csv" for i in range(1, 7)]
    with (salida / "E1.csv").open(encoding="utf-8") as fh:
        assert next(csv.reader(fh)) == benchmark.COLUMNAS
    meta = json.loads((salida / "metadatos.json").read_text(encoding="utf-8"))
    for campo in ("semilla", "repeticiones", "python", "sistema", "sha256_configuracion",
                  "experimentos"):
        assert campo in meta


# X2 - datos correctos: toda fila coincide con la referencia y es estable
def test_X2_correctos(corrida):
    filas = _filas(corrida[1])
    assert filas and all(f["ok"] == "True" and f["estable"] == "True" for f in filas)
    assert {f["experimento"] for f in filas} == {f"E{i}" for i in range(1, 7)}


# X3 - reproducibles: otra corrida da exactamente los mismos conteos
def test_X3_reproducibles(corrida, tmp_path):
    cfg, salida = corrida
    otra = benchmark.ejecutar(cfg, tmp_path / "r2", silencioso=True)
    clave = ("experimento", "algoritmo", "etapa", "instancia", "bits")
    a = {tuple(f[c] for c in clave): f for f in _filas(salida)}
    b = {tuple(f[c] for c in clave): f for f in _filas(otra)}
    assert a.keys() == b.keys()
    for k in a:
        for col in ("mult_mod", "div_mod", "mcd", "iteraciones", "extra", "ok"):
            assert a[k][col] == b[k][col], (k, col)


# X4 - coherencia con la teoría sobre los mismos datos
def test_X4_coherencia(corrida):
    verificar = _modulo("verificar_reproducibilidad")
    checks = verificar.coherencia(verificar.leer(corrida[1]))
    conteo = [c for c in checks if "tiempo" not in c[0] and "rápido" not in c[0]]
    assert conteo and all(ok for _, ok, _ in conteo), checks


# X5 - figuras, tablas y ajuste de complejidad a partir de los CSV
def test_X5_figuras_tablas_y_ajustes(corrida):
    _, salida = corrida
    assert _modulo("graficar").main([str(salida)]) == 0
    assert (salida / "figuras" / "E6_pipeline.png").is_file()
    assert (salida / "tablas" / "E4.tex").is_file()
    assert _modulo("ajuste_complejidad").main([str(salida)]) == 0
    assert (salida / "ajustes.md").is_file()


def test_X5_graficar_sin_datos(tmp_path):
    assert _modulo("graficar").main([str(tmp_path)]) == 1


def test_X5_experimento_desconocido():
    with pytest.raises(SystemExit):
        benchmark.main(["--solo", "E9"])


def test_X5_configuracion_incompleta(tmp_path):
    incompleta = {k: v for k, v in CONFIG_MINIMA.items() if k != "E6_pipeline"}
    cfg = tmp_path / "c.json"
    cfg.write_text(json.dumps(incompleta), encoding="utf-8")
    with pytest.raises(SystemExit, match="no define E6_pipeline"):
        benchmark.ejecutar(cfg, tmp_path / "s", solo=["E6"], silencioso=True)


# X6 - demos y prototipo terminan con código 0 (salida verificada [OK])
@pytest.mark.parametrize("script,args", [
    ("demo_primalidad.py", ["61", "561", "2047"]),
    ("demo_factorizacion.py", ["3233", "4294967297", "--semilla", "1"]),
    ("prototipo_gmpy2.py", ["--bits", "64", "256", "--rep", "1"]),
    ("demo_optimizacion.py", ["--bits", "128", "--mensajes", "2", "--rep", "1"]),
])
def test_X6_scripts(script, args):
    r = subprocess.run([sys.executable, str(SCRIPTS / script), *args],
                       capture_output=True, text=True, encoding="utf-8",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    assert r.returncode == 0, r.stdout + r.stderr
    assert "[OK]" in r.stdout
