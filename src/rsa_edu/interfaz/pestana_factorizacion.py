"""Pestaña «Factorización y ataque»: división de prueba, Pollard Rho y Brent."""
from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass

from ..ataque import ClaveRota, romper_clave
from ..factorizacion import factorizar
from ..primalidad import es_primo, generar_primo
from .comun import Fila, comparar, leer_entero

LIMITE_TENTATIVA = 2 ** 48     # más allá la división de prueba tarda demasiado
METODOS_ATAQUE = {"Brent": "brent", "Pollard Rho (Floyd)": "rho",
                  "División de prueba": "tentativa"}

COLUMNAS = (
    ("alternativa", "Método", 190, "w"),
    ("resultado", "Factores", 270, "w"),
    ("ms", "Tiempo (ms)", 95, "e"),
    ("mult", "Multiplicaciones", 135, "e"),
    ("div", "Divisiones", 90, "e"),
    ("mcd", "Llamadas a mcd", 125, "e"),
)


# ---------------------------------------------------------------- lógica
@dataclass
class ResultadoFactorizacion:
    n: int
    filas: list[Fila]
    iguales: bool
    omitidas: list[str]

    @property
    def verificado(self) -> bool:
        """Producto igual a n y todos los factores primos."""
        f = self.filas[0].resultado
        return self.iguales and math.prod(f) == self.n and all(es_primo(p) for p in f)


def comparar_factorizacion(n: int, semilla: int = 2026) -> ResultadoFactorizacion:
    if n < 2:
        raise ValueError("n debe ser mayor o igual que 2.")
    alternativas, omitidas = {}, []
    if n < LIMITE_TENTATIVA:
        alternativas["División de prueba (base)"] = lambda c: factorizar(n, "tentativa", cont=c)
    else:
        omitidas.append("División de prueba (n ≥ 2^48: tardaría demasiado)")
    alternativas["Pollard Rho (Floyd)"] = \
        lambda c: factorizar(n, "rho", rng=random.Random(semilla), cont=c)
    alternativas["Pollard Rho (Brent)"] = \
        lambda c: factorizar(n, "brent", rng=random.Random(semilla), cont=c)
    filas, iguales = comparar(alternativas)
    return ResultadoFactorizacion(n, filas, iguales, omitidas)


def semiprimo_aleatorio(bits: int, semilla: int = 2026) -> tuple[int, int, int]:
    """n = p·q con p y q primos distintos de bits/2 bits (como un módulo RSA)."""
    if bits < 8 or bits > 128:
        raise ValueError("Use entre 8 y 128 bits.")
    rng = random.Random(semilla)
    p = generar_primo(bits // 2, rng, dos_bits_altos=True)
    q = p
    while q == p:
        q = generar_primo(bits - bits // 2, rng, dos_bits_altos=True)
    return p * q, min(p, q), max(p, q)


@dataclass
class ResultadoAtaque:
    clave: ClaveRota
    metodo: str
    ms: float

    @property
    def verificado(self) -> bool:
        c = self.clave
        return c.p * c.q == c.n and (c.e * c.d) % c.phi == 1


def atacar(n: int, e: int, metodo: str = "brent", semilla: int = 2026) -> ResultadoAtaque:
    if metodo == "tentativa" and n >= LIMITE_TENTATIVA:
        raise ValueError("Con la división de prueba use n < 2^48; para n mayores elija Brent.")
    t0 = time.perf_counter()
    clave = romper_clave(n, e, metodo, rng=random.Random(semilla))
    return ResultadoAtaque(clave, metodo, (time.perf_counter() - t0) * 1000)


# ---------------------------------------------------------------- ventana
class PestanaFactorizacion:
    titulo = "Factorización y ataque"

    def __init__(self, padre, app) -> None:
        import tkinter as tk
        from tkinter import ttk

        from . import componentes as ui

        self.app, self.ui = app, ui
        self.marco = ttk.Frame(padre)
        ui.descripcion(self.marco, "Factoriza n con los tres métodos y muestra el ataque a RSA: "
                       "quien logra factorizar n = p·q obtiene φ(n) y la clave privada d "
                       "usando solo la clave pública (n, e).")

        f = ui.seccion(self.marco, "Factorizar n")
        self.n = ui.campo(f, 0, "n", "8051", ancho=40)
        ttk.Label(f, text="Semiprimo aleatorio de").grid(row=0, column=2, sticky="e",
                                                          padx=(24, 6))
        self.bits = tk.StringVar(value="48")
        ttk.Combobox(f, textvariable=self.bits, values=("24", "32", "40", "48", "56", "64"),
                     width=6).grid(row=0, column=3, sticky="w")
        ttk.Label(f, text="bits").grid(row=0, column=4, sticky="w", padx=4)
        ttk.Button(f, text="Generar", command=self.generar).grid(row=1, column=3, sticky="w")
        f.columnconfigure(1, weight=1)
        self.botones = ui.botones(f, ("Comparar métodos", self.ejecutar))
        self.tabla = ui.Tabla(f, COLUMNAS, alto=3)
        self.tabla.marco.grid(row=100, column=0, columnspan=5, sticky="we", pady=(10, 0))
        self.veredicto = ui.Veredicto(f)
        self.veredicto.etiqueta.grid(row=101, column=0, columnspan=5, sticky="w", pady=(8, 0))

        a = ui.seccion(self.marco, "Ataque por factorización (solo con la clave pública)")
        self.an = ui.campo(a, 0, "n", "3233", ancho=40)
        self.ae = ui.campo(a, 1, "e", "17", ancho=40)
        ttk.Label(a, text="Método").grid(row=0, column=2, sticky="e", padx=(24, 6))
        self.metodo = tk.StringVar(value="Brent")
        ttk.Combobox(a, textvariable=self.metodo, values=list(METODOS_ATAQUE),
                     state="readonly", width=20).grid(row=0, column=3, sticky="w")
        a.columnconfigure(1, weight=1)
        self.botones_ataque = ui.botones(a, ("Atacar", self.ejecutar_ataque))
        self.salida = tk.Text(a, height=6, width=90, font=("TkFixedFont", 10),
                              relief="flat", background="#f8f9fa")
        self.salida.grid(row=100, column=0, columnspan=5, sticky="we", pady=(10, 0))
        self.veredicto_ataque = ui.Veredicto(a)
        self.veredicto_ataque.etiqueta.grid(row=101, column=0, columnspan=5, sticky="w",
                                            pady=(8, 0))

    def generar(self) -> None:
        try:
            n, _, _ = semiprimo_aleatorio(leer_entero(self.bits.get(), "los bits"),
                                          self.app.semilla())
        except ValueError as exc:
            self.ui.mostrar_error(exc)
            return
        self.n.set(str(n))

    def ejecutar(self) -> None:
        try:
            n = leer_entero(self.n.get(), "n", 2)
            semilla = self.app.semilla()
        except ValueError as exc:
            self.ui.mostrar_error(exc)
            return
        self.ui.ejecutar(self.app.raiz, self.app.estado, "Factorizando…",
                         lambda: comparar_factorizacion(n, semilla), self.mostrar, self.botones)

    def mostrar(self, res: ResultadoFactorizacion) -> None:
        self.tabla.limpiar()
        for i, f in enumerate(res.filas):
            c = f.celdas()
            self.tabla.agregar((c[0], c[1], c[2], c[3], c[4], f"{f.mcd:,}"),
                               "destacada" if f.alternativa.endswith("(Brent)") else None)
        for o in res.omitidas:
            self.tabla.agregar((o, "omitido", "", "", "", ""), "falla")
        if res.verificado:
            factores = " × ".join(map(str, res.filas[0].resultado))
            self.veredicto.mostrar(f"Todos los métodos coinciden: n = {factores} "
                                   f"(producto verificado y factores primos).")
        else:
            self.veredicto.mostrar("Los métodos no coinciden o la verificación falló.", ok=False)

    def ejecutar_ataque(self) -> None:
        try:
            n = leer_entero(self.an.get(), "n", 6)
            e = leer_entero(self.ae.get(), "e", 3)
            semilla = self.app.semilla()
        except ValueError as exc:
            self.ui.mostrar_error(exc)
            return
        metodo = METODOS_ATAQUE[self.metodo.get()]
        self.ui.ejecutar(self.app.raiz, self.app.estado, "Atacando la clave…",
                         lambda: atacar(n, e, metodo, semilla), self.mostrar_ataque,
                         self.botones_ataque)

    def mostrar_ataque(self, res: ResultadoAtaque) -> None:
        c = res.clave
        texto = (f"Clave pública conocida:  n = {c.n}\n"
                 f"                         e = {c.e}\n"
                 f"1. Factorizar n:         p = {c.p},  q = {c.q}   ({res.ms:.2f} ms)\n"
                 f"2. Calcular φ(n):        (p − 1)(q − 1) = {c.phi}\n"
                 f"3. Clave privada:        d = e⁻¹ mod φ(n) = {c.d}")
        self.salida.configure(state="normal")
        self.salida.delete("1.0", "end")
        self.salida.insert("1.0", texto)
        self.salida.configure(state="disabled")
        if res.verificado:
            self.veredicto_ataque.mostrar("Clave privada recuperada: p·q = n y e·d mod φ(n) = 1.")
        else:
            self.veredicto_ataque.mostrar("La verificación de la clave falló.", ok=False)

    def texto_ataque(self) -> str:
        return self.salida.get("1.0", "end").strip()
