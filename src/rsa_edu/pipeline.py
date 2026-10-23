"""Pipeline configurable: generación de claves -> cifrado -> descifrado.

ConfigPipeline activa o desactiva las alternativas que se comparan en los
experimentos, sin cambiar las entradas ni el formato de salida:

* criba    : filtrar candidatos a primo con la criba antes de Miller-Rabin.
* crt      : descifrar con el Teorema Chino del Resto.
* ventana  : exponenciación por ventana deslizante en lugar de la binaria.
* gmpy2    : usar gmpy2.powmod (GMP) para las exponenciaciones, si está
             instalado (si no, se informa y se usa la implementación propia).

Con la misma semilla todas las configuraciones generan LA MISMA clave y
deben recuperar exactamente los mismos mensajes.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field

from .contador import Contador
from .rsa import (KeyPair, cifrar, descifrar, descifrar_crt,
                  generar_claves_aleatorias)

try:                                     # dependencia opcional
    import gmpy2 as _gmpy2
except ImportError:                      # pragma: no cover - depende del entorno
    _gmpy2 = None


def gmpy2_disponible() -> bool:
    return _gmpy2 is not None


@dataclass(frozen=True)
class ConfigPipeline:
    bits: int = 512
    e: int | None = None          # None: 65537 (17 si bits < 40)
    semilla: int | None = 2026
    criba: bool = True
    crt: bool = False
    ventana: bool = False
    gmpy2: bool = False

    def nombre(self) -> str:
        partes = [f"{self.bits}b"]
        partes += [n for n, v in (("criba", self.criba), ("crt", self.crt),
                                  ("ventana", self.ventana), ("gmpy2", self.gmpy2)) if v]
        return "+".join(partes)


@dataclass
class ResultadoPipeline:
    config: ConfigPipeline
    claves: KeyPair
    mensajes: list[int]
    cifrados: list[int]
    descifrados: list[int]
    tiempos: dict[str, float]
    contador: Contador
    gmpy2_usado: bool
    avisos: list[str] = field(default_factory=list)

    @property
    def correcto(self) -> bool:
        return self.mensajes == self.descifrados


def _mensajes_aleatorios(n: int, cantidad: int, rng: random.Random) -> list[int]:
    return [rng.randrange(0, n) for _ in range(cantidad)]


def ejecutar_pipeline(config: ConfigPipeline,
                      mensajes: list[int] | None = None,
                      cantidad: int = 10) -> ResultadoPipeline:
    """Ejecuta las tres etapas y mide tiempo y operaciones de cada una."""
    rng = random.Random(config.semilla) if config.semilla is not None else random.SystemRandom()
    avisos: list[str] = []
    usar_gmpy2 = config.gmpy2 and gmpy2_disponible()
    if config.gmpy2 and not usar_gmpy2:
        avisos.append("gmpy2 no está instalado: se usó la implementación propia")

    cont = Contador()
    tiempos: dict[str, float] = {}

    t0 = time.perf_counter()
    claves = generar_claves_aleatorias(config.bits, config.e, rng=rng,
                                       criba=config.criba, cont=cont)
    tiempos["claves"] = time.perf_counter() - t0

    pub, priv = claves.publica, claves.privada
    if mensajes is None:
        mensajes = _mensajes_aleatorios(pub.n, cantidad, random.Random(rng.getrandbits(64)))
    for m in mensajes:
        if not isinstance(m, int) or not (0 <= m < pub.n):
            raise ValueError(f"mensaje fuera de rango: 0 <= m < n = {pub.n}")

    t0 = time.perf_counter()
    if usar_gmpy2:
        cifrados = [int(_gmpy2.powmod(m, pub.e, pub.n)) for m in mensajes]
    else:
        cifrados = [cifrar(m, pub, config.ventana, cont) for m in mensajes]
    tiempos["cifrado"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    if usar_gmpy2:
        if config.crt:
            descifrados = []
            for c in cifrados:
                m1 = int(_gmpy2.powmod(c, priv.dp, priv.p))
                m2 = int(_gmpy2.powmod(c, priv.dq, priv.q))
                descifrados.append(m2 + (priv.qinv * (m1 - m2) % priv.p) * priv.q)
        else:
            descifrados = [int(_gmpy2.powmod(c, priv.d, priv.n)) for c in cifrados]
    else:
        funcion = descifrar_crt if config.crt else descifrar
        descifrados = [funcion(c, priv, config.ventana, cont) for c in cifrados]
    tiempos["descifrado"] = time.perf_counter() - t0

    return ResultadoPipeline(config, claves, list(mensajes), cifrados, descifrados,
                             tiempos, cont, usar_gmpy2, avisos)


def configuraciones_estandar(bits: int = 512, semilla: int = 2026) -> list[ConfigPipeline]:
    """Las 6 configuraciones que se comparan en las pruebas de integración."""
    return [
        ConfigPipeline(bits, semilla=semilla, criba=False),
        ConfigPipeline(bits, semilla=semilla, criba=True),
        ConfigPipeline(bits, semilla=semilla, crt=True),
        ConfigPipeline(bits, semilla=semilla, ventana=True),
        ConfigPipeline(bits, semilla=semilla, crt=True, ventana=True),
        ConfigPipeline(bits, semilla=semilla, crt=True, gmpy2=True),
    ]
