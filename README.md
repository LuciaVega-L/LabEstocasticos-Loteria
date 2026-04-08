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

## Casos de uso — Métodos públicos de predicción

Una vez construido el modelo con `construir_modelo_completo()`, los dos casos de uso del laboratorio se resuelven con estos dos métodos. Ambos viven dentro de `SistemaMarkovLoteria` e internamente delegan en `predecir_a_futuro`.

---

### `caso1_numero_mas_probable(k_dias)`

```
┌─────────────────────────────────────────────────────────────────┐
│               caso1_numero_mas_probable(k_dias)                 │
├─────────────────────────────────────────────────────────────────┤
│  ENTRADA                                                        │
│  └── k_dias : int                                               │
│        Número de días hacia adelante que se desea proyectar.    │
│        Ejemplo: 5 → "¿qué número es más probable en 5 días?"   │
├─────────────────────────────────────────────────────────────────┤
│  PROCESO INTERNO                                                │
│  1. Llama a predecir_a_futuro(k_dias)                          │
│     → obtiene v(k) para centenas, decenas y unidades           │
│  2. Para cada posición:                                         │
│     · maximo  = max(v(k))                                       │
│     · digito  = índice del máximo (argmax)                      │
│     · empates = lista de otros índices con el mismo valor       │
│  3. probabilidad_conjunta = prob_c × prob_d × prob_u            │
│     (regla multiplicativa — las tres posiciones son             │
│      independientes por diseño del modelo)                      │
├─────────────────────────────────────────────────────────────────┤
│  SALIDA : dict                                                  │
│                                                                 │
│  {                                                              │
│    "numero": (int, int, int),                                   │
│        └── tupla (centena, decena, unidad) más probable         │
│            Ejemplo: (1, 9, 1)                                   │
│                                                                 │
│    "probabilidad_conjunta": Decimal,                            │
│        └── producto de las tres probabilidades máximas          │
│            Ejemplo: 0.0011786956...                             │
│                                                                 │
│    "detalle": {                                                 │
│      "centenas": {                                              │
│        "digito":       int,      ← dígito más probable (0-9)   │
│        "probabilidad": Decimal,  ← su probabilidad individual  │
│        "empates":      list[int] ← [] si no hay empate,        │
│      },                            o [i, j, ...] si los hay    │
│      "decenas":  { ... },  ← misma estructura                  │
│      "unidades": { ... }   ← misma estructura                  │
│    }                                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

**Ejemplo de uso:**
```python
resultado = sistema.caso1_numero_mas_probable(5)

numero = resultado["numero"]                    # (1, 9, 1)
prob   = resultado["probabilidad_conjunta"]     # Decimal('0.00117...')

# Si se quiere inspeccionar el detalle por posición:
detalle_c = resultado["detalle"]["centenas"]
print(detalle_c["digito"])       # 1
print(detalle_c["probabilidad"]) # Decimal('0.10603...')
print(detalle_c["empates"])      # [] — sin empates
```

**Nota sobre empates:** si dos dígitos tienen exactamente la misma probabilidad máxima, `"digito"` toma el primero (el de índice menor) y `"empates"` lista los demás. No cambia la decisión, pero queda registrado para que la interfaz pueda informarlo.

---

### `caso2_probabilidad_numero(k_dias, numero)`

```
┌─────────────────────────────────────────────────────────────────┐
│           caso2_probabilidad_numero(k_dias, numero)             │
├─────────────────────────────────────────────────────────────────┤
│  ENTRADA                                                        │
│  ├── k_dias : int                                               │
│  │     Número de días hacia adelante a proyectar.               │
│  │     Ejemplo: 10                                              │
│  └── numero : tuple(int, int, int)                              │
│        Número específico a consultar, como tupla de dígitos.    │
│        Ejemplo: (5, 2, 1) → número "521"                        │
│                                                                 │
│  ¿Por qué tupla y no entero?                                    │
│  Porque la interfaz normalmente recibe tres campos separados    │
│  (uno por dígito), y así es consistente con get_condicion_      │
│  inicial() que usa el mismo formato. Construir la tupla en la   │
│  capa de interfaz es natural: (c, d, u) = campos del formulario │
├─────────────────────────────────────────────────────────────────┤
│  PROCESO INTERNO                                                │
│  1. Llama a predecir_a_futuro(k_dias)                          │
│     → obtiene v(k) para centenas, decenas y unidades           │
│  2. Desempaqueta numero → (digito_c, digito_d, digito_u)        │
│  3. Para cada posición extrae el valor exacto del vector:       │
│     · prob_c = v_centenas[digito_c]                             │
│     · prob_d = v_decenas[digito_d]                              │
│     · prob_u = v_unidades[digito_u]                             │
│  4. probabilidad_conjunta = prob_c × prob_d × prob_u            │
├─────────────────────────────────────────────────────────────────┤
│  SALIDA : dict                                                  │
│                                                                 │
│  {                                                              │
│    "numero": (int, int, int),                                   │
│        └── el mismo número que se recibió como entrada          │
│            Ejemplo: (5, 2, 1)                                   │
│                                                                 │
│    "probabilidad_conjunta": Decimal,                            │
│        └── probabilidad de que ese número exacto salga          │
│            en k días                                            │
│            Ejemplo: 0.0013614058...                             │
│                                                                 │
│    "detalle": {                                                 │
│      "centenas": {                                              │
│        "digito":       int,      ← el dígito consultado        │
│        "probabilidad": Decimal   ← su probabilidad en v(k)     │
│      },                                                         │
│      "decenas":  { ... },  ← misma estructura                  │
│      "unidades": { ... }   ← misma estructura                  │
│    }                                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

**Ejemplo de uso:**
```python
resultado = sistema.caso2_probabilidad_numero(10, (5, 2, 1))

prob = resultado["probabilidad_conjunta"]   # Decimal('0.00103...')

# Desglose por posición:
for posicion in ["centenas", "decenas", "unidades"]:
    d = resultado["detalle"][posicion]
    print(f"{posicion}: dígito={d['digito']}  prob={d['probabilidad']}")
```

---

### Relación entre los dos casos y `predecir_a_futuro`

```
predecir_a_futuro(k)
        │
        │  retorna vectores completos v(k) para las 3 posiciones
        │
        ├──► caso1_numero_mas_probable(k)
        │         toma el argmax de cada vector
        │         → el número más probable + su probabilidad conjunta
        │
        └──► caso2_probabilidad_numero(k, numero)
                  extrae el índice exacto de cada vector
                  → la probabilidad de ese número específico
```

Esta separación garantiza que la lógica matemática pesada (exponenciación de matrices, multiplicación vector-matriz) se ejecuta una sola vez en `predecir_a_futuro`, y los dos casos solo interpretan el resultado.

---

## Verificación matemática independiente

Para validar que el modelo está correctamente implementado, se realizó una verificación manual completa sobre los datos reales del archivo `historial_loteria.xlsx` (7489 registros).

El proceso fue:

1. Construir la matriz de conteos para la posición de **centenas** recorriendo los 7489 registros en orden cronológico y contando cuántas veces el dígito `i` fue seguido por el dígito `j`.
2. Dividir cada fila por su total para obtener la matriz estocástica.
3. Construir el vector inicial `e_5` (condición inicial: última centena fue `5`).
4. Calcular `v(1) = v(0) · M` manualmente con `Decimal`.
5. Comparar contra lo que reporta el sistema para `k=1`, posición centenas.

**Resultado:**

| | Dígito más probable | Probabilidad |
|---|---|---|
| Sistema | 5 | 0.1164658635 |
| Verificación manual | 5 | 0.1164658635 |

Coincidencia exacta. El vector resultante suma `0.9999999...` con 50 dígitos, confirmando que tanto la construcción de la matriz como la operación `v · M` están implementadas correctamente de raíz.

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

#### 5. Test de Caso 1 — número más probable

Para k = 1, 5 y 10 días, imprime el número más probable, su probabilidad conjunta y el detalle por posición incluyendo empates si los hay. Verifica que los tres métodos (`predecir_a_futuro`, `caso1_numero_mas_probable`, manejo de empates) funcionan de extremo a extremo.

#### 6. Test de Caso 2 — probabilidad de número específico

Consulta tres números concretos (`521`, `000`, `361`) para k = 1, 5 y 10 días. Verifica que la extracción del índice exacto del vector funciona correctamente y que la probabilidad conjunta se calcula bien.

#### 7. Verificación cruzada Caso 1 vs Caso 2

```python
res_c1    = sistema.caso1_numero_mas_probable(k)
numero_c1 = res_c1["numero"]
res_c2    = sistema.caso2_probabilidad_numero(k, numero_c1)
coincide  = abs(res_c1["probabilidad_conjunta"] - res_c2["probabilidad_conjunta"]) < Decimal("1e-40")
```

Si se le pide al Caso 2 la probabilidad del mismo número que predijo el Caso 1, ambos deben dar exactamente el mismo valor. Esta es la verificación más importante: si falla, hay una inconsistencia entre los dos métodos. Con los datos reales (7489 registros), los tres valores de k probados dieron `OK`.
