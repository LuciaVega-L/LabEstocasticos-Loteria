from decimal import Decimal

class Matrices:
    @staticmethod
    def multiplicar_matrices(A, B):
        n = len(A)
        m = len(B[0])
        p = len(B)
        resultado = [[Decimal(0)] * m for _ in range(n)]
        for i in range(n):
            for j in range(m):
                for k in range(p):
                    resultado[i][j] += A[i][k] * B[k][j]
        return resultado

    @staticmethod
    def multiplicar_matriz_vector(M, v):
        n = len(M) 
        resultado = [Decimal(0)] * n
        for i in range(n):
            for j in range(len(v)):
                resultado[i] += M[i][j] * v[j]
        return resultado

    @staticmethod
    def potencia_matriz(M, k):
        if k == 1:
            return [fila[:] for fila in M]
        if k % 2 == 0:
            mitad = Matrices.potencia_matriz(M, k // 2)
            return Matrices.multiplicar_matrices(mitad, mitad)
        else:
            return Matrices.multiplicar_matrices(M, Matrices.potencia_matriz(M, k - 1))

    @staticmethod
    def transponer_matriz(M):
        filas = len(M)
        columnas = len(M[0])
        return [[M[i][j] for i in range(filas)] for j in range(columnas)]
