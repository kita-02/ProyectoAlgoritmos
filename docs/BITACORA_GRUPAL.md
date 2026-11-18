# Bitácora grupal — Grupo 6

**Proyecto:** Optimización del criptosistema RSA (biblioteca `rsa_edu`)
**Curso:** Algoritmos Avanzados — UNSAAC, Ingeniería Informática y de Sistemas
**Integrantes:** Emmi Huaman (EH), Francesco Canal (FC), Orlando Clemente (OC), Camila Fernández (CF)

Registro por fechas de los avances del grupo, las decisiones tomadas, los
cambios y los problemas encontrados. Cada entrada indica la evidencia que la
respalda (commit, archivo o informe). El resumen de esta bitácora está en el
Anexo C del informe (`informe/entrega2/`).

---

## 29/09/2026 — Inicio del proyecto y estructura del repositorio

**Avance**
- Se crea el repositorio en GitHub y la estructura del paquete `rsa_edu`
  (`src/`, `scripts/`, `tests/`, `data/`, `informe/`). — EH

**Decisiones**
- Lenguaje: Python, porque su `int` es de precisión arbitraria y permite
  implementar los algoritmos sin depender de bibliotecas de enteros grandes.
- El código de la biblioteca va en `src/rsa_edu/`; los scripts de demostración
  y medición en `scripts/`; las pruebas en `tests/`.
- Un responsable por capa: aritmética (FC), primalidad (OC), factorización
  (CF), RSA, integración e infraestructura (EH).

**Evidencia:** commit `6e6a1d0`.

---

## 06/10/2026 — Prototipo de la Entrega 1

**Avance**
- Aritmética modular básica: `mcd`, `euclides_extendido`, `inverso_modular`,
  exponenciación ingenua y binaria. — FC
- Primalidad: división tentativa y Miller–Rabin. — OC
- Factorización: división tentativa y Pollard Rho (Floyd). — CF
- Pipeline RSA básico (generar claves, cifrar, descifrar) y
  `traza_instancia.py`. — EH

**Decisiones**
- Arquitectura en capas: `aritmetica` → `primalidad` → `factorizacion` /
  `rsa` → `pipeline`. Ninguna capa importa una superior.
- `__init__.py` no reexporta funciones: cada módulo se importa por su nombre.
- Los enteros grandes se guardan como texto en JSON (JSON no tiene enteros
  de precisión arbitraria en todos los lectores).
- Un commit por capa y por integrante, para que la autoría sea verificable.

**Problemas y soluciones**
- La carpeta `informe/` se subió y retiró varias veces; se decidió dejarla
  vacía hasta tener el informe definitivo (commits `56c0770`, `52bf50a`,
  `6807716`).

**Evidencia:** commits `019623e`, `e4bec8d`, `2d35c0b`, `6a05a21`, `faa26b0`, `edcbe25`.

---

## Octubre de 2026 — Entrega 1 (informe)

**Avance**
- Informe de la Entrega 1: formulación del problema, fundamentos, evaluación
  del stack, diseño algorítmico, ejemplo manual ($p = 61$, $q = 53$),
  plan de pruebas, plan de aprendizaje y prototipo.

**Decisiones**
- Se compara, en cada etapa, una alternativa **base** con una **optimizada**,
  ambas implementadas por el grupo:

  | Etapa | Base | Optimizada |
  |---|---|---|
  | Exponenciación | binaria | ventana deslizante |
  | Primalidad | división tentativa | Miller–Rabin / MR determinista |
  | Generación de primos | sin criba | con criba (< 2000) |
  | Descifrado | directo | TCR (Garner) |
  | Factorización | división tentativa | Rho (Floyd) / Brent |

- `gmpy2` queda solo como tecnología **opcional** (matriz de decisión
  ponderada: `int` nativo 4,40; `gmpy2` 3,90; `python-flint` 2,95).
- SymPy se usa como **oráculo** en pruebas y experimentos, nunca dentro de `src/`.

**Evidencia:** informe de la Entrega 1.

---

## 23/10/2026 — Segunda alternativa de cada etapa e integración

**Avance**
- Exponenciación por ventana deslizante, ventana óptima y `Contador` de
  operaciones; pruebas A1–A8. — FC
- Miller–Rabin determinista (12 bases), `es_primo`, criba de Eratóstenes,
  `pasa_criba` y `generar_primo`; pruebas P1–P11. — OC
- Pollard Rho con límite de iteraciones, variante de Brent, `factorizar`
  con pila explícita y `ataque.py`; pruebas F1–F9. — CF
- Claves según FIPS 186-5, descifrado por TCR, texto en bloques, pipeline
  configurable, formatos, CLI (`comparar`, `pipeline`), instancias,
  benchmark E1–E4 e integración continua con GitHub Actions. — EH

**Decisiones**
- El exponente privado se calcula con $\lambda(n) = \mathrm{mcm}(p-1, q-1)$
  y $e = 65537$, como pide FIPS 186-5.
- Cifrado y descifrado siguen las primitivas RSAEP/RSADP de PKCS #1 v2.2,
  incluida la variante con TCR.
- Las bases aleatorias de Miller–Rabin usan un generador aparte del de los
  candidatos, para que la secuencia de primos no dependa del número de rondas.
- Pollard Rho recibe `max_iter` para no quedarse en ciclo infinito.
- `factorizar` usa una pila explícita de cofactores en lugar de recursión.
- El `Contador` es opcional: si no se pasa, no hay costo extra.
- `generar_primo` se mueve de `rsa.py` a `primalidad.py`.
- CI en Ubuntu y Windows con Python 3.10, 3.12 y 3.13.

**Evidencia:** commits `0f1f299`, `134881e`, `9075811`, `00380c9`, `dba75ad`, `f8b1388`, `002467a`.

---

## Octubre de 2026 — Presentación de los avances de implementación

**Avance**
- Se presentan la primera y la segunda alternativa de cada etapa y la
  integración (pipeline y CLI), con instancias pedidas por el docente.

**Evidencia:** diapositivas de los avances.

---

## 05/11/2026 — Revisión del repositorio

**Avance**
- Se compara lo que está en GitHub con lo que se mostró en las presentaciones.

**Cambios detectados y corregidos**
- `traza_instancia.py` no mostraba el descifrado por TCR → se agrega el paso 5. — EH
- `demo_factorizacion.py` no comparaba Brent → se agrega. — CF
- `demo_primalidad.py` no comparaba MR determinista → se agrega. — OC
- `prototipo_gmpy2.py` y `graficar.py` eran marcadores «pendiente» → se
  implementan. — FC

**Evidencia:** `CHANGELOG.md` (sección «Corregido a partir de los avances anteriores»).

---

## 06/11/2026 — Pruebas, complejidad, diseño experimental y experimentos preliminares

**Avance**
- Diseño experimental definitivo E1–E6 en `benchmark.py`, configuraciones
  piloto, preliminar y definitiva, y `demo_optimizacion.py` con su prueba I7. — EH
- Prototipo con `gmpy2` y generación de figuras y tablas. — FC
- Ajuste de complejidad teoría vs práctica (`ajuste_complejidad.py`). — CF
- Piloto de reproducibilidad (`verificar_reproducibilidad.py`) y pruebas
  X1–X6 del procedimiento experimental. — OC
- Corrida preliminar: 287 filas, 0 fallas, 208 s; 19 de 19 ajustes
  coinciden con la teoría. — CF
- Documentación técnica, README y CHANGELOG. — EH

**Decisiones y cambios**
- El benchmark verificaba E1 con etiquetas generadas por nuestra propia
  biblioteca (verificación circular) → ahora usa `sympy.isprime` y
  `sympy.factorint` como oráculo externo.
- E3 usaba solo exponentes $2^k - 1$ (peor caso de la binaria) → ahora usa
  exponentes aleatorios (caso promedio).
- Se agrega E6: pipeline completo base frente a optimizado, para medir la
  mejora total y no solo por etapa.
- Las operaciones se cuentan en una ejecución aparte; los tiempos se miden
  sin contador, con calentamiento previo y con el recolector de basura
  desactivado.
- `tracemalloc` solo en la ejecución de conteo (hace lenta la ejecución).
- Semilla 2026 en todos los experimentos y pruebas.
- Hypothesis con `deadline=None` en las pruebas con enteros grandes.

**Resultados preliminares clave**
- E1: Miller–Rabin 70,7× más rápido que la división a 40 bits.
- E2: Brent hasta 3,7× más rápido que Rho (Floyd).
- E3: ventana ahorra 20,6 %–23,6 % de multiplicaciones.
- E4: TCR 2,3× / 2,6× / 3,3× (512 / 1024 / 2048 bits).
- E5: la criba evita el 82,8 % de las llamadas a Miller–Rabin (teoría 85,3 %).
- E6: pipeline completo 3,13× / 4,07× / 5,78× más rápido (512 / 1024 / 2048 bits).

**Evidencia:** commits 1 a 5 y 11 del paquete de la Entrega 2; `resultados/`.

---

## 06/11/2026 — Demostración al docente: algoritmos y pruebas automatizadas

**Avance**
- Se muestran al docente los algoritmos funcionando, la batería de pruebas
  (333 pruebas, 97 % de cobertura), los tipos de prueba (unitarias,
  parametrizadas, por propiedades, de integración, de equivalencia y de
  reproducibilidad) y el uso de semillas fijas.

**Evidencia:** guía de comandos del proyecto.

---

## 17/11/2026 — Entrega 2

**Avance**
- Informe de la Entrega 2 con la estructura de 14 secciones del informe
  final. — FC
- Esta bitácora grupal. — OC
- Guion de comandos para la presentación y explicación de cada salida.

**Decisiones**
- El informe se organiza por temas (no por avances); el resumen y la
  introducción se redactan solo en párrafos. Se irá completando hasta la
  Entrega 3.
- Las bitácoras individuales no se incluyen; se mantiene esta bitácora grupal.

**Evidencia:** commits 12 y 13 del paquete de la Entrega 2.

---

## 18/11/2026 — Interfaz gráfica

**Avance**
- El docente pide una interfaz para manejar los algoritmos y ver los
  resultados de forma familiar. Se agrega una ventana con cinco pestañas:
  - base común (lectura de entradas, tablas, tareas en segundo plano),
    pestañas RSA y Optimización y ventana principal. — EH
  - pestaña de exponenciación modular, con el paso a paso de la binaria. — FC
  - pestaña de primalidad y generación de primos con y sin criba. — OC
  - pestaña de factorización y ataque por factorización. — CF
- 64 pruebas nuevas (G1–G6); la suite pasa a 397 pruebas.

**Decisiones**
- Tkinter, porque viene con Python y no requiere instalar nada más.
- Cada integrante programa la pestaña de su módulo.
- En cada pestaña la lógica se separa de la ventana, así se prueba sin
  pantalla; la ventana completa se prueba con una pantalla virtual en la
  integración continua.
- Las operaciones largas (claves de 2048 bits) se ejecutan en un hilo aparte
  para que la ventana no se congele.

**Evidencia:** commits 6 a 10 del paquete de la Entrega 2.

---

## Próximos pasos (Entrega 3)

- Relleno OAEP (PKCS #1 v2.2) y su costo.
- Corrida definitiva (`config/experimentos.json`: 5 repeticiones, claves
  hasta 4096 bits).
- Comparación con OpenSSL como referencia externa.
- Reflexión individual de aprendizaje en el informe.
- Evidencias de la Entrega 3 y de la defensa.
