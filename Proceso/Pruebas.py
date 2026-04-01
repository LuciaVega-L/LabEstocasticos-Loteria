import pandas as pd
import numpy as np
import os

ruta_base = os.path.dirname(__file__)

ruta_excel = os.path.join(ruta_base, "..", "Data", "DB-NumerosGanadores.xlsx")
print(ruta_excel)
df = pd.read_excel(ruta_excel)

# Extraer cada dígito
centenas = df.iloc[:, 0].to_numpy()
decenas = df.iloc[:, 1].to_numpy()
unidades = df.iloc[:, 2].to_numpy()
def chi_cuadrado(datos):
    n = len(datos)
    esperado = n / 10  # dígitos 0-9

    frecuencias = np.zeros(10)

    for d in datos:
        frecuencias[int(d)] += 1

    chi = np.sum((frecuencias - esperado)**2 / esperado)

    return chi, frecuencias
def autocorrelacion(datos, lag=1):
    datos = np.array(datos)
    n = len(datos)
    media = np.mean(datos)

    num = np.sum((datos[:n-lag] - media) * (datos[lag:] - media))
    den = np.sum((datos - media)**2)

    return num / den
print("=== CHI-CUADRADO (ALEATORIEDAD) ===")
chi_c, f_c = chi_cuadrado(centenas)
chi_d, f_d = chi_cuadrado(decenas)
chi_u, f_u = chi_cuadrado(unidades)

print("Centenas:", chi_c)
print("Decenas :", chi_d)
print("Unidades:", chi_u)

print("\n=== AUTOCORRELACIÓN (INDEPENDENCIA) ===")
ac_c = autocorrelacion(centenas)
ac_d = autocorrelacion(decenas)
ac_u = autocorrelacion(unidades)

print("Centenas:", ac_c)
print("Decenas :", ac_d)
print("Unidades:", ac_u)