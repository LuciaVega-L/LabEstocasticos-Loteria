import pandas as pd

class DatosLoteria:

    def __init__(self, ruta_archivo: str):
        self._ruta_archivo     = ruta_archivo
        self._datos_df         = None
        self._arreglos_digitos = {"centenas": [], "decenas": [], "unidades": []}
        self._ultimo_numero    = None

    def cargar_historial(self) -> bool:
        if self._ruta_archivo.endswith(".xlsx") or self._ruta_archivo.endswith(".xls"):
            self._datos_df = pd.read_excel(self._ruta_archivo, header=None, names=["centenas", "decenas", "unidades"])
        else:
            self._datos_df = pd.read_csv(self._ruta_archivo, header=None, names=["centenas", "decenas", "unidades"])

        self._arreglos_digitos["centenas"] = self._datos_df["centenas"].astype(int).tolist()
        self._arreglos_digitos["decenas"]  = self._datos_df["decenas"].astype(int).tolist()
        self._arreglos_digitos["unidades"] = self._datos_df["unidades"].astype(int).tolist()

        ultima_fila = self._datos_df.iloc[-1]
        self._ultimo_numero = (
            int(ultima_fila["centenas"]),
            int(ultima_fila["decenas"]),
            int(ultima_fila["unidades"])
        )
        return True

    def get_arreglo(self, posicion: str) -> list:
        return self._arreglos_digitos[posicion].copy()

    def get_condicion_inicial(self) -> tuple:
        return self._ultimo_numero

    def set_nuevo_registro(self, centena: int, decena: int, unidad: int) -> bool:
        nueva_fila = pd.DataFrame([[centena, decena, unidad]])
        self._datos_df = pd.concat([self._datos_df, nueva_fila], ignore_index=True)

        self._arreglos_digitos["centenas"].append(centena)
        self._arreglos_digitos["decenas"].append(decena)
        self._arreglos_digitos["unidades"].append(unidad)

        self._ultimo_numero = (centena, decena, unidad)

        if self._ruta_archivo.endswith(".xlsx") or self._ruta_archivo.endswith(".xls"):
            self._datos_df.to_excel(self._ruta_archivo, index=False, header=False)
        else:
            self._datos_df.to_csv(self._ruta_archivo, index=False, header=False)

        return True