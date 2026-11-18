"""Ventana principal de la interfaz gráfica de rsa_edu."""
from __future__ import annotations

import sys

from .. import __version__
from .comun import leer_entero
from .pestana_exponenciacion import PestanaExponenciacion
from .pestana_factorizacion import PestanaFactorizacion
from .pestana_optimizacion import PestanaOptimizacion
from .pestana_primalidad import PestanaPrimalidad
from .pestana_rsa import PestanaRSA

PESTANAS = (PestanaRSA, PestanaExponenciacion, PestanaPrimalidad, PestanaFactorizacion,
            PestanaOptimizacion)


class Aplicacion:
    def __init__(self, visible: bool = True) -> None:
        import tkinter as tk
        from tkinter import ttk

        from . import componentes as ui

        self.raiz = tk.Tk()
        if not visible:
            self.raiz.withdraw()
        self.raiz.title(f"rsa_edu {__version__} — Biblioteca educativa RSA (Grupo 6)")
        self.raiz.geometry("1120x800")
        self.raiz.minsize(900, 600)

        estilo = ttk.Style(self.raiz)
        if "vista" in estilo.theme_names():          # Windows
            estilo.theme_use("vista")
        elif "clam" in estilo.theme_names():
            estilo.theme_use("clam")
        estilo.configure("Accent.TButton", font=("TkDefaultFont", 9, "bold"))
        estilo.configure("Titulo.TLabel", font=("TkDefaultFont", 14, "bold"))
        estilo.configure("Treeview", rowheight=22)

        cabecera = ttk.Frame(self.raiz, padding=(14, 10))
        cabecera.pack(fill="x")
        ttk.Label(cabecera, text="Optimización del pipeline RSA",
                  style="Titulo.TLabel").pack(side="left")
        self.var_semilla = tk.StringVar(value="2026")
        ttk.Entry(cabecera, textvariable=self.var_semilla, width=8).pack(side="right")
        ttk.Label(cabecera, text="Semilla (datos reproducibles)").pack(side="right", padx=6)

        self.cuaderno = ttk.Notebook(self.raiz)
        self.cuaderno.pack(fill="both", expand=True, padx=8)
        self.pestanas = {}
        for clase in PESTANAS:
            contenedor = ui.Desplazable(self.cuaderno)
            pestana = clase(contenedor.interno, self)
            pestana.marco.pack(fill="both", expand=True, pady=(0, 12))
            self.cuaderno.add(contenedor.externo, text=f"  {clase.titulo}  ")
            self.pestanas[clase.__name__] = pestana

        self.estado = tk.StringVar(value="Listo. Todas las operaciones usan la biblioteca rsa_edu.")
        ttk.Label(self.raiz, textvariable=self.estado, relief="sunken", anchor="w",
                  padding=(8, 3)).pack(fill="x", side="bottom")

    def semilla(self) -> int:
        return leer_entero(self.var_semilla.get(), "la semilla", 0)

    def ejecutar(self) -> None:
        self.raiz.mainloop()

    def cerrar(self) -> None:
        self.raiz.destroy()


def main(argv: list[str] | None = None) -> int:
    try:
        import tkinter  # noqa: F401
    except ImportError:
        print("error: esta instalación de Python no incluye tkinter. En Windows, reinstale "
              "Python desde python.org marcando «tcl/tk and IDLE».", file=sys.stderr)
        return 1
    try:
        app = Aplicacion()
    except Exception as exc:  # p. ej., sin pantalla disponible
        print(f"error: no se pudo abrir la ventana ({exc})", file=sys.stderr)
        return 1
    app.ejecutar()
    return 0
