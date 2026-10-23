"""Lectura/escritura de instancias (JSON), claves (JSON) y resultados (CSV).

Todos los lectores VALIDAN lo que leen y lanzan FormatoInvalido (subclase de
ValueError) con un mensaje claro si el archivo está mal formado o alterado.

Diseño: informe/entrega1.tex, sección 7.5 (Formato de los archivos).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

from .rsa import ClavePrivada, ClavePublica, KeyPair, lambda_carmichael

VERSION = 1
TIPOS_INSTANCIA = ("primo", "compuesto", "semiprimo_balanceado",
                   "carmichael / pseudoprimo_fuerte", "mixto")


class FormatoInvalido(ValueError):
    """El archivo no tiene el formato esperado o fue alterado."""


def _leer_json(ruta: str | Path) -> Any:
    ruta = Path(ruta)
    if not ruta.is_file():
        raise FormatoInvalido(f"no existe el archivo {ruta}")
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise FormatoInvalido(f"{ruta}: JSON mal formado ({exc})") from exc


def _escribir_json(ruta: str | Path, datos: Any) -> None:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _entero(valor: Any, campo: str) -> int:
    # Se aceptan enteros o cadenas decimales (JSON no limita el tamaño, pero
    # algunas herramientas sí, por eso los números grandes se guardan como str).
    if isinstance(valor, bool):
        raise FormatoInvalido(f"campo '{campo}': se esperaba un entero")
    if isinstance(valor, int):
        return valor
    if isinstance(valor, str) and valor.strip().lstrip("-").isdigit():
        return int(valor)
    raise FormatoInvalido(f"campo '{campo}': se esperaba un entero, se obtuvo {valor!r}")


# ---------------------------------------------------------------------------
# Instancias
# ---------------------------------------------------------------------------
def guardar_instancias(ruta: str | Path, instancias: Iterable[dict],
                       tipo: str = "mixto", meta: dict | None = None) -> None:
    """Cada instancia es un dict con al menos 'n' (int); se guarda n como str."""
    lista = []
    for i, inst in enumerate(instancias):
        if "n" not in inst:
            raise FormatoInvalido(f"instancia {i} sin campo 'n'")
        fila = dict(inst)
        fila["n"] = str(_entero(inst["n"], "n"))
        lista.append(fila)
    datos = {"version": VERSION, "meta": {"tipo": tipo, **(meta or {})}, "instancias": lista}
    _escribir_json(ruta, datos)


def cargar_instancias(ruta: str | Path) -> list[dict]:
    datos = _leer_json(ruta)
    if not isinstance(datos, dict) or "instancias" not in datos:
        raise FormatoInvalido(f"{ruta}: falta la clave 'instancias'")
    if datos.get("version") != VERSION:
        raise FormatoInvalido(f"{ruta}: versión de formato no soportada: {datos.get('version')!r}")
    if not isinstance(datos["instancias"], list):
        raise FormatoInvalido(f"{ruta}: 'instancias' debe ser una lista")
    salida = []
    for i, inst in enumerate(datos["instancias"]):
        if not isinstance(inst, dict) or "n" not in inst:
            raise FormatoInvalido(f"{ruta}: instancia {i} sin campo 'n'")
        fila = dict(inst)
        fila["n"] = _entero(inst["n"], f"instancias[{i}].n")
        if fila["n"] < 0:
            raise FormatoInvalido(f"{ruta}: instancia {i} con n negativo")
        salida.append(fila)
    return salida


# ---------------------------------------------------------------------------
# Claves
# ---------------------------------------------------------------------------
def guardar_claves(ruta: str | Path, claves: KeyPair, solo_publica: bool = False) -> None:
    pub, priv = claves.publica, claves.privada
    datos: dict[str, Any] = {"version": VERSION, "tipo": "rsa-edu",
                             "publica": {"n": str(pub.n), "e": str(pub.e)}}
    if not solo_publica:
        datos["privada"] = {"d": str(priv.d), "p": str(priv.p), "q": str(priv.q)}
    _escribir_json(ruta, datos)


def cargar_claves(ruta: str | Path) -> tuple[ClavePublica, ClavePrivada | None]:
    """Devuelve (publica, privada); privada es None si el archivo solo tiene la pública.

    Comprueba la consistencia: n = p*q, 1 < e < n y e*d = 1 (mod lambda(n)).
    """
    datos = _leer_json(ruta)
    if not isinstance(datos, dict) or datos.get("version") != VERSION:
        raise FormatoInvalido(f"{ruta}: no es un archivo de claves rsa-edu (versión {VERSION})")
    pub_d = datos.get("publica")
    if not isinstance(pub_d, dict):
        raise FormatoInvalido(f"{ruta}: falta la clave pública")
    n = _entero(pub_d.get("n"), "publica.n")
    e = _entero(pub_d.get("e"), "publica.e")
    if n < 6 or not (1 < e < n):
        raise FormatoInvalido(f"{ruta}: valores de clave pública inválidos")
    publica = ClavePublica(n, e)

    priv_d = datos.get("privada")
    if priv_d is None:
        return publica, None
    if not isinstance(priv_d, dict):
        raise FormatoInvalido(f"{ruta}: la clave privada debe ser un objeto")
    d = _entero(priv_d.get("d"), "privada.d")
    p = _entero(priv_d.get("p"), "privada.p")
    q = _entero(priv_d.get("q"), "privada.q")
    if p * q != n:
        raise FormatoInvalido(f"{ruta}: clave alterada (p*q != n)")
    if p < 2 or q < 2 or (e * d - 1) % lambda_carmichael(p, q) != 0:
        raise FormatoInvalido(f"{ruta}: clave alterada (e*d no es 1 mod lambda(n))")
    return publica, ClavePrivada(n, d, p, q)


# ---------------------------------------------------------------------------
# Resultados
# ---------------------------------------------------------------------------
def escribir_resultados(ruta: str | Path, filas: list[dict], anexar: bool = False) -> None:
    """Escribe una tabla de resultados en CSV (columnas = claves de la 1.a fila)."""
    if not filas:
        raise ValueError("no hay filas que escribir")
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    columnas = list(filas[0].keys())
    nuevo = not (anexar and ruta.exists())
    with ruta.open("a" if anexar else "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columnas)
        if nuevo:
            w.writeheader()
        for fila in filas:
            if set(fila) != set(columnas):
                raise ValueError("todas las filas deben tener las mismas columnas")
            w.writerow(fila)


def leer_resultados(ruta: str | Path) -> list[dict]:
    ruta = Path(ruta)
    if not ruta.is_file():
        raise FormatoInvalido(f"no existe el archivo {ruta}")
    with ruta.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
