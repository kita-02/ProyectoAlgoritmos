"""Pipeline RSA (Entregas 1 y 2). USO EDUCATIVO: RSA sin relleno (OAEP).

Entrega 1: generar_claves(p, q, e), cifrar y descifrar de enteros.
Entrega 2:
* generar_claves_aleatorias(bits): claves al estilo FIPS 186-5 (Algoritmo 4).
* lambda_carmichael(p, q) = mcm(p - 1, q - 1).
* descifrar_crt: descifrado por el Teorema Chino del Resto (Garner).
* cifrar_texto / descifrar_texto: cifrado de texto en bloques.
* Exponenciación seleccionable: rápida (por defecto) o ventana deslizante.
"""
from __future__ import annotations

import random
import secrets
from dataclasses import dataclass

from .aritmetica import (exp_modular_rapida, exp_modular_ventana,
                         inverso_modular, mcd, mcm)
from .contador import Contador
from .primalidad import es_primo, generar_primo

E_PREFERIDO = 65537
BITS_MINIMOS = 16


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

    # Parámetros del TCR, derivados de (d, p, q)
    @property
    def dp(self) -> int:
        return self.d % (self.p - 1)

    @property
    def dq(self) -> int:
        return self.d % (self.q - 1)

    @property
    def qinv(self) -> int:
        return inverso_modular(self.q, self.p)


@dataclass(frozen=True)
class KeyPair:
    publica: ClavePublica
    privada: ClavePrivada


def lambda_carmichael(p: int, q: int) -> int:
    """Función lambda de Carmichael de n = p*q (p, q primos): mcm(p-1, q-1)."""
    if p < 2 or q < 2:
        raise ValueError("p y q deben ser primos")
    return mcm(p - 1, q - 1)


def elegir_e(phi: int, preferido: int = E_PREFERIDO) -> int:
    """65537 si es válido; si no, el menor impar >= 3 coprimo con phi."""
    if 1 < preferido < phi and mcd(preferido, phi) == 1:
        return preferido
    for e in range(3, phi, 2):
        if mcd(e, phi) == 1:
            return e
    raise ValueError("no existe exponente público válido")


def generar_claves(p: int, q: int, e: int | None = None) -> KeyPair:
    """Arma el par de claves (con phi) a partir de dos primos distintos p y q."""
    if p == q:
        raise ValueError("p y q deben ser distintos")
    if not es_primo(p):
        raise ValueError(f"p = {p} no es primo")
    if not es_primo(q):
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


def generar_claves_aleatorias(bits: int, e: int | None = None,
                              rng: random.Random | None = None,
                              criba: bool = True,
                              cont: Contador | None = None) -> KeyPair:
    """Par de claves de ``bits`` bits según FIPS 186-5 (Algoritmo 4 del informe).

    * p y q primos de bits/2 bits (dos bits altos en 1 -> n tiene exactamente
      ``bits`` bits), con mcd(e, p-1) = mcd(e, q-1) = 1.
    * |p - q| > 2^(bits/2 - 100) (si bits/2 <= 100 basta p != q).
    * d = e^(-1) mod lambda(n) y d > 2^(bits/2); si no se cumple se repite.
    * e por defecto: 65537; para claves de juguete (bits < 40) se usa 17,
      porque lambda(n) < n < 2^bits y e debe ser menor que lambda(n).
    """
    if not isinstance(bits, int) or bits < BITS_MINIMOS or bits % 2:
        raise ValueError(f"bits debe ser un entero par >= {BITS_MINIMOS}")
    if e is None:
        e = E_PREFERIDO if bits >= 40 else 17
    if e < 3 or e % 2 == 0:
        raise ValueError("e debe ser impar y >= 3")
    if e.bit_length() >= bits - 2:
        raise ValueError(f"e = {e} es demasiado grande para claves de {bits} bits")
    rng = rng or secrets.SystemRandom()
    mitad = bits // 2
    distancia_min = 1 << (mitad - 100) if mitad > 100 else 1

    def primo_valido() -> int:
        while True:
            p = generar_primo(mitad, rng, criba=criba, dos_bits_altos=True, cont=cont)
            if mcd(e, p - 1) == 1:
                return p

    for _ in range(10_000):
        p = primo_valido()
        q = primo_valido()
        if abs(p - q) < distancia_min or p == q:
            continue
        lam = lambda_carmichael(p, q)
        if e >= lam:
            continue
        d = inverso_modular(e, lam, cont)
        if d <= (1 << mitad):
            continue
        n = p * q
        return KeyPair(ClavePublica(n, e), ClavePrivada(n, d, p, q))
    raise RuntimeError(f"no se pudo generar una clave de {bits} bits con e = {e}")


def _potencia(base: int, exp: int, mod: int, ventana: bool,
              cont: Contador | None) -> int:
    if ventana:
        return exp_modular_ventana(base, exp, mod, cont=cont)
    return exp_modular_rapida(base, exp, mod, cont)


def cifrar(m: int, publica: ClavePublica, ventana: bool = False,
           cont: Contador | None = None) -> int:
    if not isinstance(m, int) or isinstance(m, bool) or not (0 <= m < publica.n):
        raise ValueError(f"el mensaje debe ser un entero con 0 <= m < n = {publica.n}")
    return _potencia(m, publica.e, publica.n, ventana, cont)


def descifrar(c: int, privada: ClavePrivada, ventana: bool = False,
              cont: Contador | None = None) -> int:
    if not isinstance(c, int) or isinstance(c, bool) or not (0 <= c < privada.n):
        raise ValueError(f"el criptograma debe cumplir 0 <= c < n = {privada.n}")
    return _potencia(c, privada.d, privada.n, ventana, cont)


def descifrar_crt(c: int, privada: ClavePrivada, ventana: bool = False,
                  cont: Contador | None = None) -> int:
    """Descifrado por el Teorema Chino del Resto (recombinación de Garner).

    m1 = c^dp mod p,  m2 = c^dq mod q,  h = qinv (m1 - m2) mod p,
    m = m2 + h q.  Dos exponenciaciones de la mitad de bits: ~4 veces menos
    trabajo que c^d mod n.
    """
    if not isinstance(c, int) or isinstance(c, bool) or not (0 <= c < privada.n):
        raise ValueError(f"el criptograma debe cumplir 0 <= c < n = {privada.n}")
    p, q = privada.p, privada.q
    m1 = _potencia(c % p, privada.dp, p, ventana, cont)
    m2 = _potencia(c % q, privada.dq, q, ventana, cont)
    h = privada.qinv * (m1 - m2) % p
    if cont is not None:
        cont.mult_mod += 2
    return m2 + h * q


# ---------------------------------------------------------------------------
# Texto en bloques
# ---------------------------------------------------------------------------
def tamano_bloque(n: int) -> int:
    """Bytes por bloque: floor(log2(n)) // 8, así cada bloque es < n."""
    tam = (n.bit_length() - 1) // 8
    if tam < 1:
        raise ValueError(f"n = {n} es muy pequeño para cifrar texto (se requiere n >= 256)")
    return tam


def cifrar_texto(texto: str, publica: ClavePublica, ventana: bool = False,
                 cont: Contador | None = None) -> list[int]:
    """Cifra un texto UTF-8 en bloques de tamano_bloque(n) bytes.

    Relleno ISO/IEC 7816-4: se agrega 0x80 y ceros hasta completar el
    último bloque, para poder recuperar la longitud exacta al descifrar.
    """
    if not isinstance(texto, str):
        raise TypeError("texto debe ser str")
    tam = tamano_bloque(publica.n)
    datos = texto.encode("utf-8") + b"\x80"
    datos += b"\x00" * (-len(datos) % tam)
    return [cifrar(int.from_bytes(datos[i:i + tam], "big"), publica, ventana, cont)
            for i in range(0, len(datos), tam)]


def descifrar_texto(bloques: list[int], privada: ClavePrivada,
                    crt: bool = False, ventana: bool = False,
                    cont: Contador | None = None) -> str:
    tam = tamano_bloque(privada.n)
    if not bloques:
        raise ValueError("no hay bloques que descifrar")
    funcion = descifrar_crt if crt else descifrar
    datos = b""
    for c in bloques:
        m = funcion(c, privada, ventana, cont)
        if m.bit_length() > 8 * tam:
            raise ValueError("bloque inválido: no corresponde a esta clave")
        datos += m.to_bytes(tam, "big")
    datos = datos.rstrip(b"\x00")
    if not datos.endswith(b"\x80"):
        raise ValueError("relleno inválido: la clave no corresponde o el criptograma fue alterado")
    try:
        return datos[:-1].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("el texto descifrado no es UTF-8 válido") from exc
