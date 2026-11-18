"""G6 - la ventana completa: se abre, cada botón funciona y muestra el resultado.

Necesita tkinter y una pantalla; si no hay, las pruebas se omiten (en la
integración continua de Linux se ejecutan con una pantalla virtual, xvfb).
"""
from __future__ import annotations

import pytest

from rsa_edu.__main__ import construir_parser

tkinter = pytest.importorskip("tkinter")


@pytest.fixture(scope="module")
def app():
    from rsa_edu.interfaz import componentes as ui
    from rsa_edu.interfaz.app import Aplicacion
    try:
        aplicacion = Aplicacion(visible=False)
    except tkinter.TclError as exc:
        pytest.skip(f"sin pantalla: {exc}")
    ui.SINCRONO = True
    yield aplicacion
    ui.SINCRONO = False
    aplicacion.cerrar()


def test_G6_cinco_pestanas(app):
    assert len(app.pestanas) == 5
    assert app.cuaderno.index("end") == 5
    assert app.semilla() == 2026


def test_G6_rsa(app):
    p = app.pestanas["PestanaRSA"]
    p.generar()
    p.mensaje.set("65")
    p.cifrar()
    assert p.cripto.get() == "2790"
    p.metodo.set("tcr")
    p.descifrar()
    assert p.recuperado.get() == "65" and p.veredicto.texto.startswith("✓")
    p.comparar()
    assert len(p.tabla.filas()) == 2


def test_G6_rsa_texto_con_claves_aleatorias(app):
    p = app.pestanas["PestanaRSA"]
    p.modo.set("aleatoria")
    p.bits.set("512")
    p.generar()
    p.es_texto.set(True)
    p.mensaje.set("Hola, profesor")
    p.cifrar()
    p.descifrar()
    assert p.recuperado.get() == "Hola, profesor"
    p.modo.set("manual")


def test_G6_exponenciacion(app):
    p = app.pestanas["PestanaExponenciacion"]
    p.ejemplo()
    p.ejecutar()
    assert [f[1] for f in p.tabla.filas()] == ["2790"] * 3
    assert p.veredicto.texto.startswith("✓")
    p.ver_traza()
    assert len(p.traza.filas()) == 5
    p.bits.set("256")
    p.generar()
    p.ejecutar()
    assert len(p.tabla.filas()) == 2


def test_G6_primalidad(app):
    p = app.pestanas["PestanaPrimalidad"]
    p.n.set("561")
    p.ejecutar()
    assert "COMPUESTO" in p.veredicto.texto
    p.bits.set("128")
    p.generar()
    assert "mismo primo" in p.veredicto_gen.texto


def test_G6_factorizacion_y_ataque(app):
    p = app.pestanas["PestanaFactorizacion"]
    p.bits.set("32")
    p.generar()
    p.ejecutar()
    assert p.veredicto.texto.startswith("✓") and len(p.tabla.filas()) == 3
    p.ejecutar_ataque()
    assert "d = e⁻¹ mod φ(n) = 2753" in p.texto_ataque()


def test_G6_optimizacion(app):
    p = app.pestanas["PestanaOptimizacion"]
    p.bits.set("256")
    p.mensajes.set("3")
    p.repeticiones.set("1")
    p.ejecutar()
    assert len(p.etiquetas) == 5 and len(p.tabla.filas()) == 4
    assert "veces más rápido" in p.veredicto.texto


def test_G6_errores_se_informan(app):
    p = app.pestanas["PestanaPrimalidad"]
    p.n.set("hola")
    with pytest.raises(ValueError):           # en modo prueba no se abre el diálogo
        p.ejecutar()


def test_G6_tarea_en_segundo_plano_no_congela_la_ventana(app):
    import time

    from rsa_edu.interfaz import componentes as ui
    p = app.pestanas["PestanaPrimalidad"]
    p.n.set("2047")
    p.tabla.limpiar()
    ui.SINCRONO = False
    try:
        p.ejecutar()
        limite = time.time() + 10
        while not p.tabla.filas() and time.time() < limite:
            app.raiz.update()
            time.sleep(0.02)
    finally:
        ui.SINCRONO = True
    assert len(p.tabla.filas()) == 3 and app.estado.get() == "Listo."


def test_G6_subcomando_cli():
    args = construir_parser().parse_args(["interfaz"])
    assert args.func.__name__ == "cmd_interfaz"
