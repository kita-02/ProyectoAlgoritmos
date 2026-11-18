"""Pestaña «Exponenciación modular»: ingenua, binaria y ventana deslizante."""
from __future__ import annotations

import random
from dataclasses import dataclass

from ..aritmetica import (exp_modular_ingenua, exp_modular_rapida, exp_modular_ventana,
                          ventana_optima)
from .comun import COLUMNAS_COMPARACION, Fila, comparar, leer_entero, porcentaje_menos

LIMITE_INGENUA = 10 ** 6       # la ingenua hace exp multiplicaciones


# ---------------------------------------------------------------- lógica
@dataclass
class ResultadoExponenciacion:
    filas: list[Fila]
    iguales: bool
    referencia: int            # pow(base, exp, mod) de Python
    k: int                     # tamaño de ventana usado
    ahorro_ventana: float      # % de multiplicaciones que ahorra la ventana

    @property
    def correcto(self) -> bool:
        return self.iguales and all(f.resultado == self.referencia for f in self.filas)


def comparar_exponenciacion(base: int, exp: int, mod: int,
                            k: int | None = None) -> ResultadoExponenciacion:
    if mod < 1:
        raise ValueError("El módulo debe ser mayor o igual que 1.")
    if exp < 0:
        raise ValueError("El exponente no puede ser negativo.")
    k_usado = k if k is not None else ventana_optima(max(exp.bit_length(), 1))
    alternativas = {
        "Binaria (base)": lambda c: exp_modular_rapida(base, exp, mod, c),
        f"Ventana deslizante (k = {k_usado})":
            lambda c: exp_modular_ventana(base, exp, mod, k=k_usado, cont=c),
    }
    if exp <= LIMITE_INGENUA:
        alternativas["Ingenua (referencia)"] = lambda c: exp_modular_ingenua(base, exp, mod, c)
    filas, iguales = comparar(alternativas)
    ahorro = porcentaje_menos(filas[0].mult, filas[1].mult)
    return ResultadoExponenciacion(filas, iguales, pow(base, exp, mod), k_usado, ahorro)


@dataclass
class PasoBinaria:
    iteracion: int
    bit: int
    r_antes: int
    potencia: int
    r_despues: int


def traza_binaria(base: int, exp: int, mod: int) -> list[PasoBinaria]:
    """Pasos de la exponenciación binaria (bits de derecha a izquierda)."""
    if mod < 1 or exp < 0:
        raise ValueError("Se requiere módulo >= 1 y exponente >= 0.")
    pasos, r, potencia, restante, i = [], 1 % mod, base % mod, exp, 0
    while restante > 0:
        i += 1
        bit = restante & 1
        antes = r
        if bit:
            r = (r * potencia) % mod
        pasos.append(PasoBinaria(i, bit, antes, potencia, r))
        restante >>= 1
        potencia = (potencia * potencia) % mod
    return pasos


def numeros_aleatorios(bits: int, semilla: int) -> tuple[int, int, int]:
    """Base, exponente y módulo impar de ``bits`` bits (reproducibles con la semilla)."""
    if bits < 4:
        raise ValueError("Use al menos 4 bits.")
    rng = random.Random(semilla)
    mod = rng.getrandbits(bits) | (1 << (bits - 1)) | 1
    return rng.randrange(2, mod), rng.getrandbits(bits) | (1 << (bits - 1)), mod


# ---------------------------------------------------------------- ventana
class PestanaExponenciacion:
    titulo = "Exponenciación modular"

    def __init__(self, padre, app) -> None:
        import tkinter as tk
        from tkinter import ttk

        from . import componentes as ui

        self.app, self.ui = app, ui
        self.marco = ttk.Frame(padre)
        ui.descripcion(self.marco, "Calcula base^exponente mod módulo con las tres alternativas "
                       "y compara cuántas multiplicaciones hace cada una. Todas deben dar el "
                       "mismo resultado que pow() de Python.")

        f = ui.seccion(self.marco, "Datos")
        self.base = ui.campo(f, 0, "Base", "65")
        self.exp = ui.campo(f, 1, "Exponente", "17")
        self.mod = ui.campo(f, 2, "Módulo", "3233")
        ttk.Label(f, text="Números aleatorios de").grid(row=0, column=2, sticky="e", padx=(24, 6))
        self.bits = tk.StringVar(value="1024")
        ttk.Combobox(f, textvariable=self.bits, values=("64", "256", "512", "1024", "2048"),
                     width=7).grid(row=0, column=3, sticky="w")
        ttk.Label(f, text="bits").grid(row=0, column=4, sticky="w", padx=4)
        ttk.Button(f, text="Generar", command=self.generar).grid(row=1, column=3, sticky="w")
        ttk.Button(f, text="Ejemplo del informe", command=self.ejemplo).grid(
            row=2, column=3, sticky="w")
        f.columnconfigure(1, weight=1)
        self.botones = ui.botones(f, ("Comparar alternativas", self.ejecutar),
                                  ("Ver paso a paso (binaria)", self.ver_traza))

        r = ui.seccion(self.marco, "Resultados")
        self.tabla = ui.Tabla(r, COLUMNAS_COMPARACION, alto=3)
        self.tabla.marco.pack(fill="x")
        self.veredicto = ui.Veredicto(r)
        self.veredicto.etiqueta.pack(fill="x", pady=(8, 0))

        t = ui.seccion(self.marco, "Paso a paso de la exponenciación binaria")
        self.traza = ui.Tabla(t, (("i", "Iteración", 80, "e"), ("bit", "Bit", 50, "e"),
                                  ("antes", "r antes", 220, "e"), ("pot", "Potencia", 220, "e"),
                                  ("despues", "r después", 220, "e")), alto=7)
        self.traza.marco.pack(fill="both", expand=True)

    def _datos(self) -> tuple[int, int, int]:
        return (leer_entero(self.base.get(), "la base"),
                leer_entero(self.exp.get(), "el exponente", 0),
                leer_entero(self.mod.get(), "el módulo", 1))

    def ejemplo(self) -> None:
        self.base.set("65"), self.exp.set("17"), self.mod.set("3233")

    def generar(self) -> None:
        try:
            b, e, m = numeros_aleatorios(leer_entero(self.bits.get(), "los bits"),
                                         self.app.semilla())
        except ValueError as exc:
            self.ui.mostrar_error(exc)
            return
        self.base.set(str(b)), self.exp.set(str(e)), self.mod.set(str(m))

    def ejecutar(self) -> None:
        try:
            datos = self._datos()
        except ValueError as exc:
            self.ui.mostrar_error(exc)
            return
        self.ui.ejecutar(self.app.raiz, self.app.estado, "Calculando…",
                         lambda: comparar_exponenciacion(*datos), self.mostrar, self.botones)

    def mostrar(self, res: ResultadoExponenciacion) -> None:
        self.tabla.limpiar()
        for i, f in enumerate(res.filas):
            self.tabla.agregar(f.celdas(), "destacada" if i == 1 else None)
        if res.correcto:
            self.veredicto.mostrar(
                f"Todas las alternativas dan el mismo resultado que pow() de Python. "
                f"La ventana deslizante hace {res.ahorro_ventana:.1f} % menos "
                f"multiplicaciones que la binaria.")
        else:
            self.veredicto.mostrar("Las alternativas NO coinciden con pow().", ok=False)

    def ver_traza(self) -> None:
        try:
            base, exp, mod = self._datos()
            if exp.bit_length() > 64:
                raise ValueError("El paso a paso se muestra para exponentes de hasta 64 bits.")
            pasos = traza_binaria(base, exp, mod)
        except ValueError as exc:
            self.ui.mostrar_error(exc)
            return
        self.traza.limpiar()
        for p in pasos:
            self.traza.agregar((p.iteracion, p.bit, p.r_antes, p.potencia, p.r_despues),
                               "destacada" if p.bit else None)
