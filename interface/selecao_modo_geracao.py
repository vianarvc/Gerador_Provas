# interface/selecao_modo_geracao.py

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QDesktopWidget
from PyQt5.QtGui import QFont

# Importa as janelas que serão abertas
from .gerador_provas import GeradorProvasScreen as GeradorProvasWindow
# A linha abaixo vai dar erro por enquanto, pois ainda não criamos o arquivo.
# Vamos descomentá-la na próxima etapa.
from .gerador_por_id import GeradorPorIdScreen as GeradorPorIdWindow

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
        
        # --- MUDANÇA 1: Adicionar objectName e remover setFont ---
        label = QLabel("Como você deseja criar a prova?")
        label.setObjectName("TituloDialogo")
        layout.addWidget(label)

        # --- MUDANÇA 2: Remover setFont e setMinimumHeight ---
        btn_por_criterios = QPushButton("Gerar por Critérios (Sorteio)")
        btn_por_ids = QPushButton("Gerar por IDs (Pré-definido)")
        
        layout.addWidget(btn_por_criterios)
        layout.addWidget(btn_por_ids)

        btn_por_criterios.clicked.connect(self.abrir_gerador_por_criterios)
        btn_por_ids.clicked.connect(self.abrir_gerador_por_ids)

        # --- MUDANÇA 3: Chamar o novo método de estilos ---
        self._aplicar_estilos()
        self._center()

    def abrir_gerador_por_criterios(self):
        self.choice = 'criterios'
        self.accept() # Fecha o diálogo e retorna um resultado "Aceito"

    def abrir_gerador_por_ids(self):
        self.choice = 'ids'
        self.accept() # Fecha o diálogo e retorna um resultado "Aceito"

    def _center(self):
        qr = self.frameGeometry(); cp = QDesktopWidget().availableGeometry().center(); qr.moveCenter(cp); self.move(qr.topLeft())

    def _aplicar_estilos(self):
        style = """
            QDialog {
                background-color: #f7f7f7;
            }

            #TituloDialogo {
                font-size: 26px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 15px;
            }

            QPushButton {
                background-color: #3498db; 
                color: white;
                border: none;
                border-radius: 8px; 
                padding: 12px;
                font-size: 22px; 
                font-weight: bold;
                min-height: 40px;
            }

            QPushButton:hover {
                background-color: #2980b9;
            }
            
            QPushButton:pressed {
                background-color: #1a5276;
            }
        """
        self.setStyleSheet(style)