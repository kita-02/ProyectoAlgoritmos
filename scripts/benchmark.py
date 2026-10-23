"""Experimentos preliminares E1-E4: tiempo, operaciones y corrección.

Uso (desde la raíz del repositorio):
    python scripts/generar_instancias.py      # primero, si data/ está vacío
    python scripts/benchmark.py               # todos los experimentos
    python scripts/benchmark.py --solo E1 E3  # algunos

Lee config/experimentos.json y data/instancias/*.json y escribe
resultados/E1..E4.csv con rsa_edu.formatos.escribir_resultados.
Cada fila incluye si el resultado coincide con la referencia (columna "ok").
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from rsa_edu.aritmetica import (exp_modular_ingenua, exp_modular_rapida,  # noqa: E402
                                exp_modular_ventana)
from rsa_edu.contador import Contador  # noqa: E402
from rsa_edu.factorizacion import factorizar  # noqa: E402
from rsa_edu.formatos import cargar_instancias, escribir_resultados  # noqa: E402
from rsa_edu.primalidad import (division_tentativa, miller_rabin,  # noqa: E402
                                miller_rabin_determinista, LIMITE_DETERMINISTA)
from rsa_edu.rsa import descifrar, descifrar_crt, cifrar, generar_claves_aleatorias  # noqa: E402


def medir(f, repeticiones: int):
    tiempos, cont, res = [], Contador(), None
    for i in range(repeticiones):
        c = Contador()
        t0 = time.perf_counter()
        res = f(c)
        tiempos.append(time.perf_counter() - t0)
        if i == 0:
            cont = c
    return res, statistics.median(tiempos) * 1000, cont


def fila(exp, alg, inst, bits, res_ok, ms, c):
    return {"experimento": exp, "algoritmo": alg, "instancia": inst, "bits": bits,
            "ms_mediana": f"{ms:.4f}", "mult_mod": c.mult_mod, "div_mod": c.div_mod,
            "iteraciones": c.iteraciones, "ok": res_ok}


def e1(cfg, rep, semilla):
    datos = RAIZ / "data" / "instancias"
    insts = cargar_instancias(datos / "primos.json") + cargar_instancias(datos / "adversos.json")
    filas = []
    for inst in insts:
        n, esperado = inst["n"], inst.get("es_primo")
        algs = {"miller_rabin": lambda c: miller_rabin(n, cfg["rondas_mr"], random.Random(semilla), c)}
        if n < LIMITE_DETERMINISTA:
            algs["miller_rabin_determinista"] = lambda c: miller_rabin_determinista(n, c)
        if n.bit_length() <= cfg["max_bits_tentativa"]:
            algs["division_tentativa"] = lambda c: division_tentativa(n, c)
        for nombre, f in algs.items():
            r, ms, c = medir(f, rep)
            filas.append(fila("E1", nombre, n, n.bit_length(), r == esperado, ms, c))
    return filas


def e2(cfg, rep, semilla):
    filas = []
    for inst in cargar_instancias(RAIZ / "data" / "instancias" / "semiprimos.json"):
        n = inst["n"]
        if n.bit_length() > cfg["max_bits"]:
            continue
        esperado = sorted((int(inst["p"]), int(inst["q"])))
        for m in cfg["algoritmos"] + ["brent"]:
            r, ms, c = medir(lambda c, m=m: factorizar(n, m, random.Random(semilla), cont=c), rep)
            filas.append(fila("E2", m, n, n.bit_length(), r == esperado, ms, c))
    return filas


def e3(cfg, rep, semilla):
    mod, filas = int(cfg["modulo"]), []
    rng = random.Random(semilla)
    for lg in cfg["exponentes_log2"]:
        e = (1 << lg) - 1
        base = rng.randrange(2, mod)
        ref = pow(base, e, mod)
        algs = {"rapida": lambda c: exp_modular_rapida(base, e, mod, c),
                "ventana": lambda c: exp_modular_ventana(base, e, mod, cont=c)}
        if lg <= 20:
            algs["ingenua"] = lambda c: exp_modular_ingenua(base, e, mod, c)
        for nombre, f in algs.items():
            r, ms, c = medir(f, rep)
            filas.append(fila("E3", nombre, f"2^{lg}-1", lg, r == ref, ms, c))
    return filas


def e4(cfg, rep, semilla):
    rng, filas = random.Random(semilla), []
    for bits in cfg["bits"]:
        kp = generar_claves_aleatorias(bits, rng=rng)
        mensajes = [rng.randrange(0, kp.publica.n) for _ in range(cfg["mensajes_por_clave"])]
        cifrados = [cifrar(m, kp.publica) for m in mensajes]
        for nombre, f in (("descifrar", descifrar), ("descifrar_crt", descifrar_crt)):
            r, ms, c = medir(lambda c: [f(x, kp.privada, cont=c) for x in cifrados], rep)
            filas.append(fila("E4", nombre, f"{len(cifrados)} mensajes", bits, r == mensajes, ms, c))
    return filas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--solo", nargs="*", default=["E1", "E2", "E3", "E4"])
    ap.add_argument("--salida", default=str(RAIZ / "resultados"))
    a = ap.parse_args()
    cfg = json.loads((RAIZ / "config" / "experimentos.json").read_text(encoding="utf-8"))
    rep, semilla = cfg["repeticiones"], cfg["semilla"]
    tareas = {"E1": (e1, "E1_primalidad"), "E2": (e2, "E2_factorizacion"),
              "E3": (e3, "E3_exponenciacion"), "E4": (e4, "E4_rsa")}
    for clave in a.solo:
        f, seccion = tareas[clave]
        filas = f(cfg[seccion], rep, semilla)
        ruta = Path(a.salida) / f"{clave}.csv"
        escribir_resultados(ruta, filas)
        fallas = sum(1 for x in filas if not x["ok"])
        print(f"{clave}: {len(filas)} mediciones -> {ruta}  ({fallas} discrepancias)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
