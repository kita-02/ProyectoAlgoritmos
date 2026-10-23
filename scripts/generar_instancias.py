"""Generador de conjuntos de instancias reproducibles (semilla fija).

Uso (desde la raíz del repositorio):
    python scripts/generar_instancias.py                 # semilla 2026
    python scripts/generar_instancias.py --semilla 7 --salida data/instancias

Escribe data/instancias/{primos,semiprimos,adversos}.json con el formato de
rsa_edu.formatos (se leen con cargar_instancias).
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from rsa_edu.formatos import guardar_instancias  # noqa: E402
from rsa_edu.primalidad import generar_primo  # noqa: E402

# Números de Carmichael y pseudoprimos fuertes conocidos (casos adversos)
CARMICHAEL = [561, 1105, 1729, 2465, 2821, 6601, 8911, 41041, 825265, 321197185]
PSEUDOPRIMOS_FUERTES = [
    (2047, "spsp(2)"), (1373653, "spsp(2,3)"), (25326001, "spsp(2,3,5)"),
    (3215031751, "spsp(2,3,5,7)"), (2152302898747, "spsp(2..11)"),
    (3474749660383, "spsp(2..13)"), (341550071728321, "spsp(2..17)"),
    (3825123056546413051, "spsp(2..23)"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--semilla", type=int, default=2026)
    ap.add_argument("--salida", default=str(RAIZ / "data" / "instancias"))
    ap.add_argument("--por-tamano", type=int, default=3, dest="por_tamano")
    a = ap.parse_args()

    rng = random.Random(a.semilla)
    meta = {"generador": f"scripts/generar_instancias.py --semilla {a.semilla}",
            "semilla": a.semilla}
    salida = Path(a.salida)

    primos = [{"n": generar_primo(b, rng), "bits": b, "es_primo": True}
              for b in (8, 16, 24, 32, 40, 48, 64, 128, 256, 512)
              for _ in range(a.por_tamano)]
    guardar_instancias(salida / "primos.json", primos, "primo", meta)

    semiprimos = []
    for b in (16, 20, 24, 28, 32, 36, 40, 48, 56, 64):
        for _ in range(a.por_tamano):
            while True:
                p = generar_primo(b // 2, rng)
                q = generar_primo(b - b // 2, rng)
                if p != q:
                    break
            p, q = sorted((p, q))
            semiprimos.append({"n": p * q, "bits": (p * q).bit_length(),
                               "p": str(p), "q": str(q)})
    guardar_instancias(salida / "semiprimos.json", semiprimos, "semiprimo_balanceado", meta)

    adversos = [{"n": n, "clase": "carmichael", "es_primo": False} for n in CARMICHAEL]
    adversos += [{"n": n, "clase": c, "es_primo": False} for n, c in PSEUDOPRIMOS_FUERTES]
    guardar_instancias(salida / "adversos.json", adversos,
                       "carmichael / pseudoprimo_fuerte", meta)

    print(f"{len(primos)} primos, {len(semiprimos)} semiprimos y {len(adversos)} "
          f"adversos escritos en {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
