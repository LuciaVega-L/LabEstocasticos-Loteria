import pandas as pd
import numpy as np
import os


class AnalizadorNumerosGanadores:
    """
    Clase para analizar la aleatoriedad e independencia de números ganadores
    de lotería mediante pruebas estadísticas de Chi-cuadrado y Autocorrelación.
    """

    VALOR_CRITICO_CHI = 16.919  # Chi-cuadrado crítico con gl=9 y α=0.05

    def __init__(self, ruta_excel: str = None):
        """
        Inicializa el analizador cargando los datos desde un archivo Excel.

        Args:
            ruta_excel (str): Ruta al archivo Excel. Si no se proporciona,
                              se construye automáticamente relativa al script.
        """
        self.ruta_excel = ruta_excel or self._ruta_por_defecto()
        self.df: pd.DataFrame = None
        self.centenas: np.ndarray = None
        self.decenas: np.ndarray = None
        self.unidades: np.ndarray = None
        self._cargar_datos()

    # ------------------------------------------------------------------
    # Métodos privados
    # ------------------------------------------------------------------

    def _ruta_por_defecto(self) -> str:
        """Construye la ruta por defecto al archivo Excel."""
        ruta_base = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(ruta_base, "..", "Data", "DB-NumerosGanadores.xlsx")

    def _cargar_datos(self) -> None:
        """Carga el archivo Excel y extrae las columnas de dígitos."""
        print(f"Cargando datos desde: {self.ruta_excel}")
        self.df = pd.read_excel(self.ruta_excel)
        self.centenas = self.df.iloc[:, 0].to_numpy()
        self.decenas  = self.df.iloc[:, 1].to_numpy()
        self.unidades = self.df.iloc[:, 2].to_numpy()
        print(f"Datos cargados: {len(self.centenas)} registros.\n")

    # ------------------------------------------------------------------
    # Métodos de análisis estadístico
    # ------------------------------------------------------------------

    def chi_cuadrado(self, datos: np.ndarray) -> tuple[float, np.ndarray]:
        """
        Calcula el estadístico Chi-cuadrado para evaluar uniformidad
        (aleatoriedad) de los dígitos 0-9.

        Args:
            datos (np.ndarray): Arreglo de dígitos a analizar.

        Returns:
            tuple: (estadístico chi², arreglo de frecuencias observadas)
        """
        n = len(datos)
        esperado = n / 10  # frecuencia esperada por dígito
        frecuencias = np.zeros(10)

        for d in datos:
            frecuencias[int(d)] += 1

        chi = np.sum((frecuencias - esperado) ** 2 / esperado)
        return chi, frecuencias

    def autocorrelacion(self, datos: np.ndarray, lag: int = 1) -> float:
        """
        Calcula la autocorrelación de los datos para evaluar independencia
        entre sorteos consecutivos.

        Args:
            datos (np.ndarray): Arreglo de dígitos a analizar.
            lag (int): Desfase temporal. Por defecto 1.

        Returns:
            float: Coeficiente de autocorrelación [-1, 1].
        """
        datos = np.array(datos, dtype=float)
        n = len(datos)
        media = np.mean(datos)
        num = np.sum((datos[:n - lag] - media) * (datos[lag:] - media))
        den = np.sum((datos - media) ** 2)
        return num / den

    # ------------------------------------------------------------------
    # Métodos de reporte
    # ------------------------------------------------------------------

    def reporte_chi_cuadrado(self) -> dict:
        """
        Calcula e imprime el reporte de Chi-cuadrado para las tres posiciones.

        Returns:
            dict: Resultados con estadístico y frecuencias por posición.
        """
        print("=== CHI-CUADRADO (ALEATORIEDAD) ===")
        resultados = {}
        for nombre, datos in [("Centenas", self.centenas),
                               ("Decenas",  self.decenas),
                               ("Unidades", self.unidades)]:
            chi, frecuencias = self.chi_cuadrado(datos)
            pasa = chi < self.VALOR_CRITICO_CHI
            print(f"{nombre:<10}: χ² = {chi:.4f}  "
                  f"{'✔ Pasa' if pasa else '✘ No pasa'} "
                  f"(crítico = {self.VALOR_CRITICO_CHI})")
            resultados[nombre] = {"chi": chi, "frecuencias": frecuencias, "pasa": pasa}
        return resultados

    def reporte_autocorrelacion(self, lag: int = 1) -> dict:
        """
        Calcula e imprime el reporte de autocorrelación para las tres posiciones.

        Args:
            lag (int): Desfase temporal. Por defecto 1.

        Returns:
            dict: Coeficientes de autocorrelación por posición.
        """
        print(f"\n=== AUTOCORRELACIÓN (INDEPENDENCIA) — lag={lag} ===")
        resultados = {}
        for nombre, datos in [("Centenas", self.centenas),
                               ("Decenas",  self.decenas),
                               ("Unidades", self.unidades)]:
            ac = self.autocorrelacion(datos, lag)
            print(f"{nombre:<10}: r = {ac:.6f}")
            resultados[nombre] = ac
        return resultados

    def analisis_completo(self, lag: int = 1) -> dict:
        """
        Ejecuta el análisis completo: Chi-cuadrado y Autocorrelación.

        Args:
            lag (int): Desfase para la autocorrelación. Por defecto 1.

        Returns:
            dict: Resultados combinados de ambas pruebas.
        """
        chi_resultados = self.reporte_chi_cuadrado()
        ac_resultados  = self.reporte_autocorrelacion(lag)
        return {"chi_cuadrado": chi_resultados, "autocorrelacion": ac_resultados}


# ------------------------------------------------------------------
# Punto de entrada
# ------------------------------------------------------------------
if __name__ == "__main__":
    analizador = AnalizadorNumerosGanadores()
    analizador.analisis_completo()
