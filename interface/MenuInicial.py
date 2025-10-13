# interface/MenuInicial.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt, QSize, pyqtSignal

# A classe agora herda de QWidget para ser uma "tela" e não uma janela
class MenuInicialWindow(QWidget):
    # Sinais para comunicação com a MainWindow
    visualizar_questoes_pressed = pyqtSignal()
    cadastrar_questao_pressed = pyqtSignal()
    gerar_cardapio_pressed = pyqtSignal()
    gerar_prova_pressed = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Menu Principal")
        
        layout_principal = QVBoxLayout(self)
        layout_principal.setAlignment(Qt.AlignCenter) 
        
        # Margens e espaçamento ajustados para o tamanho correto de 400x350
        layout_principal.setContentsMargins(40, 30, 40, 30)
        layout_principal.setSpacing(10)

        # Título
        titulo = QLabel("Gerador de Provas")
        titulo.setObjectName("TituloMenu") 
        layout_principal.addWidget(titulo)
        
        # Botões do menu
        btn_visualizar = QPushButton("Banco de Questões")
        btn_cadastrar = QPushButton("Cadastrar Questão")
        btn_cardapio = QPushButton("Gerar Cardápio")
        btn_gerar = QPushButton("Gerar Prova")

        for btn in [btn_visualizar, btn_cadastrar, btn_cardapio, btn_gerar]:
            layout_principal.addWidget(btn)

        # Conecta os cliques dos botões para emitir os sinais
        btn_visualizar.clicked.connect(self.visualizar_questoes_pressed.emit)
        btn_cadastrar.clicked.connect(self.cadastrar_questao_pressed.emit)
        btn_cardapio.clicked.connect(self.gerar_cardapio_pressed.emit)
        btn_gerar.clicked.connect(self.gerar_prova_pressed.emit)
        
        self._aplicar_estilos()

    def sizeHint(self):
        """Informa à MainWindow qual o tamanho ideal desta tela."""
        return QSize(200, 350)

    def _aplicar_estilos(self):
        """Define e aplica o QSS para o estilo do menu original."""
        style = """
        #TituloMenu {
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50; 
            margin-bottom: 28px;
            padding-bottom: 5px;
            border-bottom: 2px solid #3498db; 
        }

        QPushButton {
            background-color: #3498db; 
            color: white;
            border: none;
            border-radius: 8px; 
            padding: 20px;
            font-size: 26px; 
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #2980b9;
        }
        
        QPushButton:pressed {
            background-color: #1a5276;
        }
        """
        self.setStyleSheet(style)