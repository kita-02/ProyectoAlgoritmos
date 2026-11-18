# Documentación técnica — rsa-edu 0.2.0 (Entrega 2)

Biblioteca educativa de teoría de números y cifrado RSA. Proyecto
«Optimización del pipeline de ejecución para el sistema criptográfico RSA»,
Algoritmos Avanzados 2026-II, UNSAAC, Grupo 6.

Contenido:

1. [Instalación](#1-instalación)
2. [Ejecución rápida](#2-ejecución-rápida)
3. [Estándares RSA que se siguen](#3-estándares-rsa-que-se-siguen)
4. [Módulos](#4-módulos)
5. [Funciones principales y parámetros](#5-funciones-principales-y-parámetros)
6. [Interfaz de línea de comandos](#6-interfaz-de-línea-de-comandos)
7. [Formatos de entrada y salida](#7-formatos-de-entrada-y-salida)
8. [Cómo reproducir las pruebas](#8-cómo-reproducir-las-pruebas)
9. [Cómo reproducir los experimentos](#9-cómo-reproducir-los-experimentos)
10. [Organización de los resultados](#10-organización-de-los-resultados)
11. [Limitaciones conocidas](#11-limitaciones-conocidas)

---

## 1. Instalación

Requisitos: Python 3.10 o superior (probado con 3.10, 3.12 y 3.13 en Linux y
Windows) y Git.

```bash
git clone https://github.com/kita-02/ProyectoAlgoritmos.git
cd ProyectoAlgoritmos
python -m venv .venv
# Windows:  .venv\Scripts\activate        Linux / macOS:  source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

La biblioteca (`src/rsa_edu/`) solo usa la biblioteca estándar. Las
dependencias de `requirements.txt` se usan para:

| Paquete | Uso |
|---|---|
| `pytest`, `pytest-cov` | pruebas y cobertura |
| `hypothesis` | pruebas basadas en propiedades |
| `sympy` | oráculo de referencia en pruebas y experimentos (nunca dentro de la biblioteca) |
| `pandas`, `matplotlib` | tablas y figuras (`scripts/graficar.py`, `scripts/ajuste_complejidad.py`) |
| `gmpy2` (opcional) | prototipo comparativo con aritmética GMP |

Comprobar la instalación:

```bash
python -m rsa_edu --version          # rsa_edu 0.2.0
python -m pytest -q                  # todas las pruebas deben pasar
```

## 2. Ejecución rápida

```bash
python scripts/traza_instancia.py                 # ejemplo manual p=61, q=53, e=17, m=65 paso a paso
python scripts/demo_optimizacion.py --bits 1024   # pipeline base frente a optimizado, mismo resultado
python -m rsa_edu comparar factorizacion 3233     # todas las alternativas sobre la misma instancia
```

## 3. Estándares RSA que se siguen

RSA como algoritmo es el de Rivest, Shamir y Adleman (1977). Lo que tiene
versiones son los estándares que dicen cómo usarlo:

| Parte | Estándar | Qué se toma |
|---|---|---|
| Generación de claves aleatorias | **NIST FIPS 186-5** (2023), apéndice A.1 | e = 65537; p y q de b/2 bits con los dos bits altos en 1; mcd(e, p−1) = mcd(e, q−1) = 1; \|p − q\| > 2^(b/2 − 100); d = e⁻¹ mod λ(n) con d > 2^(b/2) |
| Primitivas de cifrado y descifrado | **PKCS #1 v2.2** (RFC 8017, 2016) | RSAEP c = m^e mod n y RSADP m = c^d mod n; descifrado por TCR con la representación (p, q, dP, dQ, qInv) de la sección 3.2 |
| Relleno | PKCS #1 v2.2, RSAES-OAEP | **pendiente para la Entrega 3**: en la Entrega 2 se usa RSA «de libro de texto» (sin relleno), adecuado para estudiar los algoritmos pero no seguro |

Versiones anteriores de PKCS #1: v1.5 (RFC 2313, relleno hoy vulnerable), v2.0
(RFC 2437, introduce OAEP) y v2.1 (RFC 3447). Las optimizaciones estudiadas
(criba, TCR, ventana) no dependen del relleno: OAEP solo transforma m antes de
la exponenciación.

Las claves manuales (`generar_claves(p, q, e)`, usadas en el ejemplo resuelto
a mano) calculan d con φ(n) para reproducir d = 2753; las aleatorias usan λ(n)
como pide FIPS 186-5. Ambas descifran igual porque λ(n) divide a φ(n).

## 4. Módulos

Arquitectura en capas: cada módulo solo importa de capas inferiores.

| Capa | Módulo | Responsable | Contenido |
|---|---|---|---|
| 1 | `contador.py` | Francesco | `Contador`: multiplicaciones, divisiones, mcd e iteraciones |
| 1 | `aritmetica.py` | Francesco | mcd, Euclides extendido, inverso, exponenciación ingenua, binaria y por ventana |
| 2 | `primalidad.py` | Orlando | división de prueba, Miller-Rabin (aleatorio y determinista), criba, `generar_primo` |
| 2 | `factorizacion.py` | Camila | división de prueba, Pollard Rho (Floyd), Brent, `factorizar` |
| 2 | `ataque.py` | Camila | `romper_clave(n, e)`: factoriza n y recupera d |
| 3 | `rsa.py` | Emmi | claves (manual y FIPS 186-5), cifrar, descifrar, descifrar por TCR, texto en bloques |
| 3 | `pipeline.py` | Emmi | `ConfigPipeline` y `ejecutar_pipeline` (claves → cifrado → descifrado) |
| 3 | `formatos.py` | Emmi | lectura y validación de instancias y claves (JSON) y resultados (CSV) |
| Interfaz | `__main__.py` | Emmi | CLI `python -m rsa_edu` |
| Interfaz | `interfaz/` | Todos | ventana Tkinter: `app.py`, `comun.py`, `componentes.py` (Emmi) y una pestaña por módulo: `pestana_rsa.py` y `pestana_optimizacion.py` (Emmi), `pestana_exponenciacion.py` (Francesco), `pestana_primalidad.py` (Orlando), `pestana_factorizacion.py` (Camila) |

## 5. Funciones principales y parámetros

Todas aceptan un parámetro opcional `cont: Contador | None`; si se pasa, se
cuentan las operaciones; si es `None` no hay costo. Las funciones aleatorias
aceptan `rng: random.Random` para que la ejecución sea reproducible.

| Función | Parámetros | Devuelve | Errores |
|---|---|---|---|
| `exp_modular_rapida(base, exp, mod)` | exp ≥ 0, mod ≥ 1 | base^exp mod mod | `ValueError` |
| `exp_modular_ventana(base, exp, mod, k=None)` | k = ancho de ventana (None → `ventana_optima`) | igual | `ValueError` |
| `division_tentativa(n)` | entero | `bool` exacto | — |
| `miller_rabin(n, rondas=20, rng=None)` | rondas ≥ 1 | `bool` (error ≤ 4^−rondas) | `ValueError` |
| `miller_rabin_determinista(n)` | n < 3,18·10²³ | `bool` exacto | `ValueError` |
| `generar_primo(bits, rng=None, criba=True, dos_bits_altos=False)` | bits ≥ 2 | primo de exactamente `bits` bits | `ValueError` |
| `factorizar(n, metodo="rho", rng=None, max_iter=None)` | metodo ∈ {tentativa, rho, brent} | lista ordenada de factores | `ValueError`, `TypeError`, `RuntimeError` |
| `generar_claves(p, q, e=None)` | primos distintos | `KeyPair` (d con φ) | `ValueError` |
| `generar_claves_aleatorias(bits, e=None, rng=None, criba=True)` | bits par ≥ 16 | `KeyPair` FIPS 186-5 | `ValueError`, `RuntimeError` |
| `cifrar(m, publica, ventana=False)` | 0 ≤ m < n | c | `ValueError` |
| `descifrar(c, privada, ventana=False)` | 0 ≤ c < n | m | `ValueError` |
| `descifrar_crt(c, privada, ventana=False)` | 0 ≤ c < n | m | `ValueError` |
| `ejecutar_pipeline(config, mensajes=None, cantidad=10)` | `ConfigPipeline(bits, e, semilla, criba, crt, ventana, gmpy2)` | `ResultadoPipeline` | `ValueError` |

## 6. Interfaz de línea de comandos

`python -m rsa_edu <subcomando> [opciones]`; código de salida 0 si todo va
bien y 1 ante cualquier error, con un mensaje `error: ...`.

| Subcomando | Ejemplo | Alternativas |
|---|---|---|
| `primo` | `primo 561 --metodo determinista` · `primo --generar 512 --semilla 7` | `--metodo auto\|tentativa\|mr\|determinista`, `--sin-criba` |
| `factorizar` | `factorizar 600851475143 --metodo brent` | `--metodo tentativa\|rho\|brent`, `--max-iter` |
| `claves` | `claves -p 61 -q 53 -e 17 --salida clave.json` · `claves --bits 1024 --salida c.json` | `--sin-criba`, `--semilla`, `--publica` |
| `cifrar` | `cifrar 65 --claves clave.json` · `cifrar --texto "hola" --claves c.json` | `--ventana` |
| `descifrar` | `descifrar 2790 --claves clave.json --crt` | `--crt`, `--ventana` |
| `atacar` | `atacar -n 3233 -e 17` | `--metodo` |
| `comparar` | `comparar descifrado 2790 --claves clave.json` | tareas: `primalidad`, `factorizacion`, `exponenciacion`, `descifrado` |
| `pipeline` | `pipeline --bits 1024 --crt --ventana` | `--sin-criba`, `--crt`, `--ventana`, `--gmpy2` |
| `interfaz` | `interfaz` | abre la interfaz gráfica |

### Interfaz gráfica

`python -m rsa_edu interfaz` (o `python -m rsa_edu.interfaz`) abre una ventana
Tkinter con cinco pestañas que llaman a las mismas funciones de la biblioteca:

| Pestaña | Qué permite hacer |
|---|---|
| RSA | generar claves con p y q o aleatorias (FIPS 186-5), cifrar un número o un texto y descifrarlo directo o por TCR |
| Exponenciación modular | comparar ingenua, binaria y ventana; ver el paso a paso de la binaria |
| Primalidad | comparar división de prueba, Miller-Rabin y MR determinista; generar un primo con y sin criba |
| Factorización y ataque | comparar división de prueba, Rho y Brent; recuperar d a partir de (n, e) |
| Optimización | ejecutar el pipeline base y el optimizado con la misma semilla y comparar cada etapa |

Cada archivo de pestaña separa la **lógica** (funciones puras, probadas en
`tests/test_interfaz_*.py` sin pantalla) de la **ventana**. Las operaciones
largas se ejecutan en un hilo aparte para que la ventana no se congele. La
semilla de la parte superior hace reproducibles los datos aleatorios.

## 7. Formatos de entrada y salida

**Instancias** (`data/instancias/*.json`, `formatos.cargar_instancias`): los
enteros grandes se guardan como texto para no perder precisión.

```json
{"version": 1,
 "meta": {"tipo": "semiprimo_balanceado", "semilla": 2026},
 "instancias": [{"n": "47561", "bits": 16, "p": "199", "q": "239"}]}
```

**Claves** (`formatos.guardar_claves` / `cargar_claves`): al cargar se
comprueba n = p·q, 1 < e < n y e·d ≡ 1 (mod λ(n)); si no, `FormatoInvalido`.

```json
{"version": 1, "tipo": "rsa-edu",
 "publica": {"n": "3233", "e": "17"},
 "privada": {"d": "2753", "p": "61", "q": "53"}}
```

**Configuración de experimentos** (`config/*.json`): `nombre`, `semilla`,
`repeticiones`, `calentamiento`, `instancias` y una sección por experimento
(`E1_primalidad` … `E6_pipeline`) con sus tamaños.

**Resultados** (`resultados/<nombre>/E1.csv` … `E6.csv`), una fila por
alternativa e instancia:

| Columna | Significado |
|---|---|
| `experimento`, `algoritmo`, `etapa`, `instancia`, `bits` | identifican la medición (`etapa` solo en E6) |
| `repeticiones` | ejecuciones cronometradas |
| `ms_mediana`, `ms_min`, `ms_max`, `cv` | tiempo en ms y coeficiente de variación |
| `mult_mod`, `div_mod`, `mcd`, `iteraciones` | operaciones contadas (no dependen del equipo) |
| `kib_pico` | memoria pico medida con `tracemalloc` (KiB) |
| `extra` | dato propio del experimento (`llamadas_mr=…`, `mensajes=…`) |
| `ok` | el resultado coincide con la referencia (sympy, `pow` o el mensaje original) |
| `estable` | todas las repeticiones dieron el mismo resultado |

`metadatos.json` guarda fecha, versión de Python, sistema, procesador, commit,
semilla y hash de la configuración usada.

## 8. Cómo reproducir las pruebas

```bash
python -m pytest                                        # suite completa
python -m pytest --cov=rsa_edu --cov-report=term-missing
python -m pytest tests/test_primalidad.py -k P4         # un grupo concreto
```

| Archivo | Identificadores | Componente |
|---|---|---|
| `test_aritmetica.py` | A1–A8 | aritmética modular y contador |
| `test_primalidad.py` | P1–P11 | primalidad y generación de primos |
| `test_factorizacion.py` | F1–F9 | factorización y ataque |
| `test_rsa.py` | R1–R12 | claves, cifrado, descifrado, TCR, texto |
| `test_formatos.py` | R9 | archivos JSON y CSV |
| `test_propiedades.py` | — | propiedades con Hypothesis |
| `test_integracion.py` | I1–I6 | pipeline, CLI, scripts |
| `test_demo_optimizacion.py` | I7 | base y optimizado dan el mismo resultado |
| `test_experimentos.py` | X1–X6 | formato, corrección y reproducibilidad del benchmark; figuras y ajustes |

La integración continua (`.github/workflows/pruebas.yml`) ejecuta la suite
en Ubuntu y Windows con Python 3.10, 3.12 y 3.13 en cada push.

## 9. Cómo reproducir los experimentos

```bash
# 1. Instancias (ya están en el repositorio; regenerarlas da los mismos archivos)
python scripts/generar_instancias.py

# 2. Piloto: dos corridas y verificación de correctos, reproducibles y coherentes (~15 s)
python scripts/verificar_reproducibilidad.py

# 3. Experimentos preliminares (~3 min) o definitivos (más de 30 min)
python scripts/benchmark.py --config config/preliminar.json
python scripts/benchmark.py --config config/experimentos.json

# 4. Tablas, figuras y comparación con la teoría
python scripts/graficar.py resultados/preliminar
python scripts/ajuste_complejidad.py resultados/preliminar
```

Procedimiento de medición de cada caso (`benchmark.medir`):

1. una ejecución de conteo, no cronometrada, con `Contador` y `tracemalloc`;
   su resultado se verifica contra la referencia;
2. `calentamiento` ejecuciones descartadas;
3. `repeticiones` ejecuciones cronometradas con `time.perf_counter`, sin
   contador y con el recolector de basura desactivado; se guarda la mediana.

Para comparar tiempos entre corridas use el mismo equipo, conectado a la
corriente y sin otros programas pesados abiertos. Los conteos de operaciones
son idénticos en cualquier equipo.

## 10. Organización de los resultados

```
resultados/
├── piloto/
│   ├── corrida_1/  corrida_2/      E1..E6.csv + metadatos.json de cada corrida
│   └── reproducibilidad.md         veredicto: correctos, reproducibles, coherentes
├── preliminar/
│   ├── E1.csv … E6.csv, metadatos.json
│   ├── figuras/                    E1_primalidad.pdf/png … E6_pipeline.pdf/png
│   ├── tablas/                     E1.md/.tex … E6.md/.tex
│   └── ajustes.csv, ajustes.md     teoría frente a mediciones
└── definitivo/                     (misma estructura, para el informe de la Entrega 2)
```

## 11. Limitaciones conocidas

- RSA sin relleno: determinista y maleable; OAEP se agrega en la Entrega 3.
- Las operaciones no son de tiempo constante: no usar con datos reales.
- La división de prueba se vuelve inviable sobre unos 48 bits (cada bit
  multiplica su tiempo por ≈ 1,41) y Pollard Rho / Brent sobre unos 100 bits
  con factores balanceados (≈ 1,19 por bit; en E2, Brent tarda ~35 ms con
  64 bits, lo que proyecta varios segundos con 100 bits).
- Miller-Rabin aleatorio tiene probabilidad de error ≤ 4^−20; bajo
  3,18·10²³ se usa la versión determinista, que es exacta.
- Los tiempos dependen del equipo; por eso también se registran los conteos.
