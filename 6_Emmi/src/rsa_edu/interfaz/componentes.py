"""Componentes de la ventana reutilizados por todas las pestañas (Tkinter)."""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable

COLOR_OK = "#1e7b34"
COLOR_FALLA = "#b3261e"
COLOR_TEXTO_SUAVE = "#5f6368"
COLOR_BASE = "#9aa0a6"
COLOR_OPTIMIZADO = "#1a73e8"

# En las pruebas automáticas las tareas se ejecutan en el mismo hilo.
SINCRONO = False


class Desplazable:
    """Marco con barra de desplazamiento vertical (para pestañas largas)."""

    def __init__(self, padre: tk.Misc) -> None:
        self.externo = ttk.Frame(padre)
        self.lienzo = tk.Canvas(self.externo, highlightthickness=0, borderwidth=0)
        barra = ttk.Scrollbar(self.externo, orient="vertical", command=self.lienzo.yview)
        self.interno = ttk.Frame(self.lienzo)
        ventana = self.lienzo.create_window((0, 0), window=self.interno, anchor="nw")
        self.interno.bind("<Configure>", lambda _e: self.lienzo.configure(
            scrollregion=self.lienzo.bbox("all")))
        self.lienzo.bind("<Configure>", lambda e: self.lienzo.itemconfigure(
            ventana, width=e.width))
        self.lienzo.configure(yscrollcommand=barra.set)
        self.lienzo.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        self.externo.bind("<Enter>", lambda _e: self.lienzo.bind_all(
            "<MouseWheel>", self._rueda))
        self.externo.bind("<Leave>", lambda _e: self.lienzo.unbind_all("<MouseWheel>"))

    def _rueda(self, evento) -> None:
        self.lienzo.yview_scroll(int(-evento.delta / 120) or (-1 if evento.delta > 0 else 1),
                                 "units")


def campo(padre: tk.Misc, fila: int, etiqueta: str, valor: str = "",
          ancho: int = 28, columna: int = 0) -> tk.StringVar:
    """Etiqueta + caja de texto en una grilla; devuelve la variable del texto."""
    ttk.Label(padre, text=etiqueta).grid(row=fila, column=columna, sticky="w",
                                         padx=(0, 6), pady=3)
    var = tk.StringVar(value=valor)
    ttk.Entry(padre, textvariable=var, width=ancho).grid(row=fila, column=columna + 1,
                                                         sticky="we", pady=3)
    return var


def seccion(padre: tk.Misc, titulo: str) -> ttk.LabelFrame:
    marco = ttk.LabelFrame(padre, text=titulo, padding=10)
    marco.pack(fill="x", padx=10, pady=(10, 0))
    return marco


def descripcion(padre: tk.Misc, texto: str) -> ttk.Label:
    lbl = ttk.Label(padre, text=texto, foreground=COLOR_TEXTO_SUAVE, wraplength=900,
                    justify="left")
    lbl.pack(fill="x", padx=12, pady=(10, 0))
    return lbl


class Tabla:
    """Tabla de resultados (Treeview) con barra de desplazamiento."""

    def __init__(self, padre: tk.Misc, columnas, alto: int = 5) -> None:
        self.marco = ttk.Frame(padre)
        ids = [c[0] for c in columnas]
        self.vista = ttk.Treeview(self.marco, columns=ids, show="headings", height=alto)
        for ident, titulo, ancho, alin in columnas:
            self.vista.heading(ident, text=titulo, anchor=alin)
            self.vista.column(ident, width=ancho, anchor=alin, stretch=(alin == "w"))
        barra = ttk.Scrollbar(self.marco, orient="vertical", command=self.vista.yview)
        self.vista.configure(yscrollcommand=barra.set)
        self.vista.tag_configure("falla", foreground=COLOR_FALLA)
        self.vista.tag_configure("destacada", background="#e8f0fe")
        self.vista.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

    def limpiar(self) -> None:
        self.vista.delete(*self.vista.get_children())

    def agregar(self, valores, etiqueta: str | None = None) -> None:
        self.vista.insert("", "end", values=list(valores),
                          tags=(etiqueta,) if etiqueta else ())

    def filas(self) -> list[tuple]:
        return [tuple(self.vista.item(i, "values")) for i in self.vista.get_children()]


class Veredicto:
    """Línea de conclusión en verde (✓) o rojo (✗)."""

    def __init__(self, padre: tk.Misc) -> None:
        self.etiqueta = ttk.Label(padre, text="", wraplength=900, justify="left",
                                  font=("TkDefaultFont", 10, "bold"))

    def mostrar(self, texto: str, ok: bool = True) -> None:
        self.etiqueta.configure(text=("✓ " if ok else "✗ ") + texto,
                                foreground=COLOR_OK if ok else COLOR_FALLA)

    def limpiar(self) -> None:
        self.etiqueta.configure(text="")

    @property
    def texto(self) -> str:
        return str(self.etiqueta.cget("text"))


def mostrar_error(exc: BaseException) -> None:
    if SINCRONO:            # en las pruebas no se abren diálogos
        raise exc
    messagebox.showerror("rsa_edu", str(exc))


def ejecutar(raiz: tk.Misc, estado: tk.StringVar | None, mensaje: str,
             tarea: Callable[[], Any], al_terminar: Callable[[Any], None],
             botones: list[ttk.Button] | tuple = ()) -> None:
    """Corre ``tarea`` sin congelar la ventana y luego llama ``al_terminar``."""
    if SINCRONO:
        try:
            al_terminar(tarea())
        except (ValueError, TypeError, RuntimeError) as exc:
            mostrar_error(exc)
        return

    for b in botones:
        b.state(["disabled"])
    if estado is not None:
        estado.set(mensaje)
    caja: dict[str, Any] = {}

    def trabajo() -> None:
        try:
            caja["ok"] = tarea()
        except Exception as exc:  # se muestra en la ventana
            caja["error"] = exc

    hilo = threading.Thread(target=trabajo, daemon=True)
    hilo.start()

    def revisar() -> None:
        if hilo.is_alive():
            raiz.after(80, revisar)
            return
        for b in botones:
            b.state(["!disabled"])
        if estado is not None:
            estado.set("Listo.")
        if "error" in caja:
            mostrar_error(caja["error"])
        else:
            al_terminar(caja["ok"])

    raiz.after(80, revisar)


def botones(padre: tk.Misc, *pares: tuple[str, Callable[[], None]]) -> list[ttk.Button]:
    """Fila de botones; el primero se marca como acción principal."""
    marco = ttk.Frame(padre)
    marco.grid(row=99, column=0, columnspan=4, sticky="w", pady=(8, 0))
    lista = []
    for i, (texto, accion) in enumerate(pares):
        b = ttk.Button(marco, text=texto, command=accion,
                       style="Accent.TButton" if i == 0 else "TButton")
        b.pack(side="left", padx=(0, 8))
        lista.append(b)
    return lista


def grafico_barras(lienzo: tk.Canvas, categorias: list[str],
                   series: list[tuple[str, str, list[float]]], unidad: str = "ms") -> None:
    """Barras horizontales agrupadas: series = [(nombre, color, valores), ...]."""
    lienzo.delete("all")
    lienzo.update_idletasks()
    ancho = max(int(lienzo.winfo_width()), 520)
    margen_izq, margen_der, alto_barra, sep = 130, 90, 16, 14
    maximo = max((v for _, _, vals in series for v in vals), default=1.0) or 1.0
    y = 12
    for i, cat in enumerate(categorias):
        lienzo.create_text(margen_izq - 10, y + alto_barra * len(series) / 2,
                           text=cat, anchor="e", font=("TkDefaultFont", 9))
        for nombre, color, valores in series:
            largo = (ancho - margen_izq - margen_der) * valores[i] / maximo
            lienzo.create_rectangle(margen_izq, y, margen_izq + max(largo, 1),
                                    y + alto_barra - 2, fill=color, outline="")
            lienzo.create_text(margen_izq + max(largo, 1) + 6, y + alto_barra / 2 - 1,
                               text=f"{valores[i]:,.1f} {unidad}", anchor="w",
                               font=("TkDefaultFont", 8))
            y += alto_barra
        y += sep
    x = margen_izq
    for nombre, color, _ in series:
        lienzo.create_rectangle(x, y, x + 12, y + 12, fill=color, outline="")
        lienzo.create_text(x + 18, y + 6, text=nombre, anchor="w", font=("TkDefaultFont", 9))
        x += 30 + 8 * len(nombre)
    lienzo.configure(height=y + 24)
