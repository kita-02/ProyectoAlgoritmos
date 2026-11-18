"""Pestaña «RSA»: generar claves, cifrar y descifrar (directo o por TCR)."""
from __future__ import annotations

import random
from dataclasses import dataclass

from ..rsa import (KeyPair, cifrar, cifrar_texto, descifrar, descifrar_crt, descifrar_texto,
                   generar_claves, generar_claves_aleatorias)
from .comun import COLUMNAS_COMPARACION, Fila, abreviar, comparar, leer_entero, medir


# ---------------------------------------------------------------- lógica
def claves_manuales(p: int, q: int, e: int | None = None) -> KeyPair:
    return generar_claves(p, q, e)


def claves_aleatorias(bits: int, semilla: int = 2026, criba: bool = True) -> KeyPair:
    if not 16 <= bits <= 4096:
        raise ValueError("Los bits de la clave deben estar entre 16 y 4096.")
    return generar_claves_aleatorias(bits, rng=random.Random(semilla), criba=criba)


@dataclass
class Cifrado:
    es_texto: bool
    bloques: list[int]
    ms: float
    mult: int

    def como_texto(self) -> str:
        return ",".join(map(str, self.bloques))


def cifrar_mensaje(mensaje: str, claves: KeyPair, es_texto: bool,
                   ventana: bool = False) -> Cifrado:
    pub = claves.publica
    if es_texto:
        if not mensaje:
            raise ValueError("Escriba un mensaje.")
        bloques, ms, c = medir(lambda c: cifrar_texto(mensaje, pub, ventana, c))
    else:
        m = leer_entero(mensaje, "el mensaje", 0)
        if m >= pub.n:
            raise ValueError(f"El mensaje debe ser menor que n = {pub.n}.")
        valor, ms, c = medir(lambda c: cifrar(m, pub, ventana, c))
        bloques = [valor]
    return Cifrado(es_texto, bloques, ms, c.mult_mod)


@dataclass
class Descifrado:
    mensaje: str
    ms: float
    mult: int


def leer_bloques(texto: str) -> list[int]:
    partes = [p for p in str(texto).replace(";", ",").split(",") if p.strip()]
    if not partes:
        raise ValueError("Escriba el criptograma (números separados por comas).")
    return [leer_entero(p, "cada bloque del criptograma", 0) for p in partes]


def descifrar_mensaje(criptograma: str, claves: KeyPair, es_texto: bool,
                      crt: bool = False, ventana: bool = False) -> Descifrado:
    priv = claves.privada
    bloques = leer_bloques(criptograma)
    if es_texto:
        texto, ms, c = medir(lambda c: descifrar_texto(bloques, priv, crt, ventana, c))
    else:
        if len(bloques) != 1:
            raise ValueError("Para un número, el criptograma es un solo valor.")
        f = descifrar_crt if crt else descifrar
        valor, ms, c = medir(lambda c: f(bloques[0], priv, ventana, c))
        texto = str(valor)
    return Descifrado(texto, ms, c.mult_mod)


def comparar_descifrado(criptograma: str, claves: KeyPair) -> tuple[list[Fila], bool]:
    """Descifra el primer bloque con el método directo y con el TCR."""
    c = leer_bloques(criptograma)[0]
    priv = claves.privada
    return comparar({
        "Directo: c^d mod n (base)": lambda k: descifrar(c, priv, cont=k),
        "Teorema Chino del Resto": lambda k: descifrar_crt(c, priv, cont=k),
    })


# ---------------------------------------------------------------- ventana
class PestanaRSA:
    titulo = "RSA"

    def __init__(self, padre, app) -> None:
        import tkinter as tk
        from tkinter import ttk

        from . import componentes as ui

        self.app, self.ui, self.tk = app, ui, tk
        self.claves: KeyPair | None = None
        self.ultimo_mensaje = ""
        self.marco = ttk.Frame(padre)
        ui.descripcion(self.marco, "Genera un par de claves (con p y q propios o aleatorias "
                       "según FIPS 186-5), cifra un mensaje con la clave pública y lo "
                       "descifra con la clave privada, de forma directa o con el TCR.")

        # 1. claves
        k = ui.seccion(self.marco, "1. Claves")
        self.modo = tk.StringVar(value="manual")
        ttk.Radiobutton(k, text="Con p y q", variable=self.modo, value="manual").grid(
            row=0, column=0, sticky="w")
        ttk.Radiobutton(k, text="Aleatorias (FIPS 186-5)", variable=self.modo,
                        value="aleatoria").grid(row=0, column=2, sticky="w", padx=(24, 0))
        self.p = ui.campo(k, 1, "p", "61", ancho=22)
        self.q = ui.campo(k, 2, "q", "53", ancho=22)
        self.e = ui.campo(k, 3, "e (opcional)", "17", ancho=22)
        ttk.Label(k, text="Bits").grid(row=1, column=2, sticky="e", padx=(24, 6))
        self.bits = tk.StringVar(value="1024")
        ttk.Combobox(k, textvariable=self.bits, values=("512", "1024", "2048"),
                     width=8).grid(row=1, column=3, sticky="w")
        self.criba = tk.BooleanVar(value=True)
        ttk.Checkbutton(k, text="Usar criba al generar primos", variable=self.criba).grid(
            row=2, column=3, sticky="w")
        self.botones_claves = ui.botones(k, ("Generar claves", self.generar))
        self.info = tk.Text(k, height=4, width=100, font=("TkFixedFont", 9),
                            relief="flat", background="#f8f9fa")
        self.info.grid(row=100, column=0, columnspan=4, sticky="we", pady=(10, 0))
        k.columnconfigure(1, weight=1)

        # 2. cifrar
        c = ui.seccion(self.marco, "2. Cifrar con la clave pública (n, e)")
        self.es_texto = tk.BooleanVar(value=False)
        ttk.Radiobutton(c, text="Número", variable=self.es_texto, value=False).grid(
            row=0, column=0, sticky="w")
        ttk.Radiobutton(c, text="Texto", variable=self.es_texto, value=True).grid(
            row=0, column=1, sticky="w")
        self.mensaje = ui.campo(c, 1, "Mensaje", "65", ancho=60)
        self.ventana = tk.BooleanVar(value=False)
        ttk.Checkbutton(c, text="Exponenciación por ventana deslizante",
                        variable=self.ventana).grid(row=2, column=1, sticky="w")
        c.columnconfigure(1, weight=1)
        self.botones_cifrar = ui.botones(c, ("Cifrar", self.cifrar))
        self.cripto = ui.campo(c, 100, "Criptograma", "", ancho=60)

        # 3. descifrar
        d = ui.seccion(self.marco, "3. Descifrar con la clave privada d")
        self.metodo = tk.StringVar(value="directo")
        ttk.Radiobutton(d, text="Directo: c^d mod n", variable=self.metodo,
                        value="directo").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(d, text="Teorema Chino del Resto (TCR)", variable=self.metodo,
                        value="tcr").grid(row=0, column=1, sticky="w")
        self.botones_descifrar = ui.botones(d, ("Descifrar", self.descifrar),
                                            ("Comparar directo y TCR", self.comparar))
        self.recuperado = ui.campo(d, 100, "Mensaje recuperado", "", ancho=60)
        self.veredicto = ui.Veredicto(d)
        self.veredicto.etiqueta.grid(row=101, column=0, columnspan=4, sticky="w", pady=(6, 0))
        self.tabla = ui.Tabla(d, COLUMNAS_COMPARACION, alto=2)
        self.tabla.marco.grid(row=102, column=0, columnspan=4, sticky="we", pady=(8, 0))
        d.columnconfigure(1, weight=1)

    # -------------------------------------------------------------- acciones
    def _escribir_info(self, texto: str) -> None:
        self.info.configure(state="normal")
        self.info.delete("1.0", "end")
        self.info.insert("1.0", texto)
        self.info.configure(state="disabled")

    def generar(self) -> None:
        try:
            if self.modo.get() == "manual":
                p = leer_entero(self.p.get(), "p", 2)
                q = leer_entero(self.q.get(), "q", 2)
                e = leer_entero(self.e.get(), "e", 3) if self.e.get().strip() else None
                tarea = lambda: claves_manuales(p, q, e)  # noqa: E731
            else:
                bits, semilla, criba = (leer_entero(self.bits.get(), "los bits"),
                                        self.app.semilla(), self.criba.get())
                tarea = lambda: claves_aleatorias(bits, semilla, criba)  # noqa: E731
        except ValueError as exc:
            self.ui.mostrar_error(exc)
            return
        self.ui.ejecutar(self.app.raiz, self.app.estado, "Generando claves…", tarea,
                         self.mostrar_claves, self.botones_claves)

    def mostrar_claves(self, kp: KeyPair) -> None:
        self.claves = kp
        pub, priv = kp.publica, kp.privada
        a = lambda v: abreviar(v, 70)  # noqa: E731
        self._escribir_info(f"n = {a(pub.n)}   ({pub.n.bit_length()} bits)\n"
                            f"e = {pub.e}\n"
                            f"d = {a(priv.d)}\n"
                            f"p = {a(priv.p)}    q = {a(priv.q)}")
        if pub.n < 256:
            self.es_texto.set(False)
        self.veredicto.limpiar()

    def _requiere_claves(self) -> KeyPair:
        if self.claves is None:
            raise ValueError("Primero genere las claves (paso 1).")
        return self.claves

    def cifrar(self) -> None:
        try:
            kp = self._requiere_claves()
            res = cifrar_mensaje(self.mensaje.get(), kp, self.es_texto.get(), self.ventana.get())
        except (ValueError, TypeError) as exc:
            self.ui.mostrar_error(exc)
            return
        self.ultimo_mensaje = self.mensaje.get().strip() if self.es_texto.get() \
            else str(leer_entero(self.mensaje.get()))
        self.cripto.set(res.como_texto())
        self.app.estado.set(f"Cifrado en {res.ms:.3f} ms con {res.mult:,} multiplicaciones.")

    def descifrar(self) -> None:
        try:
            kp = self._requiere_claves()
            res = descifrar_mensaje(self.cripto.get(), kp, self.es_texto.get(),
                                    self.metodo.get() == "tcr", self.ventana.get())
        except (ValueError, TypeError) as exc:
            self.ui.mostrar_error(exc)
            return
        self.recuperado.set(res.mensaje)
        metodo = "TCR" if self.metodo.get() == "tcr" else "directo"
        if self.ultimo_mensaje and res.mensaje == self.ultimo_mensaje:
            self.veredicto.mostrar(f"El mensaje recuperado es igual al original "
                                   f"(descifrado {metodo}: {res.ms:.3f} ms, "
                                   f"{res.mult:,} multiplicaciones).")
        elif self.ultimo_mensaje:
            self.veredicto.mostrar("El mensaje recuperado es distinto del original.", ok=False)

    def comparar(self) -> None:
        try:
            kp = self._requiere_claves()
            filas, iguales = comparar_descifrado(self.cripto.get(), kp)
        except (ValueError, TypeError) as exc:
            self.ui.mostrar_error(exc)
            return
        self.tabla.limpiar()
        for i, f in enumerate(filas):
            self.tabla.agregar(f.celdas(), "destacada" if i == 1 else None)
        if iguales:
            self.veredicto.mostrar("Directo y TCR dan el mismo mensaje.")
        else:
            self.veredicto.mostrar("Directo y TCR dan resultados distintos.", ok=False)
