from decimal import Decimal, getcontext
getcontext().prec = 50

class SistemaMarkovLoteria:

    def __init__(self, datos):
        self._fuente_datos        = datos
        self._matrices_transicion = {}
        self._vectores_estado     = {}

    # ─────────────────────────────────────────────
    # MÉTODOS PRIVADOS
    # ─────────────────────────────────────────────

    def _multiplicar_matrices(self, A, B):
        n = len(A)
        m = len(B[0])
        p = len(B)
        resultado = [[Decimal(0)] * m for _ in range(n)]
        for i in range(n):
            for j in range(m):
                for k in range(p):
                    resultado[i][j] += A[i][k] * B[k][j]
        return resultado

    def _multiplicar_vector_matriz(self, v, M):
        n = len(M)
        m = len(M[0])
        resultado = [Decimal(0)] * m
        for j in range(m):
            for i in range(n):
                resultado[j] += v[i] * M[i][j]
        return resultado

    def _potencia_matriz(self, M, k):
        if k == 1:
            return [fila[:] for fila in M]
        if k % 2 == 0:
            mitad = self._potencia_matriz(M, k // 2)
            return self._multiplicar_matrices(mitad, mitad)
        else:
            return self._multiplicar_matrices(M, self._potencia_matriz(M, k - 1))

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
            Mk = self._potencia_matriz(M, k_dias)
            vk = self._multiplicar_vector_matriz(v, Mk)

            resultado[posicion] = {
                "vector": vk
            }

        return resultado