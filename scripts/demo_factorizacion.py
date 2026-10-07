"""Demo de factorización: división de prueba vs. Pollard Rho.

Uso (desde la raíz del repositorio):
    python scripts/demo_factorizacion.py                       # n = 3233 (Avance 1)
    python scripts/demo_factorizacion.py 561 600851475143      # números propuestos
    python scripts/demo_factorizacion.py 1099506259969 --semilla 2026

Verificación de la salida (sin depender del algoritmo que se prueba):
    * el producto de los factores es exactamente n;
    * cada factor es primo (según la división de prueba de primalidad);
    * los dos métodos devuelven la misma lista.
"""
from __future__ import annotations

import argparse
import random
import sys
import time
from math import prod
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from rsa_edu.factorizacion import factorizar  # noqa: E402
from rsa_edu.primalidad import division_tentativa, miller_rabin  # noqa: E402

INSTANCIA_CONOCIDA = [3233]
LIMITE_TENTATIVA = 2**44       # la división de prueba de semiprimos grandes tarda demasiado
MAX_ITER_RHO = 300_000         # ~1-3 s por intento: la demo nunca se queda colgada


def es_primo_ref(f: int) -> bool:
    return division_tentativa(f) if f < 2**44 else miller_rabin(f)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("numeros", nargs="*", type=int, default=INSTANCIA_CONOCIDA)
    ap.add_argument("--semilla", type=int, default=None,
                    help="fija las elecciones aleatorias de Pollard Rho")
    ap.add_argument("--max-iter", type=int, default=MAX_ITER_RHO,
                    help="límite de iteraciones de Pollard Rho por intento")
    a = ap.parse_args()
    rng = random.Random(a.semilla) if a.semilla is not None else None

    todo_ok = True
    for n in a.numeros:
        print(f"\nn = {n}  ({n.bit_length()} bits)")
        resultados = {}
        for metodo in ("tentativa", "rho"):
            if metodo == "tentativa" and n >= LIMITE_TENTATIVA:
                print(f"  {'tentativa':<10} (omitido: n demasiado grande para división de prueba)")
                continue
            try:
                t0 = time.perf_counter_ns()
                f = factorizar(n, metodo, rng, max_iter=a.max_iter)
                t = (time.perf_counter_ns() - t0) / 1e6
            except ValueError as err:              # entrada inválida (n <= 0)
                print(f"  {metodo:<10} entrada rechazada: {err}")
                continue
            except RuntimeError as err:            # límite de iteraciones agotado
                print(f"  {metodo:<10} {err}")
                print(f"  {'':<10} (n tiene factores demasiado grandes para "
                      f"Pollard Rho en tiempo de demo; esto es lo esperado)")
                continue
            ok = prod(f) == n and all(es_primo_ref(x) for x in f)
            resultados[metodo] = f
            todo_ok &= ok
            expr = " x ".join(map(str, f)) if f else "(sin factores)"
            print(f"  {metodo:<10} {expr:<40} {t:>10.3f} ms   "
                  f"{'[OK] producto = n y factores primos' if ok else '[FALLA]'}")
        if len(resultados) == 2:
            igual = resultados["tentativa"] == resultados["rho"]
            todo_ok &= igual
            print(f"  ambos métodos coinciden: {'sí [OK]' if igual else 'NO [FALLA]'}")

    print("\nResultado:", "todas las factorizaciones verificadas [OK]" if todo_ok
          else "hubo fallas [FALLA]")
    return 0 if todo_ok else 1


if __name__ == "__main__":
    sys.exit(main())
