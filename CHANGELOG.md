# Historial de cambios

## [0.2.0] — Entrega 2

### Interfaz gráfica (pedida por el docente)

**Agregado**
- `src/rsa_edu/interfaz/`: ventana Tkinter con cinco pestañas para usar los
  algoritmos y ver los resultados en tablas y gráficos. Se abre con
  `python -m rsa_edu interfaz`.
  - `comun.py`, `componentes.py`, `app.py`, `pestana_rsa.py`,
    `pestana_optimizacion.py` y subcomando `interfaz` de la CLI. — Emmi
  - `pestana_exponenciacion.py` (comparación y paso a paso de la binaria). — Francesco
  - `pestana_primalidad.py` (pruebas y generación con y sin criba). — Orlando
  - `pestana_factorizacion.py` (métodos de factorización y ataque). — Camila
- Pruebas G1–G6 (`tests/test_interfaz_*.py`): 64 pruebas nuevas, 397 en total.
- Integración continua: en Linux las pruebas de la ventana se ejecutan con
  una pantalla virtual (`xvfb-run`).

### Avances 6 y 7: pruebas, complejidad, diseño experimental y experimentos preliminares

**Agregado**
- `scripts/benchmark.py`: diseño experimental definitivo con seis experimentos
  (E1 primalidad, E2 factorización, E3 exponenciación, E4 descifrado, E5
  generación de primos, E6 pipeline completo base frente a optimizado).
  Mide mediana, mínimo, máximo, coeficiente de variación, operaciones,
  memoria pico y estabilidad; verifica cada resultado contra sympy o `pow`
  y guarda `metadatos.json`. — Emmi
- `config/piloto.json`, `config/preliminar.json`, `config/experimentos.json`
  (definitivo). — Emmi
- `scripts/demo_optimizacion.py` y `tests/test_demo_optimizacion.py` (I7):
  el pipeline base y el optimizado dan la misma clave, los mismos cifrados y
  recuperan los mensajes; muestra la mejora por etapa. — Emmi
- `scripts/verificar_reproducibilidad.py`: experimento piloto con dos
  corridas; comprueba datos correctos, reproducibles y coherentes. — Orlando
- `tests/test_experimentos.py` (X1–X6): formato, corrección y
  reproducibilidad del benchmark, figuras, ajustes y scripts. — Orlando
- `scripts/graficar.py`: figuras (PDF y PNG) y tablas (Markdown y LaTeX). — Francesco
- `scripts/ajuste_complejidad.py`: ajuste por mínimos cuadrados y comparación
  con la complejidad teórica. — Camila
- `resultados/piloto/` y `resultados/preliminar/` con datos, figuras, tablas
  y ajustes. — Orlando y Camila
- `docs/DOCUMENTACION_TECNICA.md`. — Emmi
- `informe/entrega2/`: informe de la Entrega 2 con la estructura de 14
  secciones del informe final (un archivo por sección en `secciones/`). — Francesco
- `docs/BITACORA_GRUPAL.md`: bitácora del grupo por fechas (avances,
  decisiones, cambios y evidencias). — Orlando

**Corregido a partir de los avances anteriores**
- Los archivos JSON, Markdown y LaTeX generados se escriben con fin de línea
  LF también en Windows: regenerar las instancias con la misma semilla da
  archivos idénticos byte a byte en cualquier sistema. — Emmi
- `scripts/traza_instancia.py` ahora incluye el descifrado por TCR (paso 5),
  como se mostró en la presentación del Avance 5. — Emmi
- `scripts/demo_factorizacion.py` compara también Brent. — Camila
- `scripts/demo_primalidad.py` compara también Miller-Rabin determinista. — Orlando
- `scripts/prototipo_gmpy2.py` y `scripts/graficar.py` dejaron de ser
  marcadores «pendiente» y ya funcionan. — Francesco
- El benchmark verificaba E1 con las etiquetas `es_primo` de las instancias,
  que las genera nuestra propia biblioteca (verificación circular). Ahora usa
  `sympy.isprime` y `sympy.factorint` como oráculo externo. — Emmi
- E3 solo usaba exponentes 2^k − 1 (todos los bits en 1, peor caso de la
  binaria). Ahora usa exponentes aleatorios (caso promedio) de 256 a 4096
  bits. — Emmi
- La comparación era solo por etapa; se agregó la comparación del pipeline
  completo (E6). — Emmi
- Los tiempos se medían con el contador activado; ahora las operaciones se
  cuentan en una ejecución aparte y los tiempos se toman sin contador y con el
  recolector de basura desactivado. — Emmi

### Avances 4 y 5: primera y segunda alternativa, integración

- Exponenciación por ventana deslizante y ventana óptima; `Contador`. — Francesco
- Miller-Rabin determinista (12 bases), `es_primo`, criba, `generar_primo`. — Orlando
- Pollard Rho con límite de iteraciones, variante de Brent, `factorizar`
  con pila explícita, `ataque.py`. — Camila
- Claves FIPS 186-5, TCR, texto en bloques, pipeline, formatos, CLI
  (`comparar`, `pipeline`), instancias, benchmark E1–E4 e integración
  continua. — Emmi

## [0.1.0] — Entrega 1

- Prototipo inicial: aritmética modular, división de prueba, Miller-Rabin,
  Pollard Rho y RSA básico con la instancia p = 61, q = 53 resuelta a mano.
