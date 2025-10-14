# interface/MenuInicial.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from .custom_widgets import EstilosApp

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
        
        # Layout principal
        layout_principal = QVBoxLayout(self)
        layout_principal.setAlignment(Qt.AlignCenter)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(10)

        # Título
        titulo = QLabel("Gerador de Provas")
        titulo.setObjectName("TituloMenu") 
        layout_principal.addWidget(titulo)
        
        # Botões do menu como atributos da classe
        self.btn_visualizar = QPushButton("Banco de Questões")
        self.btn_cadastrar = QPushButton("Cadastrar Questão")
        self.btn_cardapio = QPushButton("Gerar Cardápio")
        self.btn_gerar = QPushButton("Gerar Prova")

        for btn in [self.btn_visualizar, self.btn_cadastrar, self.btn_cardapio, self.btn_gerar]:
            layout_principal.addWidget(btn)
            # Aplica estilo geral para todos os botões
            EstilosApp.aplicar(btn)  # Pode deixar font_size e min_height default

        # Se necessário, sobrescreve tamanho ou cor individual
        EstilosApp.aplicar(self.btn_cadastrar, estilo="azul", font_size=26, min_height=45)
        EstilosApp.aplicar(self.btn_gerar, estilo="verde", font_size=26, min_height=45)

        # Conecta os cliques dos botões para emitir sinais
        self.btn_visualizar.clicked.connect(self.visualizar_questoes_pressed.emit)
        self.btn_cadastrar.clicked.connect(self.cadastrar_questao_pressed.emit)
        self.btn_cardapio.clicked.connect(self.gerar_cardapio_pressed.emit)
        self.btn_gerar.clicked.connect(self.gerar_prova_pressed.emit)
        
        # Aplica estilos gerais do widget (ex.: fundo, fonte do título)
        self._aplicar_estilos()


    def sizeHint(self):
        """Informa à MainWindow qual o tamanho ideal desta tela."""
        return QSize(480, 400)

    '''def _aplicar_estilos(self):
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
            padding: 12px 5px;
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
        self.setStyleSheet(style)'''
    
    def _aplicar_estilos(self):
        """Aplica estilo do menu inicial."""
        style = """
        #TituloMenu {
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50; 
            margin-bottom: 28px;
            padding-bottom: 5px;
            border-bottom: 2px solid #3498db; 
        }
        """
        self.setStyleSheet(style)

        # Aplicar estilo aos botões
        EstilosApp.aplicar(self.btn_cadastrar, estilo="azul", font_size=26, min_height=45)
        EstilosApp.aplicar(self.btn_visualizar, estilo="azul", font_size=26, min_height=45)
        EstilosApp.aplicar(self.btn_cardapio, estilo="azul", font_size=26, min_height=45)
        EstilosApp.aplicar(self.btn_gerar, estilo="azul", font_size=26, min_height=45)