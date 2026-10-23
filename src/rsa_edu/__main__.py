"""Interfaz de línea de comandos: python -m rsa_edu <subcomando> ...

Subcomandos (todos devuelven código 0 si terminan bien y 1 si hay error):

  primo       N [--metodo ...]           ¿es primo N?
  primo       --generar BITS [--semilla]   genera un primo de BITS bits
  factorizar  N [--metodo ...]           factorización completa
  claves      -p P -q Q [-e E] --salida F  claves a partir de p y q
  claves      --bits B [--semilla S] --salida F   claves aleatorias (FIPS 186-5)
  cifrar      M --claves F [--ventana]    cifra un entero (o --texto "...")
  descifrar   C --claves F [--crt]        descifra un entero (o --texto c1,c2,...)
  atacar      -n N -e E                   factoriza n y reconstruye d
  comparar    TAREA ENTRADA                ejecuta las dos alternativas y compara
  pipeline    --bits B [--crt --ventana --sin-criba --gmpy2]

Las opciones largas aceptan también un solo guion (-salida, -claves, -crt).
"""
from __future__ import annotations

import argparse
import random
import sys
import time

from . import __version__
from .aritmetica import exp_modular_ingenua, exp_modular_rapida, exp_modular_ventana
from .ataque import romper_clave
from .contador import Contador
from .factorizacion import METODOS, factorizar
from .formatos import FormatoInvalido, cargar_claves, guardar_claves
from .pipeline import ConfigPipeline, ejecutar_pipeline
from .primalidad import (LIMITE_DETERMINISTA, division_tentativa, es_primo,
                         generar_primo, miller_rabin, miller_rabin_determinista)
from .rsa import (cifrar, cifrar_texto, descifrar, descifrar_crt, descifrar_texto,
                  generar_claves, generar_claves_aleatorias)

METODOS_PRIMO = {
    "auto": lambda n, rng: es_primo(n, rng=rng),
    "tentativa": lambda n, rng: division_tentativa(n),
    "mr": lambda n, rng: miller_rabin(n, rng=rng),
    "determinista": lambda n, rng: miller_rabin_determinista(n),
}


def entero(texto: str) -> int:
    """Convierte la entrada a entero aceptando 0x..., 1_000 y 10**6."""
    t = texto.strip().replace("_", "")
    try:
        if "**" in t:
            base, exp = t.split("**", 1)
            return int(base) ** int(exp)
        return int(t, 0)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{texto}' no es un entero válido") from None


def _opt(parser: argparse.ArgumentParser, nombre: str, **kw) -> None:
    """Agrega --nombre y su alias de un guion -nombre."""
    parser.add_argument(f"--{nombre}", f"-{nombre}", **kw)


def _rng(semilla: int | None) -> random.Random:
    return random.Random(semilla) if semilla is not None else random.SystemRandom()


# ---------------------------------------------------------------------------
def cmd_primo(a: argparse.Namespace) -> int:
    rng = _rng(a.semilla)
    if a.generar is not None:
        p = generar_primo(a.generar, rng, criba=not a.sin_criba)
        print(p)
        return 0
    if a.n is None:
        raise ValueError("indique N o --generar BITS")
    if a.metodo == "determinista" and a.n >= LIMITE_DETERMINISTA:
        raise ValueError("el método determinista solo es exacto para n < 3,18e23")
    res = METODOS_PRIMO[a.metodo](a.n, rng)
    print(f"{a.n} es {'PRIMO' if res else 'COMPUESTO'} (método: {a.metodo})")
    return 0


def cmd_factorizar(a: argparse.Namespace) -> int:
    f = factorizar(a.n, a.metodo, rng=_rng(a.semilla), max_iter=a.max_iter)
    print(f"{a.n} = {' × '.join(map(str, f)) if f else '1'}")
    return 0


def cmd_claves(a: argparse.Namespace) -> int:
    if a.bits is not None:
        kp = generar_claves_aleatorias(a.bits, a.e, rng=_rng(a.semilla),
                                       criba=not a.sin_criba)
    else:
        if a.p is None or a.q is None:
            raise ValueError("indique -p y -q, o bien --bits")
        kp = generar_claves(a.p, a.q, a.e)
    pub, priv = kp.publica, kp.privada
    print(f"n = {pub.n}  ({pub.n.bit_length()} bits)")
    print(f"e = {pub.e}")
    print(f"d = {priv.d}")
    if a.salida:
        guardar_claves(a.salida, kp)
        print(f"claves guardadas en {a.salida}")
        if a.publica:
            guardar_claves(a.publica, kp, solo_publica=True)
            print(f"clave pública guardada en {a.publica}")
    return 0


def cmd_cifrar(a: argparse.Namespace) -> int:
    pub, _ = cargar_claves(a.claves)
    if a.texto is not None:
        print(",".join(map(str, cifrar_texto(a.texto, pub, a.ventana))))
    else:
        if a.m is None:
            raise ValueError("indique el mensaje M o --texto")
        print(cifrar(a.m, pub, a.ventana))
    return 0


def cmd_descifrar(a: argparse.Namespace) -> int:
    _, priv = cargar_claves(a.claves)
    if priv is None:
        raise ValueError("el archivo de claves no contiene la clave privada")
    if a.texto is not None:
        bloques = [entero(x) for x in a.texto.split(",") if x.strip()]
        print(descifrar_texto(bloques, priv, crt=a.crt, ventana=a.ventana))
    else:
        if a.c is None:
            raise ValueError("indique el criptograma C o --texto")
        f = descifrar_crt if a.crt else descifrar
        print(f(a.c, priv, a.ventana))
    return 0


def cmd_atacar(a: argparse.Namespace) -> int:
    t0 = time.perf_counter()
    r = romper_clave(a.n, a.e, a.metodo, rng=_rng(a.semilla), max_iter=a.max_iter)
    dt = time.perf_counter() - t0
    print(f"n = {r.p} × {r.q}   phi(n) = {r.phi}   d = {r.d}")
    print(f"(factorizado con {a.metodo} en {dt * 1000:.2f} ms)")
    return 0


def _medir(f):
    c = Contador()
    t0 = time.perf_counter()
    r = f(c)
    return r, (time.perf_counter() - t0) * 1000, c


def cmd_comparar(a: argparse.Namespace) -> int:
    """Ejecuta las alternativas sobre la misma instancia y verifica equivalencia."""
    rng_sem = a.semilla if a.semilla is not None else 2026
    x = a.entrada
    if a.tarea == "primalidad":
        alts = {"division_tentativa": lambda c: division_tentativa(x, c),
                "miller_rabin": lambda c: miller_rabin(x, rng=random.Random(rng_sem), cont=c)}
        if x < LIMITE_DETERMINISTA:
            alts["miller_rabin_determinista"] = lambda c: miller_rabin_determinista(x, c)
    elif a.tarea == "factorizacion":
        alts = {m: (lambda c, m=m: factorizar(x, m, rng=random.Random(rng_sem), cont=c))
                for m in METODOS}
    elif a.tarea == "exponenciacion":
        mod = a.mod or 18446744073709551557
        alts = {"rapida": lambda c: exp_modular_rapida(a.base, x, mod, c),
                "ventana": lambda c: exp_modular_ventana(a.base, x, mod, cont=c)}
        if x <= 10 ** 6:
            alts["ingenua"] = lambda c: exp_modular_ingenua(a.base, x, mod, c)
    else:   # descifrado
        if not a.claves:
            raise ValueError("comparar descifrado requiere --claves")
        _, priv = cargar_claves(a.claves)
        if priv is None:
            raise ValueError("el archivo de claves no contiene la clave privada")
        alts = {"descifrar": lambda c: descifrar(x, priv, cont=c),
                "descifrar_crt": lambda c: descifrar_crt(x, priv, cont=c)}

    print(f"{'alternativa':<26} {'resultado':<28} {'ms':>9} {'mult':>8} {'div':>8} {'iter':>8}")
    resultados = {}
    for nombre, f in alts.items():
        r, ms, c = _medir(f)
        resultados[nombre] = r
        txt = str(r)
        txt = txt if len(txt) <= 28 else txt[:25] + "..."
        print(f"{nombre:<26} {txt:<28} {ms:>9.3f} {c.mult_mod:>8} {c.div_mod:>8} {c.iteraciones:>8}")
    iguales = len({repr(v) for v in resultados.values()}) == 1
    print("EQUIVALENTES: sí" if iguales else "EQUIVALENTES: NO (revisar)")
    return 0 if iguales else 1


def cmd_pipeline(a: argparse.Namespace) -> int:
    cfg = ConfigPipeline(a.bits, semilla=a.semilla if a.semilla is not None else 2026,
                         criba=not a.sin_criba, crt=a.crt, ventana=a.ventana, gmpy2=a.gmpy2)
    r = ejecutar_pipeline(cfg, cantidad=a.mensajes)
    for aviso in r.avisos:
        print(f"aviso: {aviso}")
    print(f"configuración: {cfg.nombre()}")
    print(f"n = {r.claves.publica.n.bit_length()} bits")
    for etapa, t in r.tiempos.items():
        print(f"  {etapa:<11} {t * 1000:10.3f} ms")
    print(f"  operaciones: {r.contador.como_dict()}")
    print(f"descifrado == mensaje en {sum(x == y for x, y in zip(r.mensajes, r.descifrados))}"
          f"/{len(r.mensajes)} mensajes -> {'OK' if r.correcto else 'FALLA'}")
    return 0 if r.correcto else 1


# ---------------------------------------------------------------------------
def construir_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -m rsa_edu",
                                 description=f"rsa_edu {__version__} - biblioteca educativa RSA (Grupo 6)")
    ap.add_argument("--version", action="version", version=f"rsa_edu {__version__}")
    sub = ap.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("primo", help="test de primalidad o generación de primos")
    p.add_argument("n", type=entero, nargs="?")
    _opt(p, "metodo", choices=list(METODOS_PRIMO), default="auto")
    _opt(p, "generar", type=int, metavar="BITS")
    _opt(p, "semilla", type=int)
    _opt(p, "sin-criba", action="store_true", dest="sin_criba")
    p.set_defaults(func=cmd_primo)

    p = sub.add_parser("factorizar", help="factorización completa")
    p.add_argument("n", type=entero)
    _opt(p, "metodo", choices=list(METODOS), default="brent")
    _opt(p, "semilla", type=int)
    _opt(p, "max-iter", type=int, dest="max_iter")
    p.set_defaults(func=cmd_factorizar)

    p = sub.add_parser("claves", help="generar par de claves")
    p.add_argument("-p", type=entero)
    p.add_argument("-q", type=entero)
    p.add_argument("-e", type=entero)
    _opt(p, "bits", type=int)
    _opt(p, "semilla", type=int)
    _opt(p, "sin-criba", action="store_true", dest="sin_criba")
    _opt(p, "salida")
    _opt(p, "publica", help="archivo adicional solo con la clave pública")
    p.set_defaults(func=cmd_claves)

    p = sub.add_parser("cifrar", help="cifrar un entero o un texto")
    p.add_argument("m", type=entero, nargs="?")
    _opt(p, "claves", required=True)
    _opt(p, "texto")
    _opt(p, "ventana", action="store_true")
    p.set_defaults(func=cmd_cifrar)

    p = sub.add_parser("descifrar", help="descifrar un entero o bloques de texto")
    p.add_argument("c", type=entero, nargs="?")
    _opt(p, "claves", required=True)
    _opt(p, "texto", help="bloques separados por comas")
    _opt(p, "crt", action="store_true")
    _opt(p, "ventana", action="store_true")
    p.set_defaults(func=cmd_descifrar)

    p = sub.add_parser("atacar", help="factorizar n y recuperar d")
    p.add_argument("-n", type=entero, required=True)
    p.add_argument("-e", type=entero, required=True)
    _opt(p, "metodo", choices=list(METODOS), default="brent")
    _opt(p, "semilla", type=int)
    _opt(p, "max-iter", type=int, dest="max_iter")
    p.set_defaults(func=cmd_atacar)

    p = sub.add_parser("comparar", help="ejecutar las alternativas sobre la misma instancia")
    p.add_argument("tarea", choices=["primalidad", "factorizacion", "exponenciacion", "descifrado"])
    p.add_argument("entrada", type=entero, help="n, exponente o criptograma según la tarea")
    _opt(p, "base", type=entero, default=3)
    _opt(p, "mod", type=entero)
    _opt(p, "claves")
    _opt(p, "semilla", type=int)
    p.set_defaults(func=cmd_comparar)

    p = sub.add_parser("pipeline", help="claves -> cifrado -> descifrado con métricas")
    _opt(p, "bits", type=int, default=512)
    _opt(p, "mensajes", type=int, default=10)
    _opt(p, "semilla", type=int)
    _opt(p, "crt", action="store_true")
    _opt(p, "ventana", action="store_true")
    _opt(p, "gmpy2", action="store_true")
    _opt(p, "sin-criba", action="store_true", dest="sin_criba")
    p.set_defaults(func=cmd_pipeline)
    return ap


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = construir_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:              # argparse: --help -> 0, error -> 2
        return 0 if exc.code == 0 else 1
    try:
        return args.func(args)
    except (ValueError, TypeError, RuntimeError, FormatoInvalido) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
