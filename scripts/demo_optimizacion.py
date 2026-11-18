"""Demostración: ¿se optimiza realmente el pipeline RSA?

Ejecuta el pipeline completo (generar claves -> cifrar -> descifrar) dos veces
con la MISMA semilla:

  * BASE        : generar_primo sin criba, descifrado directo c^d mod n
                  (exponenciación binaria).
  * OPTIMIZADO  : generar_primo con criba de primos < 2000, descifrado por el
                  Teorema Chino del Resto con exponenciación por ventana.

Luego verifica que ambos producen exactamente lo mismo (misma clave, mismos
cifrados, todos los mensajes recuperados, cifrados iguales a pow(m, e, n)) y
compara, etapa por etapa, el tiempo (mediana de varias repeticiones) y las
multiplicaciones modulares contadas, que no dependen de la computadora.

Uso (desde la raíz del repositorio):
    python scripts/demo_optimizacion.py                 # clave de 1024 bits
    python scripts/demo_optimizacion.py --bits 2048
    python scripts/demo_optimizacion.py --bits 512 --mensajes 20 --rep 5
"""
from __future__ import annotations

import argparse
import random
import statistics
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from rsa_edu.contador import Contador  # noqa: E402
from rsa_edu.rsa import (cifrar, descifrar, descifrar_crt,  # noqa: E402
                         generar_claves_aleatorias)

# Las dos configuraciones que se comparan.
#   criba   -> generar_primo(..., criba=True)        (primalidad.py)
#   crt     -> descifrar_crt en vez de descifrar     (rsa.py)
#   ventana -> exp_modular_ventana en el descifrado  (aritmetica.py)
CONFIGURACIONES = {
    "base":       dict(criba=False, crt=False, ventana=False),
    "optimizado": dict(criba=True,  crt=True,  ventana=True),
}


def ejecutar(bits: int, cantidad: int, semilla: int, criba: bool, crt: bool, ventana: bool):
    """Una ejecución del pipeline; devuelve resultados, tiempos y conteos por etapa."""
    tiempos, conteos = {}, {}

    c = Contador()
    t0 = time.perf_counter()
    claves = generar_claves_aleatorias(bits, rng=random.Random(semilla), criba=criba, cont=c)
    tiempos["Generar claves"], conteos["Generar claves"] = time.perf_counter() - t0, c

    pub, priv = claves.publica, claves.privada
    rng_msg = random.Random(semilla + 1)
    mensajes = [rng_msg.randrange(0, pub.n) for _ in range(cantidad)]

    # Con e = 65537 (17 bits) la ventana no ahorra nada al cifrar: ambas
    # configuraciones cifran con la exponenciación binaria.
    c = Contador()
    t0 = time.perf_counter()
    cifrados = [cifrar(m, pub, cont=c) for m in mensajes]
    tiempos["Cifrar"], conteos["Cifrar"] = time.perf_counter() - t0, c

    funcion = descifrar_crt if crt else descifrar
    c = Contador()
    t0 = time.perf_counter()
    descifrados = [funcion(x, priv, ventana=ventana, cont=c) for x in cifrados]
    tiempos["Descifrar"], conteos["Descifrar"] = time.perf_counter() - t0, c

    return claves, mensajes, cifrados, descifrados, tiempos, conteos


def medir(bits: int, cantidad: int, semilla: int, rep: int, **config):
    """Repite la ejecución; tiempos = mediana, conteos de la primera (son deterministas)."""
    corridas = [ejecutar(bits, cantidad, semilla, **config) for _ in range(rep)]
    claves, mensajes, cifrados, descifrados, _, conteos = corridas[0]
    etapas = corridas[0][4].keys()
    tiempos = {e: statistics.median(r[4][e] for r in corridas) * 1000 for e in etapas}
    return claves, mensajes, cifrados, descifrados, tiempos, conteos


def ok(condicion: bool) -> str:
    return "[OK]" if condicion else "[FALLA]"


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bits", type=int, default=1024, help="tamaño de n (par, >= 16)")
    ap.add_argument("--mensajes", type=int, default=10)
    ap.add_argument("--rep", type=int, default=3, help="repeticiones para la mediana")
    ap.add_argument("--semilla", type=int, default=2026)
    a = ap.parse_args(argv)
    if a.mensajes < 1 or a.rep < 1:
        ap.error("--mensajes y --rep deben ser >= 1")

    print("=" * 78)
    print(f" Pipeline RSA de {a.bits} bits: BASE frente a OPTIMIZADO")
    print(f" {a.mensajes} mensajes, semilla {a.semilla}, mediana de {a.rep} repeticiones")
    print("=" * 78)

    res = {}
    for nombre, config in CONFIGURACIONES.items():
        print(f"ejecutando {nombre:<11} {config} ...", flush=True)
        res[nombre] = medir(a.bits, a.mensajes, a.semilla, a.rep, **config)

    (kb, mb, cb, db, tb, nb) = res["base"]
    (ko, mo, co, do, to, no) = res["optimizado"]
    n, e = kb.publica.n, kb.publica.e

    print("\n[1] ¿Ambas versiones hacen exactamente lo mismo?")
    checks = [
        ("misma clave (n, e, d)", kb == ko),
        ("mismos mensajes y mismos cifrados", mb == mo and cb == co),
        ("cifrados iguales a pow(m, e, n) de Python", cb == [pow(m, e, n) for m in mb]),
        (f"base recupera los {len(mb)} mensajes", db == mb),
        (f"optimizado recupera los {len(mo)} mensajes", do == mo),
    ]
    for texto, cond in checks:
        print(f"    {texto:<48} {ok(cond)}")
    print(f"    n = {str(n)[:20]}...  ({n.bit_length()} bits)   e = {e}")

    print("\n[2] ¿Cuánto mejora cada etapa?")
    print(f"    {'etapa':<15}{'base (ms)':>11}{'optim. (ms)':>13}{'mejora':>9}"
          f"{'mult. base':>13}{'mult. optim.':>14}")
    print("    " + "-" * 74)
    for etapa in tb:
        mejora = tb[etapa] / to[etapa] if to[etapa] > 0 else float("inf")
        print(f"    {etapa:<15}{tb[etapa]:>11.2f}{to[etapa]:>13.2f}{mejora:>8.2f}x"
              f"{nb[etapa].mult_mod:>13,}{no[etapa].mult_mod:>14,}")
    total_b, total_o = sum(tb.values()), sum(to.values())
    mult_b = sum(c.mult_mod for c in nb.values())
    mult_o = sum(c.mult_mod for c in no.values())
    print("    " + "-" * 74)
    print(f"    {'TOTAL':<15}{total_b:>11.2f}{total_o:>13.2f}{total_b / total_o:>8.2f}x"
          f"{mult_b:>13,}{mult_o:>14,}")

    mitad = (kb.privada.p.bit_length() + kb.privada.q.bit_length()) // 2
    extra = no["Generar claves"].div_mod - nb["Generar claves"].div_mod
    print(f"    Nota: al generar claves, la criba agrega {extra:,} divisiones entre primos < 2000;"
          f"\n    son mucho más baratas que las multiplicaciones de {mitad} bits que evita.")
    print(f"    Nota: al descifrar, la base multiplica números de {n.bit_length()} bits y el TCR"
          f" de {mitad} bits;\n    cada multiplicación del TCR cuesta ~4 veces menos, por eso"
          " el tiempo baja más que el conteo.")

    print("\n[3] Dónde está cada optimización en el código")
    print("    Generar claves : primalidad.generar_primo(..., criba=True) -> pasa_criba descarta")
    print("                     candidatos con factores < 2000 antes de Miller-Rabin")
    print("    Descifrar      : rsa.descifrar_crt -> dos exponenciaciones mod p y mod q")
    print("                     (mitad de bits) + aritmetica.exp_modular_ventana")
    print("    Cifrar         : igual en ambas (e = 65537 tiene 17 bits: no hay qué ahorrar)")

    correcto = all(cond for _, cond in checks)
    print("\n" + "=" * 78)
    print(f" RESULTADO: mismo resultado {ok(correcto)}   "
          f"pipeline {total_b / total_o:.2f} veces más rápido")
    print("=" * 78)
    return 0 if correcto else 1


if __name__ == "__main__":
    sys.exit(main())
