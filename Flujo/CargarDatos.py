import pandas as pd


ruta = "Data/DB-NumerosGanadores.xlsx"

df = pd.read_excel(ruta, header=None)
df.columns = ["num1", "num2", "num3"]

sorteos = df.values


print(f"Sorteos cargados: {len(sorteos)}")
print(f"Primeros 5:\n{sorteos[:5]}")