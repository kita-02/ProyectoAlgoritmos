# RSA educativo (rsa-edu)

Biblioteca educativa de teoría de números y cifrado **RSA** para la materia
**Algoritmos Avanzados** (2026-II) — Grupo 6. Estado: **Entrega 2**
(Avances 4 a 7: implementación funcional, alternativas comparables,
integración, pruebas automatizadas, análisis de complejidad, diseño
experimental y experimentos preliminares).

Documentación completa: [`docs/DOCUMENTACION_TECNICA.md`](docs/DOCUMENTACION_TECNICA.md) ·
cambios: [`CHANGELOG.md`](CHANGELOG.md) ·
bitácora del grupo: [`docs/BITACORA_GRUPAL.md`](docs/BITACORA_GRUPAL.md) ·
informe: [`informe/entrega2/`](informe/entrega2/).

> **Uso exclusivamente educativo.** Es RSA "de libro de texto": sin relleno
> (OAEP), por lo que **no debe usarse** para proteger información real.

**Estándares:** claves según **NIST FIPS 186-5** (e = 65537, d = e⁻¹ mod λ(n));
primitivas de cifrado y descifrado (incluido el TCR) según **PKCS #1 v2.2**
(RFC 8017). El relleno RSAES-OAEP de PKCS #1 v2.2 se agrega en la Entrega 3.

## ¿Se optimiza el RSA? (demostración en un comando)

```bash
python scripts/demo_optimizacion.py --bits 1024
```

Ejecuta el pipeline completo con los algoritmos base (sin criba, descifrado
directo) y con los optimizados (criba, TCR y ventana) usando la misma semilla,
verifica que ambos dan la misma clave, los mismos cifrados y recuperan todos
los mensajes, y muestra el tiempo y las multiplicaciones de cada etapa.

## Interfaz gráfica

```bash
python -m rsa_edu interfaz        # en Windows: py -m rsa_edu interfaz
```

Abre una ventana con cinco pestañas: **RSA** (generar claves, cifrar y
descifrar de forma directa o con el TCR), **Exponenciación modular**,
**Primalidad**, **Factorización y ataque** y **Optimización** (pipeline base
frente a optimizado). Cada pestaña muestra en tablas el resultado, el tiempo y
las operaciones de cada alternativa, y una línea verde si todas coinciden. Usa
Tkinter, que viene con Python.

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
pytest                                   # 397 pruebas
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
| `test_demo_optimizacion.py` | I7 | pipeline base y optimizado: misma clave, mismos cifrados |
| `test_experimentos.py` | X1–X6 | formato, corrección y reproducibilidad del benchmark; figuras, ajustes y demos |

La integración continua (`.github/workflows/pruebas.yml`) ejecuta la suite en
Linux y Windows con Python 3.10, 3.12 y 3.13 en cada *push*.

## Scripts

```bash
python scripts/traza_instancia.py          # traza paso a paso del pipeline, con TCR (p=61, q=53)
python scripts/demo_primalidad.py 561 2047 # división, Miller-Rabin y MR determinista
python scripts/demo_factorizacion.py 600851475143   # división, Rho y Brent
python scripts/demo_optimizacion.py        # pipeline base frente a optimizado
python scripts/prototipo_gmpy2.py          # binaria, ventana, pow y gmpy2
python scripts/generar_instancias.py       # data/instancias/*.json (semilla 2026)
```

## Experimentos

```bash
python scripts/verificar_reproducibilidad.py                 # piloto: correctos, reproducibles, coherentes
python scripts/benchmark.py --config config/preliminar.json  # E1-E6 -> resultados/preliminar/*.csv
python scripts/graficar.py resultados/preliminar             # figuras/ y tablas/
python scripts/ajuste_complejidad.py resultados/preliminar   # teoría frente a mediciones
python scripts/benchmark.py                                  # diseño definitivo (config/experimentos.json)
```

| Experimento | Primera alternativa | Segunda alternativa |
|---|---|---|
| E1 primalidad | división de prueba | Miller-Rabin / MR determinista |
| E2 factorización | división de prueba | Pollard Rho (Floyd) / Brent |
| E3 exponenciación | binaria | ventana deslizante |
| E4 descifrado | directo | Teorema Chino del Resto |
| E5 generar primos | sin criba | con criba (primos < 2000) |
| E6 pipeline completo | base | optimizado (criba + TCR + ventana) |

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
│   ├── __main__.py        # CLI
│   └── interfaz/          # interfaz gráfica (Tkinter): una pestaña por módulo
├── tests/                 # suite pytest + Hypothesis
├── scripts/               # trazas, demos, instancias, benchmark, gráficos, ajustes
├── data/instancias/       # primos, semiprimos y adversos (JSON)
├── config/                # piloto.json, preliminar.json, experimentos.json (definitivo)
├── resultados/            # piloto/ y preliminar/: CSV, figuras, tablas, ajustes
├── docs/                  # documentación técnica y bitácora grupal
├── .github/workflows/     # integración continua
└── informe/entrega2/      # informe de la Entrega 2 (LaTeX por secciones y PDF)
```

## Integrantes y distribución de módulos

| Integrante | Módulos (Entrega 2) |
|------------|---------------------|
| Francesco Canal Acevedo | `aritmetica.py`, `contador.py`, `test_aritmetica.py` |
| Orlando Clemente Lopez | `primalidad.py`, `test_primalidad.py` |
| Camila Fernández Puente de la Vega | `factorizacion.py`, `ataque.py`, `test_factorizacion.py` |
| Emmi Daniela Huaman Tairo | `rsa.py`, `pipeline.py`, `formatos.py`, `__main__.py`, pruebas de RSA/formatos/integración/propiedades, scripts de instancias y benchmark, CI, README |

Avances 6 y 7: Francesco (`prototipo_gmpy2.py`, `graficar.py`, informe), Orlando
(`verificar_reproducibilidad.py`, `test_experimentos.py`, piloto, bitácora grupal), Camila
(`ajuste_complejidad.py`, demo con Brent, resultados preliminares) y Emmi
(`benchmark.py`, configuraciones, `demo_optimizacion.py`, documentación).

Interfaz gráfica: cada integrante programó la pestaña de su módulo —
Francesco (exponenciación), Orlando (primalidad), Camila (factorización y
ataque) y Emmi (base común, RSA, optimización y ventana principal).

## Próximos pasos (Entrega 3)

- Ejecutar el diseño definitivo (`config/experimentos.json`) y actualizar las
  tablas del informe con esos resultados.
- Relleno RSAES-OAEP (PKCS #1 v2.2) y su costo; comparación con OpenSSL.
- Reflexión individual de aprendizaje e informe final.
