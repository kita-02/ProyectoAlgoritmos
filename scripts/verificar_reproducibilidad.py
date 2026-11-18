"""Experimento piloto: ¿el procedimiento produce datos correctos, coherentes y reproducibles?

Uso (desde la raíz del repositorio):
    python scripts/verificar_reproducibilidad.py                     # config/piloto.json
    python scripts/verificar_reproducibilidad.py --config config/piloto.json --tolerancia 0.25

Ejecuta el benchmark DOS veces con la misma configuración (en
resultados/<nombre>/corrida_1 y corrida_2) y comprueba:

  1. Correctos:     todas las filas tienen ok = True (resultado igual a la
                    referencia: sympy, pow o el mensaje original) y
                    estable = True (todas las repeticiones dieron lo mismo).
  2. Reproducibles: las dos corridas tienen las mismas filas y EXACTAMENTE
                    los mismos conteos de operaciones (mult_mod, div_mod, mcd,
                    iteraciones, llamadas a MR); los tiempos difieren menos
                    que la tolerancia (por defecto 25 %) en la mayoría de filas.
  3. Coherentes:    los datos respetan propiedades que la teoría garantiza
                    (p. ej. la binaria hace a lo más 2·bits multiplicaciones,
                    la criba reduce las llamadas a Miller-Rabin, etc.).

Escribe resultados/<nombre>/reproducibilidad.md y termina con código 0 solo
si las tres comprobaciones se cumplen.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import benchmark  # noqa: E402

CLAVE = ("experimento", "algoritmo", "etapa", "instancia", "bits")
DETERMINISTAS = ("mult_mod", "div_mod", "mcd", "iteraciones", "extra", "ok")


def leer(carpeta: Path) -> dict[tuple, dict]:
    filas = {}
    for ruta in sorted(carpeta.glob("E*.csv")):
        with ruta.open(newline="", encoding="utf-8") as fh:
            for f in csv.DictReader(fh):
                filas[tuple(f[c] for c in CLAVE)] = f
    return filas


def _llamadas(f: dict) -> int:
    return int(f["extra"].split("=")[1])


def coherencia(filas: dict[tuple, dict]) -> list[tuple[str, bool, str]]:
    """Propiedades teóricas que los datos deben cumplir."""
    por_exp = defaultdict(list)
    for f in filas.values():
        por_exp[f["experimento"]].append(f)
    res = []

    def agrega(nombre, filas_ok, total, detalle=""):
        res.append((nombre, filas_ok == total, f"{filas_ok}/{total} {detalle}".strip()))

    e1 = [f for f in por_exp["E1"] if f["algoritmo"] == "division_tentativa"]
    agrega("E1: la división de prueba hace a lo más sqrt(n)/6 + 1 iteraciones",
           sum(int(f["iteraciones"]) <= 2 ** (int(f["bits"]) / 2) / 6 + 1 for f in e1), len(e1))

    e3 = defaultdict(dict)
    for f in por_exp["E3"]:
        e3[(f["bits"], f["instancia"])][f["algoritmo"]] = int(f["mult_mod"])
    agrega("E3: la binaria hace a lo más 2·bits multiplicaciones",
           sum(v["binaria"] <= 2 * int(k[0]) for k, v in e3.items()), len(e3))
    agrega("E3: la ventana hace menos multiplicaciones que la binaria",
           sum(v["ventana"] < v["binaria"] for v in e3.values()), len(e3))

    e4 = defaultdict(dict)
    for f in por_exp["E4"]:
        e4[(f["bits"], f["instancia"])][f["algoritmo"]] = f
    agrega("E4: el TCR descifra en menos tiempo que el directo",
           sum(float(v["tcr"]["ms_mediana"]) < float(v["directo"]["ms_mediana"])
               for v in e4.values()), len(e4))

    e5 = defaultdict(dict)
    for f in por_exp["E5"]:
        e5[(f["bits"], f["instancia"])][f["algoritmo"]] = _llamadas(f)
    agrega("E5: la criba reduce las llamadas a Miller-Rabin",
           sum(v["con_criba"] < v["sin_criba"] for v in e5.values()), len(e5))

    e6 = defaultdict(dict)
    for f in por_exp["E6"]:
        e6[(f["bits"], f["instancia"], f["etapa"])][f["algoritmo"]] = f
    cif = [v for k, v in e6.items() if k[2] == "cifrado"]
    agrega("E6: el cifrado hace las mismas multiplicaciones en base y optimizado",
           sum(v["base"]["mult_mod"] == v["optimizado"]["mult_mod"] for v in cif), len(cif))
    des = [v for k, v in e6.items() if k[2] == "descifrado"]
    agrega("E6: el descifrado optimizado es más rápido que el base",
           sum(float(v["optimizado"]["ms_mediana"]) < float(v["base"]["ms_mediana"])
               for v in des), len(des))
    return res


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(RAIZ / "config" / "piloto.json"))
    ap.add_argument("--tolerancia", type=float, default=0.25,
                    help="diferencia relativa de tiempo aceptada entre corridas")
    ap.add_argument("--salida", help="carpeta (por defecto resultados/<nombre>)")
    a = ap.parse_args(argv)
    ruta_cfg = Path(a.config).resolve()
    cfg = json.loads(ruta_cfg.read_text(encoding="utf-8"))
    base = Path(a.salida) if a.salida else RAIZ / "resultados" / cfg["nombre"]

    carpetas = []
    for i in (1, 2):
        print(f"corrida {i} de 2 ...", flush=True)
        carpetas.append(benchmark.ejecutar(ruta_cfg, base / f"corrida_{i}", silencioso=True))
    c1, c2 = leer(carpetas[0]), leer(carpetas[1])

    # 1. Correctos
    malas = [k for k, f in {**c1, **c2}.items() if f["ok"] != "True" or f["estable"] != "True"]
    correcto = not malas

    # 2. Reproducibles
    mismas_filas = c1.keys() == c2.keys()
    distintas = [k for k in c1.keys() & c2.keys()
                 if any(c1[k][c] != c2[k][c] for c in DETERMINISTAS)]
    difs = []
    for k in c1.keys() & c2.keys():
        t1, t2 = float(c1[k]["ms_mediana"]), float(c2[k]["ms_mediana"])
        if max(t1, t2) >= 0.05:            # bajo 50 µs domina el ruido del reloj
            difs.append(abs(t2 - t1) / max(t1, t2))
    dentro = sum(d <= a.tolerancia for d in difs)
    fraccion = dentro / len(difs) if difs else 1.0
    cvs = [float(f["cv"]) for f in c1.values()]
    reproducible = mismas_filas and not distintas and fraccion >= 0.9

    # 3. Coherentes
    checks = coherencia(c1)
    coherente = all(ok for _, ok, _ in checks)

    def marca(x: bool) -> str:
        return "[OK]" if x else "[FALLA]"

    lineas = [f"# Verificación del experimento piloto ({cfg['nombre']})", "",
              f"Configuración: `{ruta_cfg.name}` · semilla {cfg['semilla']} · "
              f"{cfg['repeticiones']} repeticiones · dos corridas independientes", "",
              "## 1. Correctos", "",
              f"- Filas medidas por corrida: {len(c1)}",
              f"- Filas con resultado incorrecto o inestable: {len(malas)} {marca(correcto)}", "",
              "## 2. Reproducibles", "",
              f"- Mismas filas en ambas corridas: {'sí' if mismas_filas else 'no'} "
              f"{marca(mismas_filas)}",
              f"- Filas con conteos de operaciones distintos: {len(distintas)} "
              f"{marca(not distintas)}",
              f"- Tiempos con diferencia ≤ {a.tolerancia:.0%} entre corridas: "
              f"{dentro}/{len(difs)} ({fraccion:.0%}) {marca(fraccion >= 0.9)}",
              f"- Diferencia relativa mediana entre corridas: "
              f"{statistics.median(difs) if difs else 0:.1%}",
              f"- Coeficiente de variación mediano dentro de una corrida: "
              f"{statistics.median(cvs):.1%}", "",
              "## 3. Coherentes con la teoría", ""]
    lineas += [f"- {n}: {d} {marca(ok)}" for n, ok, d in checks]
    todo = correcto and reproducible and coherente
    lineas += ["", f"**Resultado: {'procedimiento válido' if todo else 'revisar'} "
               f"{marca(todo)}**", ""]
    informe = "\n".join(lineas)
    (base / "reproducibilidad.md").write_text(informe, encoding="utf-8", newline="\n")
    print(informe)
    return 0 if todo else 1


if __name__ == "__main__":
    sys.exit(main())
