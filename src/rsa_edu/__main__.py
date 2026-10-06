"""Punto de entrada: python -m rsa_edu  (con src/ en el PYTHONPATH).

Entrega 1: solo indica cómo ejecutar el prototipo.
Pendiente para la Entrega 2: interfaz de línea de comandos completa
(subcomandos primo, factorizar, claves, cifrar, descifrar).
"""
from . import __version__

AYUDA = f"""rsa_edu {__version__} - prototipo mínimo (Entrega 1)

Ejecute desde la raíz del repositorio:
  python scripts/traza_instancia.py            pipeline RSA completo (p=61, q=53, e=17, m=65)
  python scripts/demo_primalidad.py            división de prueba vs. Miller-Rabin
  python scripts/demo_factorizacion.py         división de prueba vs. Pollard Rho

Cada script acepta una instancia nueva por línea de comandos (use --help).
"""

if __name__ == "__main__":
    print(AYUDA)
