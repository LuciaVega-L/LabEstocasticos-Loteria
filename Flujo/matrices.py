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
    def multiplicar_vector_matriz(v, M):
        n = len(M)
        m = len(M[0])
        resultado = [Decimal(0)] * m
        for j in range(m):
            for i in range(n):
                resultado[j] += v[i] * M[i][j]
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
