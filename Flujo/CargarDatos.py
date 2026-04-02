import pandas as pd

#guarda la dirección del excel
ruta = "Data/DB-NumerosGanadores.xlsx"
#leer el excel
df = pd.read_excel(ruta, header=None)
#renombra columnas para estandarizar
df.columns = ["num1", "num2", "num3"]

#esta es la matriz! se llamará sorteos
sorteos = df.values


print(f"Sorteos cargados: {len(sorteos)}")
print(f"Primeros 5:\n{sorteos[:5]}")

