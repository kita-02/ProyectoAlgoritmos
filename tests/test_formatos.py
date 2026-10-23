"""Caso R9: lectura y escritura de instancias, claves y resultados, incluidos
archivos alterados o mal formados.
"""
from __future__ import annotations

import json

import pytest

from rsa_edu.formatos import (FormatoInvalido, cargar_claves, cargar_instancias,
                              escribir_resultados, guardar_claves,
                              guardar_instancias, leer_resultados)


def test_R9_instancias_ida_y_vuelta(tmp_path):
    ruta = tmp_path / "inst.json"
    guardar_instancias(ruta, [{"n": 3233, "p": 53}, {"n": 2 ** 200}], "mixto", {"semilla": 1})
    insts = cargar_instancias(ruta)
    assert [i["n"] for i in insts] == [3233, 2 ** 200]


def test_R9_instancias_del_repositorio():
    from pathlib import Path
    raiz = Path(__file__).resolve().parents[1] / "data" / "instancias"
    for nombre in ("primos.json", "semiprimos.json", "adversos.json"):
        assert isinstance(cargar_instancias(raiz / nombre), list)


def test_R9_claves_ida_y_vuelta(tmp_path, clave_manual, clave_512):
    for kp in (clave_manual, clave_512):
        ruta = tmp_path / "k.json"
        guardar_claves(ruta, kp)
        pub, priv = cargar_claves(ruta)
        assert pub == kp.publica and priv == kp.privada


def test_R9_solo_publica(tmp_path, clave_manual):
    ruta = tmp_path / "pub.json"
    guardar_claves(ruta, clave_manual, solo_publica=True)
    pub, priv = cargar_claves(ruta)
    assert pub == clave_manual.publica and priv is None


@pytest.mark.parametrize("campo,valor", [("d", "2752"), ("p", "59"), ("q", "abc")])
def test_R9_clave_alterada(tmp_path, clave_manual, campo, valor):
    ruta = tmp_path / "k.json"
    guardar_claves(ruta, clave_manual)
    datos = json.loads(ruta.read_text())
    datos["privada"][campo] = valor
    ruta.write_text(json.dumps(datos))
    with pytest.raises(FormatoInvalido):
        cargar_claves(ruta)


@pytest.mark.parametrize("contenido", ["{no es json", "[]", '{"version": 99}',
                                       '{"version": 1, "publica": {"n": "10", "e": "20"}}'])
def test_R9_claves_mal_formadas(tmp_path, contenido):
    ruta = tmp_path / "k.json"
    ruta.write_text(contenido)
    with pytest.raises(FormatoInvalido):
        cargar_claves(ruta)


@pytest.mark.parametrize("contenido", ['{"version": 1}', '{"version": 1, "instancias": {}}',
                                       '{"version": 1, "instancias": [{"m": 3}]}',
                                       '{"version": 1, "instancias": [{"n": "x1"}]}',
                                       '{"version": 1, "instancias": [{"n": -5}]}',
                                       '{"version": 2, "instancias": []}'])
def test_R9_instancias_mal_formadas(tmp_path, contenido):
    ruta = tmp_path / "i.json"
    ruta.write_text(contenido)
    with pytest.raises(FormatoInvalido):
        cargar_instancias(ruta)


def test_R9_archivo_inexistente(tmp_path):
    with pytest.raises(FormatoInvalido):
        cargar_claves(tmp_path / "no.json")
    with pytest.raises(FormatoInvalido):
        leer_resultados(tmp_path / "no.csv")


def test_R9_resultados_csv(tmp_path):
    ruta = tmp_path / "r" / "E1.csv"
    escribir_resultados(ruta, [{"alg": "mr", "ms": 1.5}])
    escribir_resultados(ruta, [{"alg": "td", "ms": 2.0}], anexar=True)
    assert leer_resultados(ruta) == [{"alg": "mr", "ms": "1.5"}, {"alg": "td", "ms": "2.0"}]
    with pytest.raises(ValueError):
        escribir_resultados(ruta, [])
    with pytest.raises(ValueError):
        escribir_resultados(ruta, [{"a": 1}, {"b": 2}])
