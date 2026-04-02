import os
from datos import DatosLoteria
from analisis_loteria import AuditorEstadistico



def main():
    print("hola mundo")
    # Ruta al archivo CSV con el historial de la lotería
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ruta_archivo = os.path.join(script_dir, "..", "Data", "historial_loteria.xlsx")

    print("Cargando datos de la lotería desde:", ruta_archivo)

    # Crear instancia de DatosLoteria y cargar datos
    datos_loteria = DatosLoteria(ruta_archivo)
    if not datos_loteria.cargar_historial():
        print("Error al cargar el historial de la lotería.")
        return

    # Obtener los arreglos de dígitos para cada posición
    centenas = datos_loteria.get_arreglo("centenas")
    decenas  = datos_loteria.get_arreglo("decenas")
    unidades = datos_loteria.get_arreglo("unidades")
   
    #Imprimir longitud de cada arreglo
    print("Longitud del arreglo de centenas:", len(centenas))
    print("Longitud del arreglo de decenas:", len(decenas))
    print("Longitud del arreglo de unidades:", len(unidades))

    # Imprimir la última condición inicial (último número registrado)
    condicion_inicial = datos_loteria.get_condicion_inicial()
    print("Último número registrado (condición inicial):", condicion_inicial)

    # Crear instancia de AuditorEstadistico
    auditor = AuditorEstadistico(datos_loteria)
    
    # Generar reporte de auditoría
    reporte = auditor.generar_reporte()
    print(reporte)

if __name__ == "__main__":
    main()