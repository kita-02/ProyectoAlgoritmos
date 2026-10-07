"""Traza completa del pipeline RSA sobre una instancia pequeña.

Uso (desde la raíz del repositorio):
    python scripts/traza_instancia.py                          # p=61, q=53, e=17, m=65 (Avance 1)
    python scripts/traza_instancia.py --p 89 --q 97 --m 1234   # instancia propuesta en la sesión
    python scripts/traza_instancia.py --p 61 --q 51            # caso inválido: q no es primo

Cada paso se verifica contra funciones de Python que NO son de la biblioteca
(pow(m, e, n) y pow(e, -1, phi)), de modo que la salida es verificable.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from rsa_edu.primalidad import division_tentativa, miller_rabin  # noqa: E402
from rsa_edu.rsa import cifrar, descifrar, generar_claves  # noqa: E402


def ok(cond: bool) -> str:
    return "[OK]" if cond else "[FALLA]"


def traza_euclides(a: int, b: int) -> None:
    print(f"    {'q':>8} {'a':>8} {'b':>8} {'x0':>8} {'x1':>8}")
    print(f"    {'-':>8} {a:>8} {b:>8} {1:>8} {0:>8}")
    x0, x1 = 1, 0
    while b:
        q = a // b
        a, b = b, a - q * b
        x0, x1 = x1, x0 - q * x1
        print(f"    {q:>8} {a:>8} {b:>8} {x0:>8} {x1:>8}")


def traza_exp(base: int, e: int, n: int) -> None:
    print(f"    e = {e} = {e:b} (binario), se recorre de derecha a izquierda")
    print(f"    {'it':>3} {'bit':>3} {'r antes':>10} {'base':>10} {'r después':>10}")
    r, b, it = 1, base % n, 0
    while e:
        it += 1
        antes = r
        if e & 1:
            r = r * b % n
        print(f"    {it:>3} {e & 1:>3} {antes:>10} {b:>10} {r:>10}")
        e >>= 1
        if e:
            b = b * b % n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--p", type=int, default=61)
    ap.add_argument("--q", type=int, default=53)
    ap.add_argument("--e", type=int, default=None,
                    help="si se omite: 65537 si es válido, si no el menor impar coprimo")
    ap.add_argument("--m", type=int, default=65)
    a = ap.parse_args()
    if a.e is None and (a.p, a.q, a.m) == (61, 53, 65):
        a.e = 17                                   # instancia exacta del Avance 1

    print("=" * 64)
    print(f" Instancia: p = {a.p}, q = {a.q}, e = {a.e or 'automático'}, m = {a.m}")
    print("=" * 64)

    print("\n[1] Primalidad de p y q")
    for nombre, v in (("p", a.p), ("q", a.q)):
        td = division_tentativa(v) if v < 2**44 else "(omitida, número grande)"
        mr = miller_rabin(v)
        print(f"    {nombre} = {v}: división de prueba -> {td}, Miller-Rabin -> {mr}")

    print("\n[2] Generación de claves")
    try:
        par = generar_claves(a.p, a.q, a.e)
    except ValueError as err:
        print(f"    ERROR: {err}")
        print("\nResultado: instancia rechazada correctamente (entrada inválida).")
        return 1
    pub, priv = par.publica, par.privada
    phi = (priv.p - 1) * (priv.q - 1)
    print(f"    n = p*q = {pub.n}    phi(n) = (p-1)(q-1) = {phi}    e = {pub.e}")
    if phi < 10**7:
        print(f"\n    Euclides extendido ({pub.e}, {phi}):")
        traza_euclides(pub.e, phi)
    print(f"\n    d = e^-1 mod phi(n) = {priv.d}")
    d_ref = pow(pub.e, -1, phi)
    print(f"    verificación: pow(e, -1, phi) = {d_ref}  {ok(d_ref == priv.d)}"
          f"   e*d mod phi = {pub.e * priv.d % phi}  {ok(pub.e * priv.d % phi == 1)}")

    print(f"\n[3] Cifrado: c = m^e mod n = {a.m}^{pub.e} mod {pub.n}")
    try:
        c = cifrar(a.m, pub)
    except ValueError as err:
        print(f"    ERROR: {err}")
        print("\nResultado: mensaje rechazado correctamente (entrada inválida).")
        return 1
    traza_exp(a.m, pub.e, pub.n)
    c_ref = pow(a.m, pub.e, pub.n)
    print(f"    c = {c}     verificación: pow(m, e, n) = {c_ref}  {ok(c == c_ref)}")

    print(f"\n[4] Descifrado: m' = c^d mod n = {c}^{priv.d} mod {pub.n}")
    m2 = descifrar(c, priv)
    print(f"    m' = {m2}")

    todo = (c == c_ref) and (d_ref == priv.d) and (m2 == a.m)
    print("\n" + "=" * 64)
    print(f" RESULTADO: m' = {m2}  {'=' if m2 == a.m else '!='}  m = {a.m}   {ok(todo)}")
    print("=" * 64)
    return 0 if todo else 1


if __name__ == "__main__":
    sys.exit(main())
