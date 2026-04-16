import sys
import os
from decimal import Decimal

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox,
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QPalette, QIntValidator
from PyQt6 import uic

# ── módulos de lógica ────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datos import DatosLoteria
from analisis_loteria import AuditorEstadistico
from sistema import SistemaMarkovLoteria


# ── Worker thread para cálculos pesados ─────────────────────────────────────
class WorkerPrediccion(QThread):
    resultado = pyqtSignal(dict)
    error     = pyqtSignal(str)

    def __init__(self, sistema, modo, k, numero=None):
        super().__init__()
        self.sistema = sistema
        self.modo    = modo   # "caso1" | "caso2"
        self.k       = k
        self.numero  = numero

    def run(self):
        try:
            if self.modo == "caso1":
                res = self.sistema.caso1_numero_mas_probable(self.k)
            else:
                res = self.sistema.caso2_probabilidad_numero(self.k, self.numero)
            self.resultado.emit(res)
        except Exception as e:
            self.error.emit(str(e))


# ── Ventana principal ────────────────────────────────────────────────────────
class MainWindow(QMainWindow):

    # Índices de página en stackPrincipal
    PAGE_MENU     = 0
    PAGE_CASO1    = 1
    PAGE_CASO2    = 2
    PAGE_MATRICES = 3
    PAGE_REGISTRO = 4

    def __init__(self):
        super().__init__()

        # Cargar .ui
        ui_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "Interfaz", "main_window.ui"
        )
        uic.loadUi(ui_path, self)

        # Cargar datos y construir modelo
        script_dir   = os.path.dirname(os.path.abspath(__file__))
        ruta_archivo = os.path.join(script_dir, "..", "Data", "historial_loteria.xlsx")

        self.datos   = DatosLoteria(ruta_archivo)
        if not self.datos.cargar_historial():
            QMessageBox.critical(self, "Error", "No se pudo cargar el historial de lotería.")
            sys.exit(1)

        self.auditor = AuditorEstadistico(self.datos)
        self.sistema = SistemaMarkovLoteria(self.datos)
        self.sistema.construir_modelo_completo()

        self._worker = None  # referencia al thread activo

        self._setup_navegacion()
        self._setup_menu()
        self._setup_caso1()
        self._setup_caso2()
        self._setup_matrices()
        self._setup_registro()

        # Mostrar menú al arrancar
        self.stackPrincipal.setCurrentIndex(self.PAGE_MENU)

    # ── Navegación ────────────────────────────────────────────────────────────

    def _setup_navegacion(self):
        # Menú → páginas
        self.btnIrCaso1.clicked.connect(lambda: self.stackPrincipal.setCurrentIndex(self.PAGE_CASO1))
        self.btnIrCaso2.clicked.connect(lambda: self.stackPrincipal.setCurrentIndex(self.PAGE_CASO2))
        self.btnIrMatrices.clicked.connect(lambda: self._ir_matrices())
        self.btnIrRegistro.clicked.connect(lambda: self.stackPrincipal.setCurrentIndex(self.PAGE_REGISTRO))

        # Volver → menú
        self.btnVolverCaso1.clicked.connect(lambda: self.stackPrincipal.setCurrentIndex(self.PAGE_MENU))
        self.btnVolverCaso2.clicked.connect(lambda: self.stackPrincipal.setCurrentIndex(self.PAGE_MENU))
        self.btnVolverMatrices.clicked.connect(lambda: self.stackPrincipal.setCurrentIndex(self.PAGE_MENU))
        self.btnVolverRegistro.clicked.connect(lambda: self.stackPrincipal.setCurrentIndex(self.PAGE_MENU))

    # ── Menú principal ────────────────────────────────────────────────────────

    def _setup_menu(self):
        self._actualizar_condicion_inicial()

    def _actualizar_condicion_inicial(self):
        ci = self.datos.get_condicion_inicial()
        self.lblCondicionInicial.setText("".join(map(str, ci)))

    # ── CASO 1: Número más probable ───────────────────────────────────────────

    def _setup_caso1(self):
        self.btnCalcularCaso1.clicked.connect(self._calcular_caso1)

    def _calcular_caso1(self):
        self.btnCalcularCaso1.setEnabled(False)
        self.btnCalcularCaso1.setText("Calculando…")
        k = self.spinKCaso1.value()
        self._worker = WorkerPrediccion(self.sistema, "caso1", k)
        self._worker.resultado.connect(self._mostrar_caso1)
        self._worker.error.connect(self._error_calculo)
        self._worker.start()

    def _mostrar_caso1(self, res):
        self.btnCalcularCaso1.setEnabled(True)
        self.btnCalcularCaso1.setText("Calcular Predicción")

        numero  = res["numero"]
        prob    = res["probabilidad_conjunta"]
        detalle = res["detalle"]

        self.lblNumeroCaso1.setText("".join(map(str, numero)))
        self.lblProbConjCaso1.setText(f"Probabilidad conjunta: {float(prob):.8f}")

        # Detalle centenas
        d = detalle["centenas"]
        self.lblDigitoCentenas1.setText(str(d["digito"]))
        empate = f"  (empate: {d['empates']})" if d["empates"] else ""
        self.lblProbCentenas1.setText(f"p = {float(d['probabilidad']):.6f}{empate}")

        # Detalle decenas
        d = detalle["decenas"]
        self.lblDigitoDecenas1.setText(str(d["digito"]))
        empate = f"  (empate: {d['empates']})" if d["empates"] else ""
        self.lblProbDecenas1.setText(f"p = {float(d['probabilidad']):.6f}{empate}")

        # Detalle unidades
        d = detalle["unidades"]
        self.lblDigitoUnidades1.setText(str(d["digito"]))
        empate = f"  (empate: {d['empates']})" if d["empates"] else ""
        self.lblProbUnidades1.setText(f"p = {float(d['probabilidad']):.6f}{empate}")

    # ── CASO 2: Probabilidad de un número específico ──────────────────────────

    def _setup_caso2(self):
        self.lineEditNumero.setValidator(QIntValidator(0, 999, self))
        self.btnCalcularCaso2.clicked.connect(self._calcular_caso2)

    def _calcular_caso2(self):
        texto = self.lineEditNumero.text().strip()
        if len(texto) != 3:
            QMessageBox.warning(self, "Entrada inválida",
                                "Ingresa exactamente 3 dígitos (ej: 521).\n"
                                "Usa ceros a la izquierda si es necesario (ej: 042).")
            return
        c, d, u = int(texto[0]), int(texto[1]), int(texto[2])
        numero = (c, d, u)
        k = self.spinKCaso2.value()

        self.btnCalcularCaso2.setEnabled(False)
        self.btnCalcularCaso2.setText("Calculando…")

        self._worker = WorkerPrediccion(self.sistema, "caso2", k, numero)
        self._worker.resultado.connect(self._mostrar_caso2)
        self._worker.error.connect(self._error_calculo)
        self._worker.start()

    def _mostrar_caso2(self, res):
        self.btnCalcularCaso2.setEnabled(True)
        self.btnCalcularCaso2.setText("Consultar Probabilidad")

        prob    = res["probabilidad_conjunta"]
        detalle = res["detalle"]
        numero  = res["numero"]

        self.lblProbConjCaso2.setText(f"{float(prob):.8f}")
        self.lblInfoCaso2.setText(
            f"Para el número {''.join(map(str, numero))}  ·  k = {self.spinKCaso2.value()} días"
        )

        for pos, lbl_dig, lbl_prob in [
            ("centenas", self.lblDigitoCentenas2, self.lblProbCentenas2),
            ("decenas",  self.lblDigitoDecenas2,  self.lblProbDecenas2),
            ("unidades", self.lblDigitoUnidades2,  self.lblProbUnidades2),
        ]:
            d = detalle[pos]
            lbl_dig.setText(str(d["digito"]))
            lbl_prob.setText(f"p = {float(d['probabilidad']):.6f}")

    # ── Matrices de Transición ────────────────────────────────────────────────

    def _ir_matrices(self):
        self._llenar_matrices()
        self.stackPrincipal.setCurrentIndex(self.PAGE_MATRICES)

    def _setup_matrices(self):
        # Tabs de selección
        self.btnTabCentenas.clicked.connect(lambda: self._cambiar_tab_matriz(0))
        self.btnTabDecenas.clicked.connect(lambda:  self._cambiar_tab_matriz(1))
        self.btnTabUnidades.clicked.connect(lambda: self._cambiar_tab_matriz(2))

        # Headers de tablas
        for tabla in [self.tablaCentenas, self.tablaDecenas, self.tablaUnidades]:
            tabla.setHorizontalHeaderLabels([str(j) for j in range(10)])
            tabla.setVerticalHeaderLabels([str(j) for j in range(10)])
            tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            tabla.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def _llenar_matrices(self):
        config = [
            ("centenas", self.tablaCentenas,  "#4F8EF7"),
            ("decenas",  self.tablaDecenas,   "#A78BFA"),
            ("unidades", self.tablaUnidades,  "#34D399"),
        ]
        for pos, tabla, color_alto in config:
            matriz = self.sistema._matrices_transicion.get(pos)
            if not matriz:
                continue
            for row in range(10):
                for col in range(10):
                    val  = float(matriz[row][col])
                    item = QTableWidgetItem(f"{val:.4f}")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if val >= 0.20:
                        item.setForeground(QColor(color_alto))
                        f = item.font(); f.setBold(True); item.setFont(f)
                    elif val >= 0.10:
                        item.setForeground(QColor("#E2E8F0"))
                    else:
                        item.setForeground(QColor("#64748B"))
                    tabla.setItem(row, col, item)

    def _cambiar_tab_matriz(self, idx):
        self.stackMatrices.setCurrentIndex(idx)
        btns   = [self.btnTabCentenas, self.btnTabDecenas, self.btnTabUnidades]
        colors = ["#4F8EF7", "#A78BFA", "#34D399"]
        for i, (btn, color) in enumerate(zip(btns, colors)):
            btn.setChecked(i == idx)

    # ── Registro de nuevo sorteo ──────────────────────────────────────────────

    def _setup_registro(self):
        self.btnRegistrar.clicked.connect(self._registrar_sorteo)

    def _registrar_sorteo(self):
        c = self.spinCentena.value()
        d = self.spinDecena.value()
        u = self.spinUnidad.value()
        try:
            self.datos.set_nuevo_registro(c, d, u)
            self.sistema.construir_modelo_completo()
            ci = self.datos.get_condicion_inicial()
            self.textEditLog.append(
                f"✓  Registrado: {c}{d}{u}  |  Nuevo estado inicial: {''.join(map(str, ci))}  |  Modelo actualizado."
            )
            self._actualizar_condicion_inicial()
            self.statusbar.showMessage(f"Sorteo {c}{d}{u} registrado correctamente.", 4000)
        except Exception as e:
            self.textEditLog.append(f"✗  Error: {e}")

    # ── Error genérico de cálculo ─────────────────────────────────────────────

    def _error_calculo(self, msg):
        for btn_text, btn in [
            ("Calcular Predicción",    self.btnCalcularCaso1),
            ("Consultar Probabilidad", self.btnCalcularCaso2),
        ]:
            btn.setEnabled(True)
            btn.setText(btn_text)
        QMessageBox.critical(self, "Error en el cálculo", msg)


# ── Punto de entrada ─────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Predictor Lotería Markov")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,        QColor("#0D0F1A"))
    palette.setColor(QPalette.ColorRole.WindowText,    QColor("#E2E8F0"))
    palette.setColor(QPalette.ColorRole.Base,          QColor("#151827"))
    palette.setColor(QPalette.ColorRole.Text,          QColor("#E2E8F0"))
    palette.setColor(QPalette.ColorRole.Button,        QColor("#151827"))
    palette.setColor(QPalette.ColorRole.ButtonText,    QColor("#E2E8F0"))
    palette.setColor(QPalette.ColorRole.Highlight,     QColor("#4F8EF7"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    app.setPalette(palette)

    ventana = MainWindow()
    ventana.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
