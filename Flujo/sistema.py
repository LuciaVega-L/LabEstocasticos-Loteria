from decimal import Decimal, getcontext
from matrices import Matrices

getcontext().prec = 50
class SistemaMarkovLoteria:

    def __init__(self, datos):
        self._fuente_datos        = datos
        self._matrices_transicion = {}
        self._vectores_estado     = {}

    # ─────────────────────────────────────────────
    # MÉTODOS PRIVADOS
    # ─────────────────────────────────────────────

    def _construir_matriz_suavizada(self, arreglo):
        conteos = [[0] * 10 for _ in range(10)]
        for t in range(len(arreglo) - 1):
            i = arreglo[t]
            j = arreglo[t + 1]
            conteos[i][j] += 1

        matriz = [[Decimal(0)] * 10 for _ in range(10)]
        for i in range(10):
            total_fila = sum(conteos[i])
            for j in range(10):
                if total_fila == 0:
                    matriz[i][j] = Decimal(1) / Decimal(10)
                else:
                    matriz[i][j] = Decimal(conteos[i][j]) / Decimal(total_fila)
        return matriz

    def _construir_vector_inicial(self, digito):
        vector = [Decimal(0)] * 10
        vector[digito] = Decimal(1)
        return vector

    # ─────────────────────────────────────────────
    # MÉTODOS PÚBLICOS
    # ─────────────────────────────────────────────

    def construir_modelo_completo(self):
        for posicion in ["centenas", "decenas", "unidades"]:
            arreglo = self._fuente_datos.get_arreglo(posicion)
            self._matrices_transicion[posicion] = self._construir_matriz_suavizada(arreglo)

        condicion_inicial = self._fuente_datos.get_condicion_inicial()
        self._vectores_estado["centenas"]  = self._construir_vector_inicial(condicion_inicial[0])
        self._vectores_estado["decenas"]   = self._construir_vector_inicial(condicion_inicial[1])
        self._vectores_estado["unidades"]  = self._construir_vector_inicial(condicion_inicial[2])

    def predecir_a_futuro(self, k_dias):
        resultado = {}

        for posicion in ["centenas", "decenas", "unidades"]:
            M  = self._matrices_transicion[posicion]
            v  = self._vectores_estado[posicion]
            Mk = Matrices.potencia_matriz(M, k_dias)
            vk = Matrices.multiplicar_vector_matriz(v, Mk)

            resultado[posicion] = {
                "vector": vk
            }

        return resultado

    def caso1_numero_mas_probable(self, k_dias):
        vectores = self.predecir_a_futuro(k_dias)
        detalle  = {}

        for posicion in ["centenas", "decenas", "unidades"]:
            vk      = vectores[posicion]["vector"]
            maximo  = max(vk)
            digito  = vk.index(maximo)
            empates = [i for i, v in enumerate(vk) if v == maximo and i != digito]

            detalle[posicion] = {
                "digito":       digito,
                "probabilidad": maximo,
                "empates":      empates
            }

        probabilidad_conjunta = (
            detalle["centenas"]["probabilidad"] *
            detalle["decenas"]["probabilidad"]  *
            detalle["unidades"]["probabilidad"]
        )

        return {
            "numero":                (detalle["centenas"]["digito"],
                                      detalle["decenas"]["digito"],
                                      detalle["unidades"]["digito"]),
            "probabilidad_conjunta": probabilidad_conjunta,
            "detalle":               detalle
        }


    def caso2_probabilidad_numero(self, k_dias, numero):
        vectores = self.predecir_a_futuro(k_dias)
        detalle  = {}

        for posicion, digito in zip(["centenas", "decenas", "unidades"], numero):
            prob = vectores[posicion]["vector"][digito]

            detalle[posicion] = {
                "digito":       digito,
                "probabilidad": prob
            }

        probabilidad_conjunta = (
            detalle["centenas"]["probabilidad"] *
            detalle["decenas"]["probabilidad"]  *
            detalle["unidades"]["probabilidad"]
        )

        return {
            "numero":                numero,
            "probabilidad_conjunta": probabilidad_conjunta,
            "detalle":               detalle
        }