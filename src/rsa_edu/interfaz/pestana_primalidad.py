"""Pestaña «Primalidad»: división de prueba, Miller-Rabin y generación de primos."""
from __future__ import annotations

import random
from dataclasses import dataclass

from ..primalidad import (LIMITE_DETERMINISTA, division_tentativa, generar_primo,
                          miller_rabin, miller_rabin_determinista)
from .comun import COLUMNAS_COMPARACION, Fila, comparar, leer_entero, porcentaje_menos

LIMITE_DIVISION = 2 ** 48      # más allá la división de prueba tarda demasiado

EJEMPLOS = {
    "561 (Carmichael)": "561",
    "2047 (pseudoprimo fuerte)": "2047",
    "3233 = 53 × 61": "3233",
    "2^61 − 1 (Mersenne)": "2**61-1",
    "2^89 − 1 (Mersenne)": "2**89-1",
}


# ---------------------------------------------------------------- lógica
@dataclass
class ResultadoPrimalidad:
    n: int
    filas: list[Fila]
    iguales: bool
    omitidas: list[str]

    @property
    def es_primo(self) -> bool:
        return bool(self.filas[0].resultado)


def comparar_primalidad(n: int, semilla: int = 2026) -> ResultadoPrimalidad:
    if n < 0:
        raise ValueError("n debe ser un entero no negativo.")
    alternativas, omitidas = {}, []
    if n < LIMITE_DIVISION:
        alternativas["División de prueba (base)"] = lambda c: division_tentativa(n, c)
    else:
        omitidas.append("División de prueba (n ≥ 2^48: tardaría demasiado)")
    alternativas["Miller–Rabin, 20 rondas"] = \
        lambda c: miller_rabin(n, rng=random.Random(semilla), cont=c)
    if n < LIMITE_DETERMINISTA:
        alternativas["Miller–Rabin determinista"] = lambda c: miller_rabin_determinista(n, c)
    else:
        omitidas.append("Miller–Rabin determinista (solo es exacto para n < 3,18·10^23)")
    filas, iguales = comparar(alternativas)
    return ResultadoPrimalidad(n, filas, iguales, omitidas)


@dataclass
class ResultadoGeneracion:
    bits: int
    filas: list[Fila]          # sin criba, con criba
    mismo_primo: bool

    @property
    def ahorro(self) -> float:
        return porcentaje_menos(self.filas[0].mult, self.filas[1].mult)


def comparar_generacion(bits: int, semilla: int = 2026) -> ResultadoGeneracion:
    if not 8 <= bits <= 2048:
        raise ValueError("Los bits deben estar entre 8 y 2048.")
    filas, iguales = comparar({
        "Sin criba (base)": lambda c: generar_primo(bits, random.Random(semilla),
                                                    criba=False, cont=c),
        "Con criba de primos < 2000": lambda c: generar_primo(bits, random.Random(semilla),
                                                             criba=True, cont=c),
    })
    return ResultadoGeneracion(bits, filas, iguales)


# ---------------------------------------------------------------- ventana
class PestanaPrimalidad:
    titulo = "Primalidad"

    def __init__(self, padre, app) -> None:
        import tkinter as tk
        from tkinter import ttk

        from . import componentes as ui

        self.app, self.ui = app, ui
        self.marco = ttk.Frame(padre)
        ui.descripcion(self.marco, "Decide si n es primo con las tres pruebas, y genera un "
                       "primo con y sin criba de primos pequeños. La criba descarta antes a "
                       "los candidatos con un factor menor que 2000.")

        f = ui.seccion(self.marco, "¿Es primo?")
        self.n = ui.campo(f, 0, "n", "561", ancho=40)
        ttk.Label(f, text="Ejemplos").grid(row=0, column=2, sticky="e", padx=(24, 6))
        self.ejemplo = tk.StringVar()
        cb = ttk.Combobox(f, textvariable=self.ejemplo, values=list(EJEMPLOS),
                          state="readonly", width=26)
        cb.grid(row=0, column=3, sticky="w")
        cb.bind("<<ComboboxSelected>>", lambda _e: self.n.set(EJEMPLOS[self.ejemplo.get()]))
        f.columnconfigure(1, weight=1)
        self.botones = ui.botones(f, ("Comparar pruebas", self.ejecutar))
        self.tabla = ui.Tabla(f, COLUMNAS_COMPARACION, alto=3)
        self.tabla.marco.grid(row=100, column=0, columnspan=4, sticky="we", pady=(10, 0))
        self.veredicto = ui.Veredicto(f)
        self.veredicto.etiqueta.grid(row=101, column=0, columnspan=4, sticky="w", pady=(8, 0))

        g = ui.seccion(self.marco, "Generar un primo")
        self.bits = ui.campo(g, 0, "Bits", "512", ancho=10)
        self.botones_gen = ui.botones(g, ("Generar con y sin criba", self.generar))
        self.tabla_gen = ui.Tabla(g, COLUMNAS_COMPARACION, alto=2)
        self.tabla_gen.marco.grid(row=100, column=0, columnspan=4, sticky="we", pady=(10, 0))
        self.veredicto_gen = ui.Veredicto(g)
        self.veredicto_gen.etiqueta.grid(row=101, column=0, columnspan=4, sticky="w",
                                         pady=(8, 0))
        g.columnconfigure(3, weight=1)

    def ejecutar(self) -> None:
        try:
            n = leer_entero(self.n.get(), "n", 0)
            semilla = self.app.semilla()
        except ValueError as exc:
            self.ui.mostrar_error(exc)
            return
        self.ui.ejecutar(self.app.raiz, self.app.estado, "Probando primalidad…",
                         lambda: comparar_primalidad(n, semilla), self.mostrar, self.botones)

    def mostrar(self, res: ResultadoPrimalidad) -> None:
        self.tabla.limpiar()
        for f in res.filas:
            self.tabla.agregar(f.celdas())
        for o in res.omitidas:
            self.tabla.agregar((o, "omitida", "", "", "", ""), "falla")
        if res.iguales:
            self.veredicto.mostrar(f"Todas las pruebas coinciden: n es "
                                   f"{'PRIMO' if res.es_primo else 'COMPUESTO'}.")
        else:
            self.veredicto.mostrar("Las pruebas no coinciden.", ok=False)

    def generar(self) -> None:
        try:
            bits = leer_entero(self.bits.get(), "los bits")
            semilla = self.app.semilla()
        except ValueError as exc:
            self.ui.mostrar_error(exc)
            return
        self.ui.ejecutar(self.app.raiz, self.app.estado, "Generando primo…",
                         lambda: comparar_generacion(bits, semilla), self.mostrar_gen,
                         self.botones_gen)

    def mostrar_gen(self, res: ResultadoGeneracion) -> None:
        self.tabla_gen.limpiar()
        for i, f in enumerate(res.filas):
            self.tabla_gen.agregar(f.celdas(), "destacada" if i == 1 else None)
        if res.mismo_primo:
            self.veredicto_gen.mostrar(
                f"Con y sin criba se obtiene el mismo primo de {res.bits} bits; la criba "
                f"hace {res.ahorro:.1f} % menos multiplicaciones.")
        else:
            self.veredicto_gen.mostrar("Con y sin criba se obtuvieron primos distintos.", ok=False)
