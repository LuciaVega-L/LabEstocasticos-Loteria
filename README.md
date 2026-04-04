# Laboratorio 2 — Predicción de la Lotería con Cadenas de Markov

## Contexto del proyecto

Este proyecto es un laboratorio universitario de la materia de **Procesos Estocásticos**. El objetivo es construir un sistema que prediga números de lotería de tres dígitos usando **Cadenas de Markov discretas en tiempo discreto**.

El número ganador de la lotería se compone de tres dígitos: centena, decena y unidad. La hipótesis del modelo es que cada posición puede modelarse como una cadena de Markov independiente: el dígito que saldrá mañana depende únicamente del dígito que salió hoy en esa misma posición.

---

## Arquitectura general del proyecto

El proyecto está dividido en módulos con responsabilidades separadas:

```
proyecto/
├── Flujo/
│   ├── datos.py          # Carga y gestión del historial desde archivo
│   ├── markov.py         # Modelo estocástico y predicciones
│   └── main.py           # Punto de entrada y pruebas
└── Data/
    └── historial_loteria.xlsx   # Historial cronológico de números ganadores
```

El archivo de datos contiene una fila por cada sorteo histórico, con tres columnas: la centena, la decena y la unidad del número ganador, en orden cronológico.

---

## Módulo `datos.py` — Clase `DatosLoteria`

### Responsabilidad

Cargar el historial desde un archivo `.xlsx` o `.csv` y exponerlo al resto del sistema a través de métodos públicos. No hace matemáticas: solo organiza y entrega datos.

### Atributos internos

| Atributo | Tipo | Descripción |
|---|---|---|
| `_ruta_archivo` | `str` | Ruta al archivo de historial |
| `_datos_df` | `DataFrame` | Tabla completa cargada con pandas |
| `_arreglos_digitos` | `dict` | Listas separadas por posición: centenas, decenas, unidades |
| `_ultimo_numero` | `tuple` | Último número registrado `(centena, decena, unidad)` |

### Métodos

#### `cargar_historial() -> bool`

Lee el archivo (`.xlsx` o `.csv`) con `pandas`. Las tres columnas se nombran internamente `centenas`, `decenas`, `unidades` sin importar los encabezados originales del archivo. Extrae los valores de cada columna como listas de enteros y guarda el último registro como condición inicial del modelo.

#### `get_arreglo(posicion: str) -> list`

Retorna una copia de la lista de dígitos históricos para la posición solicitada (`"centenas"`, `"decenas"` o `"unidades"`). Retorna una copia para que nadie pueda modificar el historial interno accidentalmente.

#### `get_condicion_inicial() -> tuple`

Retorna el último número registrado como tupla `(centena, decena, unidad)`. Este valor es la **condición inicial** del modelo de Markov: representa el estado actual del sistema antes de hacer cualquier predicción.

#### `set_nuevo_registro(centena, decena, unidad) -> bool`

Agrega un nuevo sorteo al historial en memoria y lo persiste inmediatamente en el archivo original. Esto permite que el modelo sea **adaptativo**: al ingresar datos nuevos y reconstruir el modelo, las matrices de transición se actualizan automáticamente sin cambiar el núcleo del sistema.

---

## Módulo `markov.py` — Clase `SistemaMarkovLoteria`

### Responsabilidad

Construir el modelo estocástico de alta precisión y calcular predicciones. Consume datos de `DatosLoteria` pero no la modifica: es un consumidor puro de información.

### Decisiones de diseño relevantes

#### ¿Por qué matrices 10×10 siempre?

Los dígitos van del 0 al 9, así que hay exactamente 10 estados posibles por posición. Las matrices son siempre 10×10 independientemente de cuáles dígitos hayan aparecido en el historial. Si una fila no tiene observaciones (ese dígito nunca apareció como estado actual), se le asigna una distribución uniforme de `1/10` en cada celda. Esto se llama **suavizado** y evita que el modelo colapse ante estados no observados.

#### ¿Por qué `decimal.Decimal` y no `float`?

Las operaciones de cadenas de Markov implican multiplicaciones repetidas de probabilidades pequeñas. Con `float` de 64 bits (~15 dígitos significativos), el error de punto flotante se acumula en cada operación matricial. Con `decimal.Decimal` configurado a 50 dígitos de precisión, estas operaciones son exactas dentro de ese margen. No se usa `mpmath` porque no es necesaria para este volumen de datos (~5000 registros por posición), y `decimal` está en la librería estándar de Python sin dependencias adicionales.

#### ¿Por qué vectores fila y no vectores columna?

En cadenas de Markov discretas con matrices de transición donde **las filas suman 1**, la operación correcta es:

```
v(k) = v(0) · M^k
```

donde `v` es un **vector fila**. Si se usa vector columna y se calcula `M^k · v`, el resultado solo suma 1 si las **columnas** de M también suman 1 (matriz doblemente estocástica), lo cual no está garantizado en datos reales de lotería. Por eso se usa la convención de vector fila y la operación `v · M`.

#### ¿Por qué las tres posiciones son independientes?

El número de tres dígitos se modela como tres cadenas de Markov independientes, una por posición. Esto significa que la centena no influye en la decena ni en la unidad. Esta es una simplificación del modelo que hace la matemática tratable y está justificada por el enunciado del laboratorio.

### Atributos internos

| Atributo | Tipo | Descripción |
|---|---|---|
| `_fuente_datos` | `DatosLoteria` | Referencia al objeto de datos |
| `_matrices_transicion` | `dict` | Una matriz 10×10 de `Decimal` por posición |
| `_vectores_estado` | `dict` | Un vector fila de longitud 10 por posición |

### Métodos

#### `_construir_matriz_suavizada(arreglo: list) -> list[list[Decimal]]`

Recibe la secuencia histórica de un dígito (ej. todas las centenas en orden cronológico) y construye la matriz de transición 10×10.

**Algoritmo:**

1. Recorre el arreglo de izquierda a derecha, tomando pares consecutivos `(arreglo[t], arreglo[t+1])`.
2. Para cada par, incrementa el contador `conteos[i][j]` donde `i` es el dígito actual y `j` es el siguiente.
3. Para cada fila `i`, divide cada conteo por el total de la fila para obtener la probabilidad de transición `P(i → j)`.
4. Si una fila tiene total cero (ese dígito nunca apareció), se asigna `1/10` a cada celda (suavizado uniforme).

Todos los valores se almacenan como `Decimal` desde el primer momento para no acumular error de punto flotante.

#### `_construir_vector_inicial(digito: int) -> list[Decimal]`

Retorna el **vector canónico** para el dígito dado: una lista de 10 elementos donde la posición `digito` vale `1` y el resto valen `0`. Representa certeza absoluta: "el último número conocido en esta posición fue exactamente este dígito".

#### `_multiplicar_matrices(A, B) -> list[list[Decimal]]`

Multiplicación matricial estándar implementada con listas de listas y `Decimal`. Se usa para la exponenciación de matrices (`M × M`).

#### `_multiplicar_vector_matriz(v, M) -> list[Decimal]`

Multiplicación de vector fila por matriz: `v · M`. Retorna un vector fila. Esta es la operación central de la proyección de Markov.

#### `_potencia_matriz(M, k) -> list[list[Decimal]]`

Calcula `M^k` usando **exponenciación rápida por cuadrados** con complejidad O(log k):

```
M^k = M^(k/2) · M^(k/2)        si k es par
M^k = M · M^(k-1)               si k es impar
M^1 = copia de M                 caso base
```

El caso base retorna una **copia** de la matriz (no la referencia original) para evitar mutaciones accidentales sobre `_matrices_transicion`.

#### `construir_modelo_completo() -> None`

Método principal que orquesta la construcción del modelo completo:

1. Para cada posición (`centenas`, `decenas`, `unidades`), obtiene el arreglo histórico de `DatosLoteria` y construye su matriz de transición.
2. Obtiene la condición inicial (último número registrado) y construye el vector de estado inicial para cada posición.

Después de llamar a este método, el sistema está listo para predecir.

#### `predecir_a_futuro(k_dias: int) -> dict`

Proyecta el estado del sistema `k_dias` hacia adelante usando la fórmula:

```
v(k) = v(0) · M^k
```

Para cada posición retorna el **vector completo de distribución de probabilidad** sobre los 10 dígitos posibles. El resultado tiene la forma:

```python
{
    "centenas": {"vector": [Decimal, Decimal, ...]},  # longitud 10
    "decenas":  {"vector": [Decimal, Decimal, ...]},
    "unidades": {"vector": [Decimal, Decimal, ...]}
}
```

Se retorna el vector completo (no solo el máximo) porque hay dos casos de uso distintos:

- **Caso 1** — número más probable en k días: tomar el `argmax` de cada vector y multiplicar las tres probabilidades máximas.
- **Caso 2** — probabilidad de un número específico: extraer el valor en el índice exacto de cada dígito del número consultado y multiplicar los tres valores.

Ambos casos los resuelve quien consuma este método, sin que la clase tome decisiones que no le corresponden.

---

## Módulo `main.py` — Pruebas del sistema

El `main.py` actual cumple dos funciones: ejecutar pruebas de la clase `DatosLoteria` (longitudes de arreglos, condición inicial) y un bloque de test completo para `SistemaMarkovLoteria`.

### Bloque de test — qué verifica y por qué

#### 1. Filas de cada matriz suman 1

```python
todas_suman_uno = all(abs(s - Decimal(1)) < Decimal("1e-40") for s in sumas)
```

Una matriz de transición válida debe ser **estocástica**: cada fila representa una distribución de probabilidad y debe sumar exactamente 1. Si alguna fila no cumple esto, el modelo está mal construido. El umbral `1e-40` es conservador dado que trabajamos con 50 dígitos de precisión.

#### 2. Vector inicial es canónico

Verifica que el vector de estado inicial tenga exactamente un `1` en la posición del último dígito conocido y `0` en todas las demás. Esto garantiza que la condición inicial representa certeza absoluta sobre el estado actual.

#### 3. Predicciones para k = 1, 5 y 10 días

```python
digito = vk.index(max(vk))
prob  *= max(vk)
```

Para cada k, extrae el dígito más probable por posición (Caso 1) y calcula la probabilidad conjunta multiplicando los tres máximos. Esto prueba que `_potencia_matriz` y `_multiplicar_vector_matriz` funcionan sin errores para distintos valores de k.

#### 4. Vector resultante suma 1 para k = 1

```python
suma = sum(vk)
```

Después de proyectar un paso, el vector resultante debe seguir siendo una distribución de probabilidad válida y sumar 1. Esta verificación confirma que la operación `v · M` está implementada correctamente.

---

## Dependencias

| Librería | Origen | Uso |
|---|---|---|
| `pandas` | Externa (`pip install pandas`) | Lectura de `.xlsx` y `.csv` |
| `openpyxl` | Externa (`pip install openpyxl`) | Motor de lectura de `.xlsx` requerido por pandas |
| `decimal` | Librería estándar de Python | Aritmética de alta precisión (50 dígitos) |

---

## Cómo ejecutar

```bash
cd Flujo
python main.py
```

El archivo de datos debe estar en `../Data/historial_loteria.xlsx` relativo al directorio `Flujo/`.
