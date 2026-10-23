"""Tests de primalidad y generación de primos (Entregas 1 y 2).

Entrega 1:
* division_tentativa: determinista y exacto, O(sqrt(n)) divisiones probando
  solo los candidatos 6k - 1 y 6k + 1.
* miller_rabin: probabilístico; la probabilidad de declarar primo a un
  compuesto es a lo más 4^(-rondas).

Entrega 2:
* miller_rabin_determinista: Miller-Rabin con las 12 primeras bases primas
  (2, 3, ..., 37). Es EXACTO para n < 3,18 x 10^23 (sección 1.2.2).
* es_primo: fachada que usa la versión determinista bajo ese límite y la
  aleatoria (20 rondas) por encima.
* criba_eratostenes / pasa_criba: filtro rápido de candidatos con los 303
  primos menores que 2000.
* generar_primo: genera un primo de exactamente b bits (Algoritmo 2).
"""
from __future__ import annotations

import random
import secrets

from .aritmetica import exp_modular_rapida
from .contador import Contador

# Las 12 primeras bases primas y el límite hasta el cual son suficientes
# (menor pseudoprimo fuerte para todas ellas: psi_12, Sorenson y Webster 2015).
BASES_DETERMINISTAS: tuple[int, ...] = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
LIMITE_DETERMINISTA: int = 318_665_857_834_031_151_167_461   # ~ 3,18 x 10^23

LIMITE_CRIBA = 2000
RONDAS_POR_DEFECTO = 20


# ---------------------------------------------------------------------------
# Entrega 1
# ---------------------------------------------------------------------------
def division_tentativa(n: int, cont: Contador | None = None) -> bool:
    """Decide de forma exacta si n es primo.

    Se descartan primero los múltiplos de 2 y de 3; luego basta probar los
    divisores 6k - 1 y 6k + 1 mientras no superen sqrt(n).
    """
    if n < 2:
        return False
    if n < 4:
        return True
    if cont is not None:
        cont.div_mod += 2
    if n % 2 == 0 or n % 3 == 0:
        return False

    candidato = 5
    while candidato * candidato <= n:
        if cont is not None:
            cont.div_mod += 2
            cont.iteraciones += 1
        if n % candidato == 0 or n % (candidato + 2) == 0:
            return False
        candidato += 6
    return True


def descomponer(n: int) -> tuple[int, int]:
    """Factoriza n - 1 como 2^s * d, con d impar, y devuelve el par (s, d)."""
    if n < 3:
        raise ValueError("descomponer requiere n >= 3")
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    return s, d


def es_testigo(a: int, s: int, d: int, n: int,
               cont: Contador | None = None) -> bool:
    """Indica si la base a es testigo de que n es compuesto.

    Devuelve True cuando a PRUEBA que n no es primo, y False cuando n pasa
    la prueba para esa base (n es primo o a es un "mentiroso fuerte").
    """
    x = exp_modular_rapida(a, d, n, cont)
    if x == 1 or x == n - 1:                 # a^d = +-1 (mod n)
        return False
    for _ in range(s - 1):                   # a^(2^r d) = -1 para 0 < r < s
        x = x * x % n
        if cont is not None:
            cont.mult_mod += 1
        if x == n - 1:
            return False
    return True


def _casos_triviales(n: int) -> bool | None:
    """Resuelve n < 4 y los pares; devuelve None si hace falta el test."""
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False
    return None


def miller_rabin(n: int, rondas: int = RONDAS_POR_DEFECTO,
                 rng: random.Random | None = None,
                 cont: Contador | None = None) -> bool:
    """Test de Miller-Rabin con bases aleatorias en [2, n-2].

    False -> n es compuesto (seguro); True -> n es "probablemente primo".
    Con rng = random.Random(semilla) el resultado es reproducible.
    """
    if rondas < 1:
        raise ValueError("se requiere al menos una ronda")
    trivial = _casos_triviales(n)
    if trivial is not None:
        return trivial

    rng = rng or secrets.SystemRandom()
    s, d = descomponer(n)
    for _ in range(rondas):
        if cont is not None:
            cont.iteraciones += 1
        a = rng.randint(2, n - 2)
        if es_testigo(a, s, d, n, cont):
            return False
    return True


# ---------------------------------------------------------------------------
# Entrega 2
# ---------------------------------------------------------------------------
def miller_rabin_determinista(n: int, cont: Contador | None = None) -> bool:
    """Miller-Rabin con las 12 bases fijas 2, 3, ..., 37.

    Exacto (sin error) para n < LIMITE_DETERMINISTA ~ 3,18 x 10^23.
    Para n mayores lanza ValueError: ahí debe usarse es_primo o miller_rabin.
    """
    trivial = _casos_triviales(n)
    if trivial is not None:
        return trivial
    if n >= LIMITE_DETERMINISTA:
        raise ValueError(
            f"miller_rabin_determinista solo es exacto para n < {LIMITE_DETERMINISTA}")
    s, d = descomponer(n)
    for a in BASES_DETERMINISTAS:
        if a % n == 0:                       # n es una de las bases -> primo
            return True
        if cont is not None:
            cont.iteraciones += 1
        if es_testigo(a, s, d, n, cont):
            return False
    return True


def es_primo(n: int, rondas: int = RONDAS_POR_DEFECTO,
             rng: random.Random | None = None,
             cont: Contador | None = None) -> bool:
    """Fachada: exacta (determinista) bajo el límite, aleatoria por encima."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("es_primo requiere un entero")
    if n < LIMITE_DETERMINISTA:
        return miller_rabin_determinista(n, cont)
    return miller_rabin(n, rondas, rng, cont)


def criba_eratostenes(limite: int = LIMITE_CRIBA) -> list[int]:
    """Lista de los primos <= limite por la criba de Eratóstenes."""
    if limite < 2:
        return []
    marcado = bytearray([1]) * (limite + 1)
    marcado[0] = marcado[1] = 0
    i = 2
    while i * i <= limite:
        if marcado[i]:
            marcado[i * i::i] = bytearray(len(range(i * i, limite + 1, i)))
        i += 1
    return [k for k in range(limite + 1) if marcado[k]]


PRIMOS_PEQUENOS: tuple[int, ...] = tuple(criba_eratostenes(LIMITE_CRIBA - 1))  # 303 primos < 2000


def pasa_criba(n: int, cont: Contador | None = None) -> bool:
    """False si n tiene un factor primo < 2000 distinto de sí mismo.

    True significa "puede ser primo" (no lo garantiza para n >= 2000^2).
    """
    if n < 2:
        return False
    for p in PRIMOS_PEQUENOS:
        if p * p > n:
            return True                       # n < p^2 sin factores: es primo
        if cont is not None:
            cont.div_mod += 1
        if n % p == 0:
            return n == p
    return True


def generar_primo(bits: int, rng: random.Random | None = None,
                  criba: bool = True, dos_bits_altos: bool = False,
                  cont: Contador | None = None) -> int:
    """Genera un primo de exactamente ``bits`` bits (Algoritmo 2 del informe).

    1. Tomar un candidato aleatorio de ``bits`` bits; forzar el bit más alto
       (para que tenga exactamente ``bits`` bits) y el bit 0 (impar).
       Con dos_bits_altos=True también se fuerza el segundo bit más alto, así
       el producto de dos primos de b bits tiene exactamente 2b bits (RSA).
    2. Si criba=True, descartar el candidato si tiene un factor < 2000.
    3. Confirmar con es_primo (Miller-Rabin). Repetir hasta hallar un primo.

    Los candidatos salen de ``rng`` y las bases de Miller-Rabin de un
    generador derivado al inicio, de modo que con criba=True o criba=False
    se obtiene EL MISMO primo para la misma semilla.
    ``cont.iteraciones`` cuenta los candidatos probados.
    """
    if not isinstance(bits, int) or bits < 2:
        raise ValueError("bits debe ser un entero >= 2")
    if dos_bits_altos and bits < 3:
        raise ValueError("dos_bits_altos requiere bits >= 3")
    rng = rng or secrets.SystemRandom()
    if bits == 2:                              # únicos primos de 2 bits: 2 y 3
        return rng.choice((2, 3))
    rng_mr = random.Random(rng.getrandbits(64))

    mascara = (1 << (bits - 1)) | 1
    if dos_bits_altos:
        mascara |= 1 << (bits - 2)
    while True:
        candidato = rng.getrandbits(bits) | mascara
        if cont is not None:
            cont.iteraciones += 1
        if criba and not pasa_criba(candidato, cont):
            continue
        if es_primo(candidato, rng=rng_mr, cont=cont):
            return candidato
