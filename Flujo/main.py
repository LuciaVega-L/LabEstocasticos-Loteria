import os
from datos import DatosLoteria
from analisis_loteria import AuditorEstadistico
from sistema import SistemaMarkovLoteria
from decimal import Decimal

def main():
    print("hola mundo")
    script_dir   = os.path.dirname(os.path.abspath(__file__))
    ruta_archivo = os.path.join(script_dir, "..", "Data", "historial_loteria.xlsx")
    print("Cargando datos de la lotería desde:", ruta_archivo)

    datos_loteria = DatosLoteria(ruta_archivo)
    if not datos_loteria.cargar_historial():
        print("Error al cargar el historial de la lotería.")
        return

    centenas = datos_loteria.get_arreglo("centenas")
    decenas  = datos_loteria.get_arreglo("decenas")
    unidades = datos_loteria.get_arreglo("unidades")
    print("Longitud del arreglo de centenas:", len(centenas))
    print("Longitud del arreglo de decenas:",  len(decenas))
    print("Longitud del arreglo de unidades:", len(unidades))

    condicion_inicial = datos_loteria.get_condicion_inicial()
    print("Último número registrado (condición inicial):", condicion_inicial)

    auditor = AuditorEstadistico(datos_loteria)
    reporte = auditor.generar_reporte()
    print(reporte)

    # ── TEST SistemaMarkovLoteria ──────────────────────────────────────

    print("\n" + "="*50)
    print("TEST: SistemaMarkovLoteria")
    print("="*50)

    sistema = SistemaMarkovLoteria(datos_loteria)
    sistema.construir_modelo_completo()
    print("Modelo construido correctamente.")

    # Verificar que las matrices son estocásticas (cada fila suma 1)
    print("\n-- Verificación: filas de cada matriz suman 1 --")
    for posicion in ["centenas", "decenas", "unidades"]:
        matriz = sistema._matrices_transicion[posicion]
        sumas  = [sum(fila) for fila in matriz]
        todas_suman_uno = all(abs(s - Decimal(1)) < Decimal("1e-40") for s in sumas)
        print(f"  {posicion}: {'OK' if todas_suman_uno else 'ERROR — alguna fila no suma 1'}")
        if not todas_suman_uno:
            for i, s in enumerate(sumas):
                print(f"    fila {i}: {s}")

    # Verificar vector inicial
    print("\n-- Verificación: vector inicial --")
    for posicion, digito in zip(["centenas", "decenas", "unidades"], condicion_inicial):
        vector = sistema._vectores_estado[posicion]
        print(f"  {posicion} (dígito={digito}): posición {digito} = {vector[digito]}, resto = {[vector[i] for i in range(10) if i != digito]}")

    # Predicción a 1, 5 y 10 días
    print("\n-- Predicciones --")
    for k in [1, 5, 10]:
        resultado = sistema.predecir_a_futuro(k)
        numero    = []
        prob      = Decimal(1)
        for posicion in ["centenas", "decenas", "unidades"]:
            vk     = resultado[posicion]["vector"]
            digito = vk.index(max(vk))
            numero.append(digito)
            prob *= max(vk)
        print(f"  k={k:>2} días → número más probable: {''.join(map(str, numero))}  |  probabilidad conjunta: {prob:.10f}")

    # Verificar que el vector resultante suma 1 para k=1
    print("\n-- Verificación: vectores resultantes suman 1 (k=1) --")
    resultado_k1 = sistema.predecir_a_futuro(1)
    for posicion in ["centenas", "decenas", "unidades"]:
        vk   = resultado_k1[posicion]["vector"]
        suma = sum(vk)
        print(f"  {posicion}: suma = {suma}  {'OK' if abs(suma - Decimal(1)) < Decimal('1e-40') else 'ERROR'}")

if __name__ == "__main__":
    main()