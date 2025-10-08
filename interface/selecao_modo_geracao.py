# interface/selecao_modo_geracao.py

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QDesktopWidget
from PyQt5.QtGui import QFont

# Importa as janelas que serão abertas
from .gerador_provas import GeradorProvasWindow
# A linha abaixo vai dar erro por enquanto, pois ainda não criamos o arquivo.
# Vamos descomentá-la na próxima etapa.
from .gerador_por_id import GeradorPorIdWindow

# interface/selecao_modo_geracao.py

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QDesktopWidget
from PyQt5.QtGui import QFont

class SelecaoModoGeracaoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecionar Modo de Geração")
        self.choice = None # Armazena a escolha do usuário
        self.resize(400, 250)

        layout = QVBoxLayout(self)
        # ... (seu layout atual está correto)
        label = QLabel("Como você deseja criar a prova?")
        label.setFont(QFont("Arial", 14)); layout.addWidget(label)
        btn_por_criterios = QPushButton("Gerar por Critérios (Sorteio)")
        btn_por_ids = QPushButton("Gerar por IDs (Pré-definido)")
        for btn in [btn_por_criterios, btn_por_ids]:
            btn.setFont(QFont("Arial", 12)); btn.setMinimumHeight(50); layout.addWidget(btn)
        # Fim do layout

        btn_por_criterios.clicked.connect(self.abrir_gerador_por_criterios)
        btn_por_ids.clicked.connect(self.abrir_gerador_por_ids)

        self._center()

    def abrir_gerador_por_criterios(self):
        self.choice = 'criterios'
        self.accept() # Fecha o diálogo e retorna um resultado "Aceito"

    def abrir_gerador_por_ids(self):
        self.choice = 'ids'
        self.accept() # Fecha o diálogo e retorna um resultado "Aceito"

    def _center(self):
        qr = self.frameGeometry(); cp = QDesktopWidget().availableGeometry().center(); qr.moveCenter(cp); self.move(qr.topLeft())