"""Tablas y figuras a partir de resultados/<nombre>/E*.csv.

Uso (desde la raíz del repositorio):
    python scripts/graficar.py                       # resultados/preliminar
    python scripts/graficar.py resultados/definitivo

Escribe en la misma carpeta:
    figuras/E1_primalidad.{pdf,png} ... figuras/E6_pipeline.{pdf,png}
    tablas/E1.md, tablas/E1.tex, ...  (mediana entre instancias de la mediana
                                       de tiempo de cada instancia, en ms)
Requiere pandas y matplotlib.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]

PRIMERA, SEGUNDA = "#6B7280", "#0E6E6D"
COLORES = {"division_tentativa": PRIMERA, "miller_rabin": SEGUNDA,
           "miller_rabin_determinista": "#B4531B",
           "tentativa": PRIMERA, "rho": "#B4531B", "brent": SEGUNDA,
           "binaria": PRIMERA, "ventana": SEGUNDA, "directo": PRIMERA, "tcr": SEGUNDA,
           "sin_criba": PRIMERA, "con_criba": SEGUNDA, "base": PRIMERA, "optimizado": SEGUNDA}
NOMBRES = {"division_tentativa": "división de prueba", "miller_rabin": "Miller-Rabin",
           "miller_rabin_determinista": "MR determinista", "tentativa": "división de prueba",
           "rho": "Pollard Rho (Floyd)", "brent": "Brent", "binaria": "binaria",
           "ventana": "ventana", "directo": "directo", "tcr": "TCR",
           "sin_criba": "sin criba", "con_criba": "con criba", "base": "base",
           "optimizado": "optimizado"}
ORDEN = {"E1": ["division_tentativa", "miller_rabin", "miller_rabin_determinista"],
         "E2": ["tentativa", "rho", "brent"], "E3": ["binaria", "ventana"],
         "E4": ["directo", "tcr"], "E5": ["sin_criba", "con_criba"],
         "E6": ["base", "optimizado"]}
ARCHIVOS = {"E1": "E1_primalidad", "E2": "E2_factorizacion", "E3": "E3_exponenciacion",
            "E4": "E4_descifrado", "E5": "E5_generacion_primos", "E6": "E6_pipeline"}
TITULOS = {"E1": "E1 · Primalidad (primos)", "E2": "E2 · Factorización de semiprimos",
           "E3": "E3 · Exponenciación modular", "E4": "E4 · Descifrado (10 mensajes)",
           "E5": "E5 · Generación de un primo", "E6": "E6 · Pipeline RSA completo"}


def cargar(carpeta: Path, exp: str) -> pd.DataFrame | None:
    ruta = carpeta / f"{exp}.csv"
    if not ruta.is_file():
        return None
    df = pd.read_csv(ruta, keep_default_na=False)
    if exp == "E1":
        df = df[df["instancia"].str.startswith("primo")]
    if exp == "E2":                       # semiprimos de b o b-1 bits -> tamaño nominal
        df = df.assign(bits=(df["bits"] + 3) // 4 * 4)
    if exp == "E5":
        df = df.assign(llamadas_mr=df["extra"].str.split("=").str[1].astype(int))
    return df


def resumen(df: pd.DataFrame, valor: str = "ms_mediana") -> pd.DataFrame:
    """bits x algoritmo con la mediana entre instancias."""
    t = df.pivot_table(index="bits", columns="algoritmo", values=valor, aggfunc="median")
    return t[[c for c in ORDEN[df["experimento"].iloc[0]] if c in t.columns]]


def mejora_pareada(df: pd.DataFrame, lento: str, rapido: str) -> pd.Series:
    """Mediana, por tamaño, del cociente lento/rapido medido sobre la MISMA instancia."""
    t = df.pivot_table(index=["bits", "instancia"], columns="algoritmo",
                       values="ms_mediana", aggfunc="sum")
    if lento not in t.columns or rapido not in t.columns:
        return pd.Series(dtype=float)
    return (t[lento] / t[rapido]).dropna().groupby(level=0).median()


def _ejes(ax, titulo, xlabel, ylabel, log=True):
    ax.set_title(titulo, fontsize=10)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if log:
        ax.set_yscale("log")
    ax.grid(True, which="major", alpha=0.25)
    ax.legend(fontsize=8)


def _lineas(ax, t):
    for alg in t.columns:
        serie = t[alg].dropna()
        ax.plot(serie.index, serie.values, marker="o", ms=4, color=COLORES[alg],
                label=NOMBRES[alg])


def _guardar(fig, carpeta: Path, nombre: str) -> None:
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(carpeta / f"{nombre}.{ext}", dpi=160)
    plt.close(fig)


def figuras(carpeta: Path, datos: dict[str, pd.DataFrame]) -> list[str]:
    salida = carpeta / "figuras"
    salida.mkdir(parents=True, exist_ok=True)
    hechas = []
    for exp, df in datos.items():
        if exp in ("E1", "E2", "E4"):
            fig, ax = plt.subplots(figsize=(5, 3.4))
            _lineas(ax, resumen(df))
            _ejes(ax, TITULOS[exp], "bits", "tiempo (ms, escala log)")
        elif exp == "E3":
            fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.4))
            _lineas(a1, resumen(df, "mult_mod"))
            _ejes(a1, "E3 · Multiplicaciones modulares", "bits del exponente",
                  "multiplicaciones", log=False)
            _lineas(a2, resumen(df))
            a2.set_xscale("log", base=2)
            _ejes(a2, "E3 · Tiempo", "bits (escala log)", "ms (escala log)")
        elif exp == "E5":
            fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.4))
            _lineas(a1, resumen(df, "llamadas_mr"))
            _ejes(a1, "E5 · Llamadas a Miller-Rabin", "bits", "llamadas", log=False)
            _lineas(a2, resumen(df))
            _ejes(a2, "E5 · Tiempo", "bits", "ms (escala log)")
        else:                                   # E6: total y mejora por etapa
            fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.4))
            tot = df.pivot_table(index=["bits", "instancia"], columns="algoritmo",
                                 values="ms_mediana", aggfunc="sum").groupby("bits").median()
            _lineas(a1, tot[[c for c in ORDEN["E6"] if c in tot.columns]])
            _ejes(a1, "E6 · Pipeline completo (claves + cifrado + descifrado)", "bits de n",
                  "ms (escala log)")
            pares = df.pivot_table(index=["bits", "etapa", "instancia"], columns="algoritmo",
                                   values="ms_mediana", aggfunc="sum")
            cociente = (pares["base"] / pares["optimizado"]).groupby(level=[0, 1]).median()
            etapas = ["claves", "cifrado", "descifrado"]
            tonos = {"claves": "#0E6E6D", "cifrado": "#9CA3AF", "descifrado": "#B4531B"}
            tamanos = sorted(cociente.index.get_level_values(0).unique())
            ancho = 0.8 / len(etapas)
            for i, et in enumerate(etapas):
                valores = [cociente.get((b, et), float("nan")) for b in tamanos]
                a2.bar([k + i * ancho for k in range(len(tamanos))], valores, ancho,
                       color=tonos[et], label=et)
            a2.axhline(1, color="black", lw=0.8)
            a2.set_xticks([k + ancho for k in range(len(tamanos))], [str(b) for b in tamanos])
            _ejes(a2, "E6 · Mejora base / optimizado por etapa", "bits de n",
                  "veces más rápido", log=False)
        _guardar(fig, salida, ARCHIVOS[exp])
        hechas.append(exp)
    return hechas


def _tabla_md(t: pd.DataFrame, columnas: list[str]) -> str:
    cab = "| " + " | ".join(columnas) + " |"
    sep = "|" + "|".join("---:" for _ in columnas) + "|"
    filas = ["| " + " | ".join(str(v) for v in fila) + " |" for fila in t.itertuples(index=False)]
    return "\n".join([cab, sep, *filas]) + "\n"


def _tabla_tex(t: pd.DataFrame, columnas: list[str]) -> str:
    def esc(s):
        return str(s).replace("_", r"\_").replace("%", r"\%")
    lineas = [r"\begin{tabular}{" + "r" * len(columnas) + "}", r"\toprule",
              " & ".join(esc(c) for c in columnas) + r" \\", r"\midrule"]
    lineas += [" & ".join(esc(v) for v in fila) + r" \\" for fila in t.itertuples(index=False)]
    lineas += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(lineas) + "\n"


def tablas(carpeta: Path, datos: dict[str, pd.DataFrame]) -> None:
    salida = carpeta / "tablas"
    salida.mkdir(parents=True, exist_ok=True)
    for exp, df in datos.items():
        if exp == "E6":
            t = df.pivot_table(index=["bits", "etapa"], columns="algoritmo",
                               values="ms_mediana", aggfunc="median").reset_index()
            orden_etapa = {"claves": 0, "cifrado": 1, "descifrado": 2}
            t = t.sort_values(["bits", "etapa"], key=lambda s: s.map(orden_etapa)
                              if s.name == "etapa" else s)
            tot = df.pivot_table(index=["bits", "instancia"], columns="algoritmo",
                                 values="ms_mediana", aggfunc="sum").groupby("bits").median()
            tot = tot.reset_index().assign(etapa="TOTAL")
            t = pd.concat([t, tot]).sort_values(["bits"], kind="stable")
            pares = df.pivot_table(index=["bits", "etapa", "instancia"], columns="algoritmo",
                                   values="ms_mediana", aggfunc="sum")
            cociente = (pares["base"] / pares["optimizado"]).groupby(level=[0, 1]).median()
            total = mejora_pareada(df, "base", "optimizado")
            t["mejora"] = [f"{(total[b] if e == 'TOTAL' else cociente[(b, e)]):.2f}x"
                           for b, e in zip(t["bits"], t["etapa"])]
            for c in ("base", "optimizado"):
                t[c] = t[c].map(lambda v: f"{v:.2f}")
            cols = ["bits", "etapa", "base", "optimizado", "mejora"]
            t = t[cols]
        else:
            r = resumen(df)
            algs = list(r.columns)
            t = r.reset_index()
            if len(algs) >= 2:
                primero, mejor = algs[0], algs[1] if exp != "E2" else algs[-1]
                t["mejora"] = mejora_pareada(df, primero, mejor).reindex(r.index).map(
                    lambda v: "-" if pd.isna(v) else f"{v:.1f}x").values
                if exp == "E2" and {"rho", "brent"} <= set(algs):
                    t["rho/brent"] = mejora_pareada(df, "rho", "brent").reindex(r.index).map(
                        lambda v: "-" if pd.isna(v) else f"{v:.1f}x").values
            for c in algs:
                t[c] = t[c].map(lambda v: "-" if pd.isna(v) else f"{v:.3f}")
            if exp in ("E3", "E5"):
                extra = "mult_mod" if exp == "E3" else "llamadas_mr"
                r2 = resumen(df, extra)
                for c in r2.columns:
                    t[f"{extra} {c}"] = r2[c].values.astype(int)
            cols = list(t.columns)
        (salida / f"{exp}.md").write_text(_tabla_md(t, cols), encoding="utf-8", newline="\n")
        (salida / f"{exp}.tex").write_text(_tabla_tex(t, cols), encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("carpeta", nargs="?", default=str(RAIZ / "resultados" / "preliminar"))
    a = ap.parse_args(argv)
    carpeta = Path(a.carpeta)
    datos = {e: d for e in ORDEN if (d := cargar(carpeta, e)) is not None and len(d)}
    if not datos:
        print(f"no hay archivos E*.csv en {carpeta}", file=sys.stderr)
        return 1
    hechas = figuras(carpeta, datos)
    tablas(carpeta, datos)
    print(f"figuras y tablas de {', '.join(hechas)} en {carpeta / 'figuras'} y "
          f"{carpeta / 'tablas'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
