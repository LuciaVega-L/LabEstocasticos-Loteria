from scipy.stats import chi2_contingency, spearmanr
import numpy as np

class AuditorEstadistico:

    def __init__(self, datos):
        self._fuente_datos = datos

    def evaluar_independencia(self) -> dict:
        centenas = self._fuente_datos.get_arreglo("centenas")
        decenas  = self._fuente_datos.get_arreglo("decenas")
        unidades = self._fuente_datos.get_arreglo("unidades")

        def p_value_chi2(arreglo_a, arreglo_b):
            tabla = np.zeros((10, 10), dtype=int)
            for a, b in zip(arreglo_a, arreglo_b):
                tabla[a][b] += 1
            _, p, _, _ = chi2_contingency(tabla)
            return p

        p_cd = p_value_chi2(centenas, decenas)
        p_du = p_value_chi2(decenas,  unidades)
        p_cu = p_value_chi2(centenas, unidades)

        return {
            "es_independiente": p_cd > 0.05 and p_du > 0.05 and p_cu > 0.05,
            "p_value_cd": p_cd,
            "p_value_du": p_du,
            "p_value_cu": p_cu
        }

    def evaluar_aleatoriedad(self) -> dict:
        resultados = {}
        for posicion in ["centenas", "decenas", "unidades"]:
            arreglo = self._fuente_datos.get_arreglo(posicion)
            indices = list(range(len(arreglo)))
            correlacion, p_value = spearmanr(indices, arreglo)
            resultados[posicion] = {
                "es_aleatorio": p_value > 0.05,
                "correlacion":  correlacion,
                "p_value":      p_value
            }
        return resultados

    def generar_reporte(self) -> str:
        indep  = self.evaluar_independencia()
        aleat  = self.evaluar_aleatoriedad()

        lineas = [
            "===== REPORTE DE AUDITORÍA ESTADÍSTICA =====",
            "",
            "--- Independencia entre posiciones ---",
            f"  Centenas vs Decenas  | p-value: {indep['p_value_cd']:.4f}",
            f"  Decenas  vs Unidades | p-value: {indep['p_value_du']:.4f}",
            f"  Centenas vs Unidades | p-value: {indep['p_value_cu']:.4f}",
            f"  Veredicto: {'INDEPENDIENTES ✓' if indep['es_independiente'] else 'NO independientes ✗'}",
            "",
            "--- Aleatoriedad por posición (Spearman) ---",
        ]

        for posicion, res in aleat.items():
            lineas.append(
                f"  {posicion.capitalize():10} | correlación: {res['correlacion']:+.4f} | "
                f"p-value: {res['p_value']:.4f} | "
                f"{'Aleatoria ✓' if res['es_aleatorio'] else 'No aleatoria ✗'}"
            )

        lineas += [
            "",
            "--- Conclusión ---",
            "  El modelo de Markov está justificado." if (
                indep["es_independiente"] and all(r["es_aleatorio"] for r in aleat.values())
            ) else "  Advertencia: los datos no cumplen todos los supuestos del modelo.",
            "",
            "============================================="
        ]

        return "\n".join(lineas)