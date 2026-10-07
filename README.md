# RSA educativo (rsa-edu)

Prototipo mínimo viable del cifrado **RSA** para la materia **Algoritmos Avanzados**
(UNSAAC, 2026-II) — Grupo 6, Entrega 1.

> **Uso exclusivamente educativo.** Es RSA "de libro de texto": sin relleno
> (padding), por lo que **no debe usarse** para proteger información real.

## Requisitos

- Python **3.8** o superior.
- Solo la biblioteca estándar: en la Entrega 1 **no hay dependencias que instalar**.

## Instalación

```bash
git clone https://github.com/kita-02/ProyectoAlgoritmos.git
cd ProyectoAlgoritmos
```

## Ejecución

### 1. Traza completa del pipeline RSA (instancia conocida: p = 61, q = 53, e = 17, m = 65)

```bash
python scripts/traza_instancia.py
```

Muestra paso a paso la primalidad de p y q, la generación de claves
(n, φ(n), d), el cifrado `c = m^e mod n` y el descifrado `m' = c^d mod n`,
terminando con:

```
 RESULTADO: m' = 65  =  m = 65   [OK]
```

Se puede probar con otra instancia:

```bash
python scripts/traza_instancia.py --p 89 --q 97 --m 1234
python scripts/traza_instancia.py --p 61 --q 51     # caso inválido: q no es primo
```

### 2. Demostración de primalidad (división de prueba vs. Miller-Rabin)

```bash
python scripts/demo_primalidad.py                # instancia conocida
python scripts/demo_primalidad.py 61 53 561 3233  # números dados en la sesión
```

### 3. Demostración de factorización (división de prueba vs. Pollard Rho)

```bash
python scripts/demo_factorizacion.py             # n = 3233 (Avance 1)
python scripts/demo_factorizacion.py 561 600851475143
```

### 4. Pruebas automatizadas (plan de pruebas; suite completa en la Entrega 2)

```bash
pip install -r requirements.txt   # descomentar las líneas de pytest/hypothesis
pytest
```

## Estructura del repositorio

```
├── src/rsa_edu/            # biblioteca
│   ├── aritmetica.py       # mcd, Euclides extendido, inverso modular, exp. rápida
│   ├── primalidad.py       # división de tentativa y Miller-Rabin
│   ├── factorizacion.py    # división de prueba y Pollard Rho
│   ├── rsa.py              # generar_claves, cifrar, descifrar (pipeline RSA)
│   ├── contador.py         # contador de operaciones (Entrega 2)
│   └── formatos.py         # lectura/escritura de instancias y claves (Entrega 2)
├── scripts/
│   ├── traza_instancia.py  # traza completa del pipeline (verificable)
│   ├── demo_primalidad.py
│   ├── demo_factorizacion.py
│   └── ...                 # benchmarks y utilidades (Entrega 2)
├── tests/                  # suite de pruebas
├── data/instancias/        # instancias de prueba (JSON)
├── config/                 # configuración de experimentos
├── informe/                # informe LaTeX del proyecto
└── requirements.txt
```

## Integrantes y distribución de módulos

| Orden | Integrante | Capa / módulo | Commit |
|:-----:|------------|---------------|--------|
| 1 | Francesco Canal Acevedo | `aritmetica.py` — aritmética modular | `feat(aritmetica): implementar aritmética modular básica` |
| 2 | Orlando Clemente Lopez | `primalidad.py` — división de tentativa y Miller-Rabin | `feat(primalidad): implementar division_tentativa y miller_rabin con demo básico` |
| 3 | Camila Fernández Puente de la Vega | `factorizacion.py` — división de prueba y Pollard Rho | `feat(factorizacion): implementar factorizar_tentativa y pollard_rho con demo básico` |
| 4 | **Emmi Daniela Huaman Tairo** | `rsa.py` + `traza_instancia.py` + este `README.md` — integración y reproducibilidad | `feat(rsa): pipeline RSA básico con generacion de claves, cifrado y descifrado + traza instancia` |

Cadena de dependencias (no se puede saltar ninguna capa):

```
aritmética modular → primalidad → generación de claves → cifrado / descifrado
```

## Fuera del prototipo inicial (Entrega 2)

`exp_modular_ingenua`, `miller_rabin_determinista`, generación aleatoria de primos
(`generar_primo`), descifrado por Teorema Chino del Resto (`descifrar_crt`),
suite completa de pruebas con pytest/Hypothesis, archivos JSON de instancias y
scripts de benchmark con gráficos.
