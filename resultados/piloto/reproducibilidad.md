# Verificación del experimento piloto (piloto)

Configuración: `piloto.json` · semilla 2026 · 3 repeticiones · dos corridas independientes

## 1. Correctos

- Filas medidas por corrida: 184
- Filas con resultado incorrecto o inestable: 0 [OK]

## 2. Reproducibles

- Mismas filas en ambas corridas: sí [OK]
- Filas con conteos de operaciones distintos: 0 [OK]
- Tiempos con diferencia ≤ 25% entre corridas: 118/126 (94%) [OK]
- Diferencia relativa mediana entre corridas: 4.4%
- Coeficiente de variación mediano dentro de una corrida: 5.6%

## 3. Coherentes con la teoría

- E1: la división de prueba hace a lo más sqrt(n)/6 + 1 iteraciones: 26/26 [OK]
- E3: la binaria hace a lo más 2·bits multiplicaciones: 4/4 [OK]
- E3: la ventana hace menos multiplicaciones que la binaria: 4/4 [OK]
- E4: el TCR descifra en menos tiempo que el directo: 1/1 [OK]
- E5: la criba reduce las llamadas a Miller-Rabin: 2/2 [OK]
- E6: el cifrado hace las mismas multiplicaciones en base y optimizado: 1/1 [OK]
- E6: el descifrado optimizado es más rápido que el base: 1/1 [OK]

**Resultado: procedimiento válido [OK]**
