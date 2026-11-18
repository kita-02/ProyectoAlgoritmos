"""Lógica común de la interfaz: lectura de entradas y comparación de alternativas.

No importa tkinter, así que se prueba sin pantalla.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

from ..contador import Contador


def leer_entero(texto: str, nombre: str = "el valor", minimo: int | None = None) -> int:
    """Convierte el texto de un campo en entero (acepta 0x..., 1_000, 2**61 - 1)."""
    t = str(texto).strip().replace("_", "").replace(" ", "")
    if not t:
        raise ValueError(f"Escriba {nombre}.")
    try:
        if "**" in t:
            base, resto = t.split("**", 1)
            ajuste = 0
            for signo in ("-", "+"):
                if signo in resto:
                    resto, cola = resto.split(signo, 1)
                    ajuste = int(cola, 0) * (-1 if signo == "-" else 1)
                    break
            valor = int(base, 0) ** int(resto, 0) + ajuste
        else:
            valor = int(t, 0)
    except ValueError:
        raise ValueError(f"{nombre.capitalize()} debe ser un número entero "
                         f"(se escribió «{texto}»).") from None
    if minimo is not None and valor < minimo:
        raise ValueError(f"{nombre.capitalize()} debe ser mayor o igual que {minimo}.")
    return valor


def abreviar(valor: Any, largo: int = 46) -> str:
    """Texto de una celda: los números muy largos se muestran como inicio…fin (bits)."""
    if isinstance(valor, list):
        texto = " × ".join(abreviar(v, 20) for v in valor) if valor else "1"
        return texto
    if isinstance(valor, bool):
        return "primo" if valor else "compuesto"
    texto = str(valor)
    if isinstance(valor, int) and len(texto) > largo:
        return f"{texto[:12]}…{texto[-8:]} ({valor.bit_length()} bits)"
    return texto if len(texto) <= largo else texto[: largo - 1] + "…"


@dataclass
class Fila:
    """Una alternativa ejecutada: resultado, tiempo y operaciones contadas."""

    alternativa: str
    resultado: Any
    ms: float
    mult: int
    div: int
    mcd: int
    iteraciones: int

    def celdas(self) -> tuple[str, ...]:
        return (self.alternativa, abreviar(self.resultado), f"{self.ms:,.3f}",
                f"{self.mult:,}", f"{self.div:,}", f"{self.iteraciones:,}")


def medir(funcion: Callable[[Contador], Any]) -> tuple[Any, float, Contador]:
    """Ejecuta funcion(contador) y devuelve (resultado, milisegundos, contador)."""
    cont = Contador()
    t0 = time.perf_counter()
    resultado = funcion(cont)
    return resultado, (time.perf_counter() - t0) * 1000, cont


def comparar(alternativas: dict[str, Callable[[Contador], Any]]) -> tuple[list[Fila], bool]:
    """Ejecuta cada alternativa sobre la misma entrada; indica si todas coinciden."""
    filas = []
    for nombre, funcion in alternativas.items():
        resultado, ms, c = medir(funcion)
        filas.append(Fila(nombre, resultado, ms, c.mult_mod, c.div_mod, c.mcd, c.iteraciones))
    iguales = len({repr(f.resultado) for f in filas}) <= 1
    return filas, iguales


def porcentaje_menos(base: int, otro: int) -> float:
    """Cuánto menos (en %) hace ``otro`` respecto de ``base``."""
    return 0.0 if base == 0 else 100.0 * (base - otro) / base


COLUMNAS_COMPARACION = (
    ("alternativa", "Alternativa", 190, "w"),
    ("resultado", "Resultado", 285, "w"),
    ("ms", "Tiempo (ms)", 95, "e"),
    ("mult", "Multiplicaciones", 135, "e"),
    ("div", "Divisiones", 90, "e"),
    ("iter", "Iteraciones", 90, "e"),
)
