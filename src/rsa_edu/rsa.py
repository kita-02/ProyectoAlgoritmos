"""Pipeline RSA básico (Entrega 1). USO EDUCATIVO: RSA sin relleno (OAEP).

En esta entrega p y q se reciben directamente (no se generan al azar).

Pendiente para la Entrega 2: generar_primo / claves aleatorias por tamaño,
descifrado por el Teorema Chino del Resto y cifrado de texto por bloques.
"""
from __future__ import annotations

from dataclasses import dataclass

from .aritmetica import exp_modular_rapida, inverso_modular, mcd
from .primalidad import miller_rabin

E_PREFERIDO = 65537


@dataclass(frozen=True)
class ClavePublica:
    n: int
    e: int


@dataclass(frozen=True)
class ClavePrivada:
    n: int
    d: int
    p: int
    q: int


@dataclass(frozen=True)
class KeyPair:
    publica: ClavePublica
    privada: ClavePrivada


def elegir_e(phi: int, preferido: int = E_PREFERIDO) -> int:
    """65537 si es válido; si no, el menor impar >= 3 coprimo con phi."""
    if 1 < preferido < phi and mcd(preferido, phi) == 1:
        return preferido
    for e in range(3, phi, 2):
        if mcd(e, phi) == 1:
            return e
    raise ValueError("no existe exponente público válido")


def generar_claves(p: int, q: int, e: int | None = None) -> KeyPair:
    """Arma el par de claves a partir de dos primos distintos p y q."""
    if p == q:
        raise ValueError("p y q deben ser distintos")
    if not miller_rabin(p):
        raise ValueError(f"p = {p} no es primo")
    if not miller_rabin(q):
        raise ValueError(f"q = {q} no es primo")
    n, phi = p * q, (p - 1) * (q - 1)
    if e is None:
        e = elegir_e(phi)
    elif not (1 < e < phi):
        raise ValueError(f"e debe cumplir 1 < e < phi(n) = {phi}")
    elif mcd(e, phi) != 1:
        raise ValueError(f"mcd(e, phi(n)) = {mcd(e, phi)}: e no es invertible")
    d = inverso_modular(e, phi)
    return KeyPair(ClavePublica(n, e), ClavePrivada(n, d, p, q))


def cifrar(m: int, publica: ClavePublica) -> int:
    if not isinstance(m, int) or not (0 <= m < publica.n):
        raise ValueError(f"el mensaje debe ser un entero con 0 <= m < n = {publica.n}")
    return exp_modular_rapida(m, publica.e, publica.n)


def descifrar(c: int, privada: ClavePrivada) -> int:
    if not isinstance(c, int) or not (0 <= c < privada.n):
        raise ValueError(f"el criptograma debe cumplir 0 <= c < n = {privada.n}")
    return exp_modular_rapida(c, privada.d, privada.n)
