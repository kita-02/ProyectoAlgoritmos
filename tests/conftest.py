"""Datos compartidos por la suite: casos básicos, límite y adversos.

Plan de pruebas: informe, sección 2 (Tabla 3).
"""
from __future__ import annotations

import random

import pytest

# Números de Carmichael (pasan Fermat para toda base coprima)
CARMICHAEL = [561, 1105, 1729, 2465, 2821, 6601, 8911, 10585, 15841, 29341,
              41041, 46657, 52633, 62745, 63973, 75361, 101101, 115921]

# Pseudoprimos fuertes: el menor compuesto que engaña a las primeras k bases
PSEUDOPRIMOS_FUERTES = [2047, 1373653, 25326001, 3215031751, 2152302898747,
                        3474749660383, 341550071728321, 3825123056546413051]

# Primos conocidos de distintos tamaños (incluye Mersenne)
PRIMOS_CONOCIDOS = [2, 3, 5, 7, 61, 53, 7919, 65537, 2147483647, 1000000007,
                    2305843009213693951, 618970019642690137449562111,
                    2 ** 127 - 1]

# Instancia del Avance 1 (resuelta a mano en el informe)
P, Q, E, M, C, D = 61, 53, 17, 65, 2790, 2753


@pytest.fixture
def rng() -> random.Random:
    return random.Random(2026)


@pytest.fixture
def clave_manual():
    from rsa_edu.rsa import generar_claves
    return generar_claves(P, Q, E)


@pytest.fixture(scope="session")
def clave_512():
    from rsa_edu.rsa import generar_claves_aleatorias
    return generar_claves_aleatorias(512, rng=random.Random(2026))
