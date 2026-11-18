"""Experimentos E1-E6: tiempo, operaciones, memoria y corrección.

Uso (desde la raíz del repositorio):
    python scripts/benchmark.py --config config/piloto.json       # piloto (~10 s)
    python scripts/benchmark.py --config config/preliminar.json   # preliminar (~4 min)
    python scripts/benchmark.py                                   # definitivo
    python scripts/benchmark.py --config config/preliminar.json --solo E4 E6

Experimentos (primera frente a segunda alternativa de cada etapa):
    E1 primalidad       división de prueba / Miller-Rabin / MR determinista
    E2 factorización    división de prueba / Pollard Rho (Floyd) / Brent
    E3 exponenciación   binaria / ventana deslizante
    E4 descifrado       directo / Teorema Chino del Resto
    E5 generar primos   sin criba / con criba de primos < 2000
    E6 pipeline RSA     base / optimizado, por etapa (claves, cifrado, descifrado)

Procedimiento de medición de cada caso (función medir):
    1. Una ejecución de conteo, NO cronometrada, con Contador (operaciones)
       y tracemalloc (memoria pico).  Su resultado se verifica contra una
       referencia externa: sympy, pow() o el mensaje original.
    2. ``calentamiento`` ejecuciones descartadas.
    3. ``repeticiones`` ejecuciones cronometradas con time.perf_counter, sin
       contador y con el recolector de basura desactivado; cada una debe dar
       el mismo resultado que la de conteo (columna "estable").
Se guarda la mediana, el mínimo, el máximo y el coeficiente de variación.

Salida: resultados/<nombre de la configuración>/E1.csv ... E6.csv y
metadatos.json (fecha, Python, sistema, semilla, hash de la configuración).
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import platform
import random
import statistics
import subprocess
import sys
import time
import tracemalloc
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

import sympy  # noqa: E402  (oráculo de referencia, solo para verificar)

import rsa_edu.primalidad as primalidad  # noqa: E402
from rsa_edu import __version__  # noqa: E402
from rsa_edu.aritmetica import exp_modular_rapida, exp_modular_ventana  # noqa: E402
from rsa_edu.contador import Contador  # noqa: E402
from rsa_edu.factorizacion import factorizar  # noqa: E402
from rsa_edu.formatos import cargar_instancias, escribir_resultados  # noqa: E402
from rsa_edu.primalidad import (LIMITE_DETERMINISTA, division_tentativa,  # noqa: E402
                                generar_primo, miller_rabin, miller_rabin_determinista)
from rsa_edu.rsa import (cifrar, descifrar, descifrar_crt,  # noqa: E402
                         generar_claves_aleatorias)

COLUMNAS = ["experimento", "algoritmo", "etapa", "instancia", "bits", "repeticiones",
            "ms_mediana", "ms_min", "ms_max", "cv", "mult_mod", "div_mod", "mcd",
            "iteraciones", "kib_pico", "extra", "ok", "estable"]


# ---------------------------------------------------------------------------
# Medición
# ---------------------------------------------------------------------------
def medir(f, rep: int, calentamiento: int) -> tuple[object, dict]:
    """f(cont) -> resultado.  Devuelve (resultado, métricas)."""
    cont = Contador()
    tracemalloc.start()
    resultado = f(cont)
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    for _ in range(calentamiento):
        f(None)

    tiempos, estable = [], True
    for _ in range(rep):
        gc.collect()
        gc.disable()
        try:
            t0 = time.perf_counter()
            r = f(None)
            tiempos.append(time.perf_counter() - t0)
        finally:
            gc.enable()
        estable &= r == resultado

    media = statistics.fmean(tiempos)
    cv = statistics.stdev(tiempos) / media if len(tiempos) > 1 and media > 0 else 0.0
    return resultado, {
        "repeticiones": rep,
        "ms_mediana": round(statistics.median(tiempos) * 1000, 5),
        "ms_min": round(min(tiempos) * 1000, 5),
        "ms_max": round(max(tiempos) * 1000, 5),
        "cv": round(cv, 4),
        "mult_mod": cont.mult_mod, "div_mod": cont.div_mod, "mcd": cont.mcd,
        "iteraciones": cont.iteraciones,
        "kib_pico": round(pico / 1024, 2),
        "estable": estable,
    }


def fila(exp, alg, inst, bits, metricas, ok, etapa="", extra=""):
    return {"experimento": exp, "algoritmo": alg, "etapa": etapa, "instancia": inst,
            "bits": bits, **metricas, "extra": extra, "ok": ok}


def _orden(f: dict) -> dict:
    return {c: f[c] for c in COLUMNAS}


# ---------------------------------------------------------------------------
# Experimentos
# ---------------------------------------------------------------------------
def e1(cfg, rep, cal, semilla, datos):
    """Primalidad sobre primos (peor caso) y adversos (Carmichael, spsp)."""
    insts = cargar_instancias(datos / "primos.json") + cargar_instancias(datos / "adversos.json")
    filas = []
    for k, inst in enumerate(insts):
        n = inst["n"]
        if n.bit_length() > cfg["max_bits"]:
            continue
        ref = sympy.isprime(n)
        clase = inst.get("clase", "primo")
        algs = {"miller_rabin":
                lambda c: miller_rabin(n, cfg["rondas_mr"], random.Random(semilla), c)}
        if n < LIMITE_DETERMINISTA:
            algs["miller_rabin_determinista"] = lambda c: miller_rabin_determinista(n, c)
        if n.bit_length() <= cfg["max_bits_tentativa"]:
            algs["division_tentativa"] = lambda c: division_tentativa(n, c)
        for nombre in cfg["algoritmos"]:
            if nombre in algs:
                r, m = medir(algs[nombre], rep, cal)
                filas.append(fila("E1", nombre, f"{clase}#{k}", n.bit_length(), m, r == ref))
    return filas


def e2(cfg, rep, cal, semilla, datos):
    """Factorización de semiprimos balanceados (p y q de bits/2)."""
    filas = []
    for k, inst in enumerate(cargar_instancias(datos / "semiprimos.json")):
        n = inst["n"]
        if n.bit_length() > cfg["max_bits"]:
            continue
        ref = sorted(sympy.factorint(n, multiple=True))
        for nombre in cfg["algoritmos"]:
            if nombre == "tentativa" and n.bit_length() > cfg["max_bits_tentativa"]:
                continue
            r, m = medir(lambda c, a=nombre: factorizar(n, a, random.Random(semilla + k), cont=c),
                         rep, cal)
            filas.append(fila("E2", nombre, f"semiprimo#{k}", n.bit_length(), m, r == ref))
    return filas


def e3(cfg, rep, cal, semilla, datos):
    """Exponenciación con módulo, base y exponente aleatorios de b bits."""
    rng, filas = random.Random(semilla), []
    funciones = {"binaria": lambda b, e, n, c: exp_modular_rapida(b, e, n, c),
                 "ventana": lambda b, e, n, c: exp_modular_ventana(b, e, n, cont=c)}
    for bits in cfg["bits"]:
        for k in range(cfg["instancias_por_tamano"]):
            n = rng.getrandbits(bits) | (1 << (bits - 1)) | 1
            b = rng.randrange(2, n)
            e = rng.getrandbits(bits) | (1 << (bits - 1))
            ref = pow(b, e, n)
            for nombre in cfg["algoritmos"]:
                f = funciones[nombre]
                r, m = medir(lambda c, f=f: f(b, e, n, c), rep, cal)
                filas.append(fila("E3", nombre, f"aleatoria#{k}", bits, m, r == ref))
    return filas


def e4(cfg, rep, cal, semilla, datos):
    """Descifrado de ``mensajes_por_clave`` mensajes con cada clave."""
    filas = []
    for bits in cfg["bits"]:
        for k in range(cfg["claves_por_tamano"]):
            rng = random.Random(semilla * 1000 + bits + k)
            kp = generar_claves_aleatorias(bits, rng=rng)
            mensajes = [rng.randrange(0, kp.publica.n) for _ in range(cfg["mensajes_por_clave"])]
            cifrados = [pow(m, kp.publica.e, kp.publica.n) for m in mensajes]
            for nombre, f in (("directo", descifrar), ("tcr", descifrar_crt)):
                r, m = medir(lambda c, f=f: [f(x, kp.privada, cont=c) for x in cifrados],
                             rep, cal)
                filas.append(fila("E4", nombre, f"clave#{k}", bits, m, r == mensajes,
                                  extra=f"mensajes={len(mensajes)}"))
    return filas


def e5(cfg, rep, cal, semilla, datos):
    """Generación de un primo de b bits con y sin criba (misma semilla)."""
    filas = []
    for bits in cfg["bits"]:
        for k in range(cfg["instancias_por_tamano"]):
            s = semilla * 100 + bits + k
            primos = {}
            for nombre, criba in (("sin_criba", False), ("con_criba", True)):
                llamadas = [0]

                def f(c, criba=criba, llamadas=llamadas):
                    if c is None:
                        return generar_primo(bits, random.Random(s), criba=criba)
                    original = primalidad.es_primo

                    def contar(*args, **kw):
                        llamadas[0] += 1
                        return original(*args, **kw)
                    primalidad.es_primo = contar
                    try:
                        return generar_primo(bits, random.Random(s), criba=criba, cont=c)
                    finally:
                        primalidad.es_primo = original

                r, m = medir(f, rep, cal)
                primos[nombre] = r
                ok = sympy.isprime(r) and r.bit_length() == bits
                filas.append(fila("E5", nombre, f"semilla#{k}", bits, m, ok,
                                  extra=f"llamadas_mr={llamadas[0]}"))
            if primos["sin_criba"] != primos["con_criba"]:
                for x in filas[-2:]:
                    x["ok"] = False
    return filas


CONFIG_E6 = {"base": dict(criba=False, crt=False, ventana=False),
             "optimizado": dict(criba=True, crt=True, ventana=True)}


def e6(cfg, rep, cal, semilla, datos):
    """Pipeline completo base frente a optimizado, etapa por etapa."""
    filas = []
    for bits in cfg["bits"]:
        for k in range(cfg["semillas_por_tamano"]):
            s = semilla * 10 + bits + k
            referencia = {}
            for nombre, op in CONFIG_E6.items():
                r_cl, m_cl = medir(lambda c, op=op: generar_claves_aleatorias(
                    bits, rng=random.Random(s), criba=op["criba"], cont=c), rep, cal)
                pub, priv = r_cl.publica, r_cl.privada
                rng_m = random.Random(s + 1)
                mensajes = [rng_m.randrange(0, pub.n) for _ in range(cfg["mensajes"])]
                r_ci, m_ci = medir(lambda c: [cifrar(x, pub, cont=c) for x in mensajes], rep, cal)
                fdes = descifrar_crt if op["crt"] else descifrar
                r_de, m_de = medir(lambda c, fd=fdes, v=op["ventana"]:
                                   [fd(x, priv, ventana=v, cont=c) for x in r_ci], rep, cal)
                if not referencia:
                    referencia = {"claves": r_cl, "cifrados": r_ci}
                ok_cl = r_cl == referencia["claves"]
                ok_ci = r_ci == referencia["cifrados"] and r_ci == [pow(x, pub.e, pub.n)
                                                                    for x in mensajes]
                ok_de = r_de == mensajes
                inst = f"semilla#{k}"
                filas.append(fila("E6", nombre, inst, bits, m_cl, ok_cl, etapa="claves"))
                filas.append(fila("E6", nombre, inst, bits, m_ci, ok_ci, etapa="cifrado",
                                  extra=f"mensajes={len(mensajes)}"))
                filas.append(fila("E6", nombre, inst, bits, m_de, ok_de, etapa="descifrado",
                                  extra=f"mensajes={len(mensajes)}"))
    return filas


TAREAS = {"E1": (e1, "E1_primalidad"), "E2": (e2, "E2_factorizacion"),
          "E3": (e3, "E3_exponenciacion"), "E4": (e4, "E4_descifrado"),
          "E5": (e5, "E5_generacion_primos"), "E6": (e6, "E6_pipeline")}


# ---------------------------------------------------------------------------
def _commit() -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=RAIZ,
                           capture_output=True, text=True, timeout=5)
        return r.stdout.strip() or "desconocido"
    except (OSError, subprocess.SubprocessError):
        return "desconocido"


def ejecutar(ruta_config: Path, salida: Path | None = None,
             solo: list[str] | None = None, silencioso: bool = False) -> Path:
    texto = ruta_config.read_text(encoding="utf-8")
    cfg = json.loads(texto)
    rep, cal, semilla = cfg["repeticiones"], cfg.get("calentamiento", 1), cfg["semilla"]
    datos = RAIZ / cfg.get("instancias", "data/instancias")
    salida = Path(salida) if salida else RAIZ / "resultados" / cfg["nombre"]
    solo = solo or [k for k in TAREAS if TAREAS[k][1] in cfg]

    inicio = time.perf_counter()
    resumen = {}
    for clave in solo:
        f, seccion = TAREAS[clave]
        if seccion not in cfg:
            raise SystemExit(f"la configuración no define {seccion}")
        t0 = time.perf_counter()
        filas = [_orden(x) for x in f(cfg[seccion], rep, cal, semilla, datos)]
        escribir_resultados(salida / f"{clave}.csv", filas)
        fallas = sum(1 for x in filas if not (x["ok"] and x["estable"]))
        resumen[clave] = {"filas": len(filas), "fallas": fallas,
                          "segundos": round(time.perf_counter() - t0, 1)}
        if not silencioso:
            print(f"{clave}: {len(filas):4d} filas  {fallas} fallas  "
                  f"{resumen[clave]['segundos']:7.1f} s  -> {salida / (clave + '.csv')}")

    meta = {
        "configuracion": str(ruta_config.relative_to(RAIZ) if ruta_config.is_relative_to(RAIZ)
                             else ruta_config),
        "sha256_configuracion": hashlib.sha256(texto.encode()).hexdigest()[:16],
        "nombre": cfg["nombre"], "semilla": semilla, "repeticiones": rep,
        "calentamiento": cal, "fecha": datetime.now().isoformat(timespec="seconds"),
        "rsa_edu": __version__, "commit": _commit(),
        "python": platform.python_version(), "implementacion": platform.python_implementation(),
        "sistema": platform.platform(), "procesador": platform.processor() or platform.machine(),
        "experimentos": resumen, "segundos_total": round(time.perf_counter() - inicio, 1),
    }
    (salida / "metadatos.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
                                           encoding="utf-8", newline="\n")
    return salida


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(RAIZ / "config" / "experimentos.json"))
    ap.add_argument("--solo", nargs="*", choices=list(TAREAS))
    ap.add_argument("--salida", help="carpeta de salida (por defecto resultados/<nombre>)")
    a = ap.parse_args(argv)
    salida = ejecutar(Path(a.config).resolve(), a.salida, a.solo)
    meta = json.loads((salida / "metadatos.json").read_text(encoding="utf-8"))
    fallas = sum(v["fallas"] for v in meta["experimentos"].values())
    print(f"total: {meta['segundos_total']} s, {fallas} fallas, metadatos en "
          f"{salida / 'metadatos.json'}")
    return 0 if fallas == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
