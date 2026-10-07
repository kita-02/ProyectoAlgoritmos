"""Demostración de primalidad: compara la división de prueba con Miller-Rabin.

Modo de uso (ejecutar desde la raíz del repositorio):
    python scripts/demo_primalidad.py                  # usa la instancia conocida
    python scripts/demo_primalidad.py 97 1105 7919     # números dados en la sesión
    python scripts/demo_primalidad.py 2147483647 --rondas 5 --semilla 2026

Cómo verificar la salida:
    * ambos métodos tienen que llegar al mismo resultado;
    * cuando n es compuesto se imprime un divisor, para revisarlo a mano.
"""
from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from rsa_edu.primalidad import division_tentativa, miller_rabin  # noqa: E402

INSTANCIA_CONOCIDA = [61, 53, 561, 3233]     # p, q, un Carmichael y el n del Avance 1
LIMITE_DIVISION = 2**44                      # cerca de 1 s; sobre este valor dividir es muy lento


def menor_divisor(n: int) -> int | None:
    """Busca el menor divisor de n sin usar la biblioteca (verificación aparte)."""
    if n % 2 == 0:
        return 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return d
        d += 2
    return None


def etiqueta(n: int, es_primo: bool) -> str:
    """Texto que se muestra en la tabla según el veredicto."""
    if es_primo:
        return "primo"
    return "no primo" if n < 2 else "compuesto"


def medir(fn, *args):
    """Ejecuta fn(*args) y devuelve (resultado, tiempo en microsegundos)."""
    t0 = time.perf_counter_ns()
    r = fn(*args)
    return r, (time.perf_counter_ns() - t0) / 1000      # de ns a microsegundos


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("numeros", nargs="*", type=int, default=INSTANCIA_CONOCIDA)
    ap.add_argument("--rondas", type=int, default=20)
    ap.add_argument("--semilla", type=int, default=None,
                    help="semilla para las bases de Miller-Rabin (ejecución reproducible)")
    a = ap.parse_args()
    rng = random.Random(a.semilla) if a.semilla is not None else None

    print(f"{'n':>22} | {'División de prueba':>22} | {'Miller-Rabin (r=' + str(a.rondas) + ')':>24} | Verificación")
    print("-" * 100)
    todo_ok = True
    for n in a.numeros:
        # Miller-Rabin se ejecuta siempre; la división solo si n es manejable
        mr, t_mr = medir(miller_rabin, n, a.rondas, rng)
        if n < LIMITE_DIVISION:
            td, t_td = medir(division_tentativa, n)
            txt_td = f"{etiqueta(n, td):>9} {t_td:>9.1f} µs"
            coinciden = td == mr
        else:
            td, txt_td, coinciden = None, f"{'(omitido, n grande)':>22}", True
        txt_mr = f"{etiqueta(n, mr):>9} {t_mr:>11.1f} µs"

        # Columna de verificación: se contrasta con un divisor explícito
        if not coinciden:
            verif = "DISCREPANCIA"
        elif n >= 2 and not mr and n < LIMITE_DIVISION:
            d = menor_divisor(n)
            verif = f"OK  ({n} = {d} x {n // d})"
        elif td is None:
            verif = "solo Miller-Rabin (n demasiado grande para dividir)"
        else:
            verif = "OK"
        todo_ok &= coinciden
        print(f"{n:>22} | {txt_td} | {txt_mr} | {verif}")

    print("-" * 100)
    print("Resultado:", "ambos métodos coinciden en todos los casos [OK]" if todo_ok
          else "hay discrepancias [FALLA]")
    return 0 if todo_ok else 1


if __name__ == "__main__":
    sys.exit(main())
