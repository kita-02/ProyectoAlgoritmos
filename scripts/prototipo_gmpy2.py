"""Prototipo de exponenciación modular: binaria, ventana deslizante, pow y gmpy2.

Uso (desde la raíz del repositorio):
    python scripts/prototipo_gmpy2.py                  # 512, 1024 y 2048 bits
    python scripts/prototipo_gmpy2.py --bits 1024 4096 --rep 7 --semilla 7

Para cada tamaño se genera (con semilla) un módulo impar, una base y un
exponente de ese número de bits, y se calcula base^exp mod n con:
    * exp_modular_rapida  (primera alternativa, aritmetica.py)
    * exp_modular_ventana (segunda alternativa, aritmetica.py)
    * pow(base, exp, n)   (referencia de Python, en C)
    * gmpy2.powmod        (biblioteca GMP, opcional)
Verifica que los cuatro resultados coinciden y muestra multiplicaciones
modulares contadas y la mediana del tiempo.  gmpy2 muestra cuánto se ganaría
cambiando la aritmética de enteros por una biblioteca optimizada en C; si no
está instalado, la columna se omite.
"""
from __future__ import annotations

import argparse
import random
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from rsa_edu.aritmetica import (exp_modular_rapida, exp_modular_ventana,  # noqa: E402
                                ventana_optima)
from rsa_edu.contador import Contador  # noqa: E402

try:
    import gmpy2
except ImportError:                       # dependencia opcional
    gmpy2 = None


def mediana_ms(f, rep: int) -> tuple[int, float]:
    tiempos, r = [], None
    for _ in range(rep):
        t0 = time.perf_counter()
        r = f()
        tiempos.append(time.perf_counter() - t0)
    return r, statistics.median(tiempos) * 1000


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bits", type=int, nargs="+", default=[512, 1024, 2048])
    ap.add_argument("--rep", type=int, default=5)
    ap.add_argument("--semilla", type=int, default=2026)
    a = ap.parse_args(argv)
    if a.rep < 1 or any(b < 8 for b in a.bits):
        ap.error("--rep debe ser >= 1 y cada tamaño >= 8 bits")
    rng = random.Random(a.semilla)

    print(f"gmpy2: {'versión ' + gmpy2.version() if gmpy2 else 'no instalado (se omite)'}")
    print(f"{'bits':>6} {'k':>3} {'mult. binaria':>14} {'mult. ventana':>14} "
          f"{'binaria ms':>11} {'ventana ms':>11} {'pow ms':>9} {'gmpy2 ms':>9}  verificación")
    print("-" * 104)
    todo_ok = True
    for bits in a.bits:
        n = rng.getrandbits(bits) | (1 << (bits - 1)) | 1
        b = rng.randrange(2, n)
        e = rng.getrandbits(bits) | (1 << (bits - 1))

        cb, cv = Contador(), Contador()
        exp_modular_rapida(b, e, n, cb)
        exp_modular_ventana(b, e, n, cont=cv)

        r_bin, t_bin = mediana_ms(lambda: exp_modular_rapida(b, e, n), a.rep)
        r_ven, t_ven = mediana_ms(lambda: exp_modular_ventana(b, e, n), a.rep)
        r_pow, t_pow = mediana_ms(lambda: pow(b, e, n), a.rep)
        resultados = [r_bin, r_ven, r_pow]
        txt_gmp = f"{'-':>9}"
        if gmpy2 is not None:
            r_gmp, t_gmp = mediana_ms(lambda: int(gmpy2.powmod(b, e, n)), a.rep)
            resultados.append(r_gmp)
            txt_gmp = f"{t_gmp:>9.3f}"
        ok = len(set(resultados)) == 1
        todo_ok &= ok
        print(f"{bits:>6} {ventana_optima(e.bit_length()):>3} {cb.mult_mod:>14,} {cv.mult_mod:>14,} "
              f"{t_bin:>11.3f} {t_ven:>11.3f} {t_pow:>9.3f} {txt_gmp}  "
              f"{'[OK] los resultados coinciden' if ok else '[FALLA]'}")

    print("-" * 104)
    print("Resultado:", "todas las implementaciones coinciden [OK]" if todo_ok else "[FALLA]")
    return 0 if todo_ok else 1


if __name__ == "__main__":
    sys.exit(main())
