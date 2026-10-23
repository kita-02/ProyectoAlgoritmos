# RSA educativo (rsa-edu)

Biblioteca educativa de teoría de números y cifrado **RSA** para la materia
**Algoritmos Avanzados** (2026-II) — Grupo 6. Estado: **Entrega 2**
(Avances 4 y 5: implementación funcional, alternativas comparables,
integración y pruebas automatizadas).

> **Uso exclusivamente educativo.** Es RSA "de libro de texto": sin relleno
> (OAEP), por lo que **no debe usarse** para proteger información real.

## Requisitos

- Python **3.10** o superior (probado en 3.10, 3.12 y 3.13; Linux y Windows).
- La biblioteca solo usa la biblioteca estándar. Las pruebas usan `pytest`,
  `hypothesis` y `sympy` (como oráculo); `gmpy2` es opcional.

## Instalación

```bash
git clone https://github.com/kita-02/ProyectoAlgoritmos.git
cd ProyectoAlgoritmos
python -m venv .venv
# Windows:  .venv\Scripts\activate     Linux/Mac:  source .venv/bin/activate
pip install -r requirements.txt
pip install -e .          # permite ejecutar "python -m rsa_edu" desde cualquier carpeta
```

## Interfaz de línea de comandos

Todos los subcomandos devuelven código **0** si terminan bien y **1** ante
cualquier error (con un mensaje claro). Las opciones aceptan uno o dos guiones
(`-claves` o `--claves`). Use `python -m rsa_edu <subcomando> --help`.

| Subcomando | Qué hace | Alternativas seleccionables |
|------------|----------|-----------------------------|
| `primo N` / `primo --generar BITS` | test de primalidad / genera un primo | `--metodo auto\|tentativa\|mr\|determinista`, `--sin-criba` |
| `factorizar N` | factorización completa | `--metodo tentativa\|rho\|brent` |
| `claves -p P -q Q [-e E]` / `claves --bits B` | par de claves (manual o FIPS 186-5) | `--sin-criba`, `--semilla` |
| `cifrar M --claves F` / `cifrar --texto "..."` | cifrado de entero o texto en bloques | `--ventana` |
| `descifrar C --claves F` / `descifrar --texto c1,c2` | descifrado | `--crt`, `--ventana` |
| `atacar -n N -e E` | factoriza n y reconstruye d | `--metodo` |
| `comparar TAREA ENTRADA` | ejecuta **todas las alternativas** sobre la misma instancia, mide tiempo y operaciones y verifica que coincidan | tareas: `primalidad`, `factorizacion`, `exponenciacion`, `descifrado` |
| `pipeline --bits B` | claves → cifrado → descifrado con métricas | `--crt --ventana --sin-criba --gmpy2` |

### Demostración (instancia resuelta a mano: p = 61, q = 53, e = 17, m = 65)

```bash
python -m rsa_edu claves -p 61 -q 53 -e 17 -salida clave.json   # n = 3233, d = 2753
python -m rsa_edu cifrar 65 -claves clave.json                    # -> 2790
python -m rsa_edu descifrar 2790 -claves clave.json               # -> 65
python -m rsa_edu descifrar 2790 -claves clave.json -crt          # -> 65 (TCR)
python -m rsa_edu atacar -n 3233 -e 17                            # -> n = 53 × 61, d = 2753
```

### Las dos alternativas sobre la misma instancia (Avance 5)

```bash
python -m rsa_edu comparar primalidad 561                 # Carmichael: todas dicen COMPUESTO
python -m rsa_edu comparar factorizacion 600851475143     # tentativa, rho y brent
python -m rsa_edu comparar exponenciacion 100000 --base 7 # ingenua, rápida y ventana
python -m rsa_edu comparar descifrado 2790 --claves clave.json   # normal vs TCR
python -m rsa_edu pipeline --bits 1024 --crt --ventana
```

Entradas inválidas (deben dar error y código 1):

```bash
python -m rsa_edu claves -p 61 -q 51            # q no es primo
python -m rsa_edu cifrar 5000 -claves clave.json  # m >= n
python -m rsa_edu atacar -n 49 -e 5             # n no es producto de dos primos distintos
```

## Pruebas automatizadas

```bash
pytest                                   # ~316 pruebas
pytest --cov=rsa_edu --cov-report=term-missing
```

| Archivo | Casos | Contenido |
|---------|-------|-----------|
| `test_aritmetica.py` | A1–A8 | mcd, Bézout, inverso, exp. ingenua/rápida/ventana (k = 1..8), cotas del contador |
| `test_primalidad.py` | P1–P11 | barrido exhaustivo [0, 20000] vs. sympy, Carmichael, pseudoprimos fuertes, cota 1/4, criba, `generar_primo` |
| `test_factorizacion.py` | F1–F9 | oráculo sympy, comparación cruzada de los 3 métodos, límites, Brent, `max_iter`, ataque |
| `test_rsa.py` | R1–R12 | ejemplo manual, ida y vuelta 16–2048 bits, FIPS 186-5, λ, TCR, texto, entradas inválidas |
| `test_formatos.py` | R9 | archivos JSON/CSV alterados o mal formados |
| `test_propiedades.py` | — | Hypothesis: Bézout, inverso, exponenciaciones, primalidad, factorización, RSA |
| `test_integracion.py` | I1–I6 | 6 configuraciones del pipeline (misma clave), demo de la CLI, entradas inválidas, scripts |

La integración continua (`.github/workflows/pruebas.yml`) ejecuta la suite en
Linux y Windows con Python 3.10, 3.12 y 3.13 en cada *push*.

## Scripts

```bash
python scripts/traza_instancia.py          # traza paso a paso del pipeline (p=61, q=53)
python scripts/demo_primalidad.py 561 2047
python scripts/demo_factorizacion.py 600851475143
python scripts/generar_instancias.py       # data/instancias/*.json (semilla 2026)
python scripts/benchmark.py                # experimentos preliminares E1-E4 -> resultados/*.csv
```

## Estructura del repositorio

```
├── src/rsa_edu/
│   ├── contador.py        # Contador de operaciones (mult_mod, div_mod, mcd, iteraciones)
│   ├── aritmetica.py      # mcd, Bézout, inverso, exp. ingenua / rápida / ventana deslizante
│   ├── primalidad.py      # tentativa, Miller-Rabin (aleatorio y determinista), criba, generar_primo
│   ├── factorizacion.py   # tentativa, Pollard Rho (Floyd) y Pollard-Rho-Brent
│   ├── ataque.py          # romper_clave(n, e)
│   ├── rsa.py             # claves (manual y FIPS 186-5), cifrar/descifrar, TCR, texto
│   ├── pipeline.py        # ConfigPipeline / ejecutar_pipeline
│   ├── formatos.py        # instancias y claves (JSON), resultados (CSV) con validación
│   └── __main__.py        # CLI
├── tests/                 # suite pytest + Hypothesis
├── scripts/               # trazas, demos, generación de instancias, benchmark
├── data/instancias/       # primos, semiprimos y adversos (JSON)
├── config/                # configuración de experimentos
├── .github/workflows/     # integración continua
└── informe/
```

## Integrantes y distribución de módulos

| Integrante | Módulos (Entrega 2) |
|------------|---------------------|
| Francesco Canal Acevedo | `aritmetica.py`, `contador.py`, `test_aritmetica.py` |
| Orlando Clemente Lopez | `primalidad.py`, `test_primalidad.py` |
| Camila Fernández Puente de la Vega | `factorizacion.py`, `ataque.py`, `test_factorizacion.py` |
| Emmi Daniela Huaman Tairo | `rsa.py`, `pipeline.py`, `formatos.py`, `__main__.py`, pruebas de RSA/formatos/integración/propiedades, scripts de instancias y benchmark, CI, README |

## Pendiente (Entrega 3)

Gráficos de los experimentos (`scripts/graficar.py`), análisis estadístico de
E1–E4 a mayor escala, prototipo comparativo con `gmpy2` y el informe final.
