"""Pestaña «Optimización»: pipeline RSA base frente a optimizado."""
from __future__ import annotations

import random
import statistics
import time
from dataclasses import dataclass, field

from ..contador import Contador
from ..rsa import KeyPair, cifrar, descifrar, descifrar_crt, generar_claves_aleatorias

VERSIONES = {
    "Base": dict(criba=False, crt=False, ventana=False),
    "Optimizado": dict(criba=True, crt=True, ventana=True),
}
ETAPAS = ("Generar claves", "Cifrar", "Descifrar")


# ---------------------------------------------------------------- lógica
@dataclass
class Version:
    claves: KeyPair
    mensajes: list[int]
    cifrados: list[int]
    descifrados: list[int]
    ms: dict[str, float] = field(default_factory=dict)
    mult: dict[str, int] = field(default_factory=dict)


def ejecutar_version(bits: int, cantidad: int, semilla: int, criba: bool, crt: bool,
                     ventana: bool) -> Version:
    """Una ejecución del pipeline completo con tiempo y multiplicaciones por etapa."""
    conteos = {e: Contador() for e in ETAPAS}
    ms: dict[str, float] = {}
    t0 = time.perf_counter()
    claves = generar_claves_aleatorias(bits, rng=random.Random(semilla), criba=criba,
                                       cont=conteos["Generar claves"])
    ms["Generar claves"] = (time.perf_counter() - t0) * 1000
    pub, priv = claves.publica, claves.privada
    rng_m = random.Random(semilla + 1)
    mensajes = [rng_m.randrange(0, pub.n) for _ in range(cantidad)]
    # Con e = 65537 (17 bits) la ventana no ahorra nada al cifrar: ambas versiones
    # cifran con la exponenciación binaria (igual que scripts/demo_optimizacion.py).
    t0 = time.perf_counter()
    cifrados = [cifrar(m, pub, cont=conteos["Cifrar"]) for m in mensajes]
    ms["Cifrar"] = (time.perf_counter() - t0) * 1000
    funcion = descifrar_crt if crt else descifrar
    t0 = time.perf_counter()
    descifrados = [funcion(c, priv, ventana, conteos["Descifrar"]) for c in cifrados]
    ms["Descifrar"] = (time.perf_counter() - t0) * 1000
    return Version(claves, mensajes, cifrados, descifrados, ms,
                   {e: conteos[e].mult_mod for e in ETAPAS})


@dataclass
class Etapa:
    nombre: str
    ms_base: float
    ms_opt: float
    mult_base: int
    mult_opt: int

    @property
    def mejora(self) -> float:
        return self.ms_base / self.ms_opt if self.ms_opt > 0 else float("inf")


@dataclass
class ResultadoOptimizacion:
    bits: int
    etapas: list[Etapa]
    comprobaciones: list[tuple[str, bool]]

    @property
    def total(self) -> Etapa:
        return Etapa("Total", sum(e.ms_base for e in self.etapas),
                     sum(e.ms_opt for e in self.etapas),
                     sum(e.mult_base for e in self.etapas),
                     sum(e.mult_opt for e in self.etapas))

    @property
    def correcto(self) -> bool:
        return all(ok for _, ok in self.comprobaciones)


def comparar_pipeline(bits: int = 1024, cantidad: int = 10, semilla: int = 2026,
                      repeticiones: int = 3) -> ResultadoOptimizacion:
    if bits % 2 or not 64 <= bits <= 4096:
        raise ValueError("Los bits deben ser un número par entre 64 y 4096.")
    if not 1 <= cantidad <= 100 or not 1 <= repeticiones <= 10:
        raise ValueError("Use de 1 a 100 mensajes y de 1 a 10 repeticiones.")
    corridas = {v: [ejecutar_version(bits, cantidad, semilla, **cfg) for _ in range(repeticiones)]
                for v, cfg in VERSIONES.items()}
    b, o = corridas["Base"][0], corridas["Optimizado"][0]

    def mediana(version: str, etapa: str) -> float:
        return statistics.median(r.ms[etapa] for r in corridas[version])

    etapas = [Etapa(e, mediana("Base", e), mediana("Optimizado", e), b.mult[e], o.mult[e])
              for e in ETAPAS]
    pub = b.claves.publica
    comprobaciones = [
        ("Misma clave (n, e, d) en ambas versiones", b.claves == o.claves),
        ("Mismos mensajes y mismos cifrados", b.mensajes == o.mensajes
         and b.cifrados == o.cifrados),
        ("Cifrados iguales a pow(m, e, n) de Python",
         b.cifrados == [pow(m, pub.e, pub.n) for m in b.mensajes]),
        (f"La versión base recupera los {cantidad} mensajes", b.descifrados == b.mensajes),
        (f"La versión optimizada recupera los {cantidad} mensajes",
         o.descifrados == o.mensajes),
    ]
    return ResultadoOptimizacion(bits, etapas, comprobaciones)


# ---------------------------------------------------------------- ventana
class PestanaOptimizacion:
    titulo = "Optimización (base vs optimizado)"

    def __init__(self, padre, app) -> None:
        import tkinter as tk
        from tkinter import ttk

        from . import componentes as ui

        self.app, self.ui = app, ui
        self.marco = ttk.Frame(padre)
        ui.descripcion(self.marco, "Ejecuta el RSA completo dos veces con la misma semilla: con "
                       "las alternativas base (sin criba, descifrado directo, exponenciación "
                       "binaria) y con las optimizadas (criba, TCR y ventana deslizante al descifrar). "
                       "Primero comprueba que ambas hacen exactamente lo mismo y luego "
                       "compara el costo de cada etapa.")

        f = ui.seccion(self.marco, "Configuración")
        ttk.Label(f, text="Tamaño de la clave (bits)").grid(row=0, column=0, sticky="w",
                                                            padx=(0, 6))
        self.bits = tk.StringVar(value="1024")
        ttk.Combobox(f, textvariable=self.bits, values=("256", "512", "1024", "2048"),
                     width=8).grid(row=0, column=1, sticky="w")
        self.mensajes = ui.campo(f, 1, "Mensajes", "10", ancho=8)
        self.repeticiones = ui.campo(f, 2, "Repeticiones (mediana)", "3", ancho=8)
        self.botones = ui.botones(f, ("Ejecutar base y optimizado", self.ejecutar))

        r = ui.seccion(self.marco, "¿Hacen lo mismo?")
        self.lista = ttk.Frame(r)
        self.lista.pack(fill="x")
        self.etiquetas: list[ttk.Label] = []

        t = ui.seccion(self.marco, "¿Cuánto mejora cada etapa?")
        self.tabla = ui.Tabla(t, (
            ("etapa", "Etapa", 140, "w"), ("base", "Base (ms)", 110, "e"),
            ("opt", "Optimizado (ms)", 135, "e"), ("mejora", "Mejora", 80, "e"),
            ("mb", "Mult. base", 120, "e"), ("mo", "Mult. optimizado", 130, "e")), alto=4)
        self.tabla.marco.pack(fill="x")
        self.veredicto = ui.Veredicto(t)
        self.veredicto.etiqueta.pack(fill="x", pady=(8, 0))
        self.lienzo = tk.Canvas(t, height=170, background="white", highlightthickness=0)
        self.lienzo.pack(fill="x", pady=(8, 0))

    def ejecutar(self) -> None:
        from .comun import leer_entero
        try:
            bits = leer_entero(self.bits.get(), "los bits")
            cantidad = leer_entero(self.mensajes.get(), "los mensajes", 1)
            rep = leer_entero(self.repeticiones.get(), "las repeticiones", 1)
            semilla = self.app.semilla()
        except ValueError as exc:
            self.ui.mostrar_error(exc)
            return
        self.ui.ejecutar(self.app.raiz, self.app.estado,
                         f"Ejecutando el pipeline de {bits} bits (base y optimizado)…",
                         lambda: comparar_pipeline(bits, cantidad, semilla, rep),
                         self.mostrar, self.botones)

    def mostrar(self, res: ResultadoOptimizacion) -> None:
        from tkinter import ttk
        for e in self.etiquetas:
            e.destroy()
        self.etiquetas = []
        for texto, ok in res.comprobaciones:
            lbl = ttk.Label(self.lista, text=("✓  " if ok else "✗  ") + texto,
                            foreground=self.ui.COLOR_OK if ok else self.ui.COLOR_FALLA)
            lbl.pack(anchor="w")
            self.etiquetas.append(lbl)

        self.tabla.limpiar()
        for e in res.etapas + [res.total]:
            self.tabla.agregar((e.nombre, f"{e.ms_base:,.2f}", f"{e.ms_opt:,.2f}",
                                f"{e.mejora:.2f}×", f"{e.mult_base:,}", f"{e.mult_opt:,}"),
                               "destacada" if e.nombre == "Total" else None)
        total = res.total
        if res.correcto:
            self.veredicto.mostrar(f"Mismo resultado y {total.mejora:.2f} veces más rápido "
                                   f"con claves de {res.bits} bits.")
        else:
            self.veredicto.mostrar("Las versiones no dan el mismo resultado.", ok=False)
        self.ui.grafico_barras(self.lienzo, [e.nombre for e in res.etapas] + ["Total"], [
            ("Base", self.ui.COLOR_BASE, [e.ms_base for e in res.etapas] + [total.ms_base]),
            ("Optimizado", self.ui.COLOR_OPTIMIZADO,
             [e.ms_opt for e in res.etapas] + [total.ms_opt]),
        ])
