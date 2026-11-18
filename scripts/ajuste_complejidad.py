"""Compara los resultados medidos con el análisis teórico de complejidad.

Uso (desde la raíz del repositorio):
    python scripts/ajuste_complejidad.py                       # resultados/preliminar
    python scripts/ajuste_complejidad.py resultados/definitivo

Para cada alternativa ajusta por mínimos cuadrados el modelo que predice la
teoría y compara el parámetro obtenido con el teórico:

  * Crecimiento exponencial en los bits b (algoritmos sobre n = 2^b):
        log2(ms) = a + s·b      división de prueba O(sqrt n)  -> s = 1/2
                                Pollard Rho / Brent O(n^1/4)  -> s = 1/4
  * Crecimiento polinomial en b (aritmética con enteros de b bits):
        log(ms) = a + alfa·log(b)
        exponenciación y descifrado: b multiplicaciones de b bits;
        con multiplicación escolar M(b) = b^2 (CPython la usa bajo ~2100
        bits; encima usa Karatsuba, b^1,585) el exponente asintótico es
        alfa = 3.  Cada multiplicación tiene además un costo fijo del
        intérprete, por eso con b de cientos de bits se observa entre 2 y 3.
  * Conteo de multiplicaciones (independiente del hardware):
        mult = c·b              binaria: c = 1,5 (b cuadrados + b/2 productos)
                                ventana: c = 1 + 1/(k+1)  (k = ancho de ventana)
  * Criba (E5): fracción de candidatos impares sin factores primos < 2000
        = prod_{3 <= p < 2000} (1 - 1/p)     (Mertens)  ->  ~85 % menos MR.
        (con y sin criba se prueban los MISMOS candidatos, así el cociente
        es estable aunque el número de candidatos varíe mucho entre semillas)
  * TCR (E4): mejora directo/TCR = 2^beta con beta = 2 (escolar) -> hasta 4.

Escribe ajustes.csv y ajustes.md en la carpeta de resultados.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from graficar import cargar, mejora_pareada, resumen  # noqa: E402
from rsa_edu.aritmetica import ventana_optima  # noqa: E402
from rsa_edu.primalidad import PRIMOS_PEQUENOS  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]


def recta(x: list[float], y: list[float]) -> tuple[float, float, float]:
    """Mínimos cuadrados y = a + s·x.  Devuelve (s, a, R^2)."""
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((xi - mx) ** 2 for xi in x)
    sxy = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    s = sxy / sxx
    a = my - s * mx
    ss_tot = sum((yi - my) ** 2 for yi in y)
    ss_res = sum((yi - (a + s * xi)) ** 2 for xi, yi in zip(x, y))
    return s, a, (1 - ss_res / ss_tot) if ss_tot else 1.0


def fila(exp, alg, modelo, rango, obs, teo_txt, lo, hi, r2, nota=""):
    return {"experimento": exp, "algoritmo": alg, "modelo": modelo, "rango": rango,
            "observado": round(obs, 3), "teorico": teo_txt,
            "r2": "-" if r2 is None else round(r2, 4),
            "coincide": "sí" if lo <= obs <= hi else "no", "nota": nota}


def ajustes(carpeta: Path) -> list[dict]:
    filas = []
    datos = {e: cargar(carpeta, e) for e in ("E1", "E2", "E3", "E4", "E5", "E6")}

    # Exponenciales en bits: log2(ms) = a + s·b
    casos = [("E1", "division_tentativa", 24, 0.5), ("E2", "tentativa", 24, 0.5),
             ("E2", "rho", 32, 0.25), ("E2", "brent", 32, 0.25)]
    for exp, alg, desde, teo in casos:
        df = datos[exp]
        if df is None or alg not in set(df["algoritmo"]):
            continue
        serie = resumen(df)[alg].dropna()
        serie = serie[serie.index >= desde]
        if len(serie) < 3:
            continue
        s, _, r2 = recta(list(serie.index), [math.log2(v) for v in serie.values])
        filas.append(fila(exp, alg, "log2(ms) = a + s·b", f"{serie.index.min()}-{serie.index.max()}",
                          s, f"s = {teo}", teo * 0.8, teo * 1.2, r2,
                          f"cada bit multiplica el tiempo por {2 ** s:.2f} (teoría {2 ** teo:.2f})"))

    # Polinomiales en bits: log(ms) = a + alfa·log(b)
    for exp, alg in (("E3", "binaria"), ("E3", "ventana"), ("E4", "directo"), ("E4", "tcr")):
        df = datos[exp]
        if df is None:
            continue
        serie = resumen(df)[alg].dropna()
        if len(serie) < 3:
            continue
        alfa, _, r2 = recta([math.log(b) for b in serie.index],
                            [math.log(v) for v in serie.values])
        filas.append(fila(exp, alg, "log(ms) = a + alfa·log(b)",
                          f"{serie.index.min()}-{serie.index.max()}", alfa,
                          "alfa -> 3; entre 2 y 3 con costo fijo", 2.0, 3.1, r2,
                          "b multiplicaciones de b bits (escolar); el costo fijo por "
                          "operación del intérprete baja el exponente observado"))

    # Conteo de multiplicaciones: mult = c·b
    df = datos["E3"]
    if df is not None:
        for alg in ("binaria", "ventana"):
            serie = resumen(df, "mult_mod")[alg].dropna()
            c = sum(serie.values / serie.index) / len(serie)
            if alg == "binaria":
                filas.append(fila("E3", alg, "mult = c·b", f"{serie.index.min()}-{serie.index.max()}",
                                  c, "c = 1,5", 1.4, 1.6, None, "promedio de mult/b"))
            else:
                teo = [1 + 1 / (ventana_optima(b) + 1) + 2 ** (ventana_optima(b) - 1) / b
                       for b in serie.index]
                filas.append(fila("E3", alg, "mult = c·b", f"{serie.index.min()}-{serie.index.max()}",
                                  c, f"c = 1 + 1/(k+1) + 2^(k-1)/b ≈ {sum(teo) / len(teo):.3f}",
                                  min(teo) * 0.95, max(teo) * 1.05, None, "k = ventana_optima(b)"))

    # TCR: mejora = directo / tcr (mediana de cocientes sobre la misma clave)
    df = datos["E4"]
    if df is not None:
        for b, v in mejora_pareada(df, "directo", "tcr").items():
            filas.append(fila("E4", "directo/tcr", "mejora", str(b), v,
                              "hasta 2^2 = 4", 1.5, 4.2, None,
                              "se acerca a 4 al crecer b (el costo fijo pesa menos)"))

    # Criba: fracción de llamadas a MR que sobreviven
    df = datos["E5"]
    if df is not None:
        mertens = math.prod(1 - 1 / p for p in PRIMOS_PEQUENOS if p > 2)
        r = resumen(df, "llamadas_mr")
        suma = r.sum()
        frac = suma["con_criba"] / suma["sin_criba"]
        filas.append(fila("E5", "con/sin criba", "fracción de llamadas a MR", "todas",
                          frac, f"prod(1-1/p) = {mertens:.3f}", mertens * 0.7, mertens * 1.3, None,
                          f"reducción observada {1 - frac:.1%}, teórica {1 - mertens:.1%}"))

    # Pipeline: exponente polinomial del total
    df = datos["E6"]
    if df is not None:
        tot = df.pivot_table(index=["bits", "instancia"], columns="algoritmo",
                             values="ms_mediana", aggfunc="sum").groupby("bits").median()
        if len(tot) >= 3:
            for alg in ("base", "optimizado"):
                alfa, _, r2 = recta([math.log(b) for b in tot.index],
                                    [math.log(v) for v in tot[alg]])
                filas.append(fila("E6", alg, "log(ms) = a + alfa·log(b)",
                                  f"{tot.index.min()}-{tot.index.max()}", alfa,
                                  "alfa -> 4; menor con costo fijo", 2.5, 4.2, r2,
                                  "generar primos: O(b) candidatos × MR O(b^3)"))
        for b, v in mejora_pareada(df, "base", "optimizado").items():
            filas.append(fila("E6", "base/optimizado", "mejora total", str(b),
                              v, "> 1", 1.0, 1e9, None,
                              "mismo resultado, menos tiempo"))
    return filas


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("carpeta", nargs="?", default=str(RAIZ / "resultados" / "preliminar"))
    a = ap.parse_args(argv)
    carpeta = Path(a.carpeta)
    filas = ajustes(carpeta)
    if not filas:
        print(f"no hay datos suficientes en {carpeta}", file=sys.stderr)
        return 1
    df = pd.DataFrame(filas)
    df.to_csv(carpeta / "ajustes.csv", index=False)
    cols = list(df.columns)
    md = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    md += ["| " + " | ".join(str(v) for v in f.values()) + " |" for f in filas]
    (carpeta / "ajustes.md").write_text("# Teoría frente a mediciones\n\n" + "\n".join(md) + "\n",
                                        encoding="utf-8", newline="\n")
    with pd.option_context("display.width", 200, "display.max_columns", 20,
                           "display.max_colwidth", 60):
        print(df[["experimento", "algoritmo", "modelo", "rango", "observado", "teorico",
                  "r2", "coincide"]].to_string(index=False))
    print(f"\n{(df['coincide'] == 'sí').sum()}/{len(df)} ajustes coinciden con la teoría; "
          f"detalle en {carpeta / 'ajustes.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
