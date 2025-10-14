# interface/selecao_modo_geracao.py

# Importa as janelas que serão abertas
from PyQt5.QtWidgets import QDialog, QVBoxLayout
from .custom_widgets import MeuLabel, MeuBotao

class SelecaoModoGeracaoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selecionar Modo de Geração")
        self.choice = None # Armazena a escolha do usuário
        self.resize(400, 150)

        layout = QVBoxLayout(self)
        
        # --- MUDANÇA 2: Usa MeuLabel para o título ---
        # Usamos tags <b> para negrito e definimos um tamanho apropriado.
        label = MeuLabel("<b>Como você deseja criar a prova?</b>", tamanho=22)
        layout.addWidget(label)

        # --- MUDANÇA 3: Usa MeuBotao para as opções ---
        # O tipo "acao" já tem a cor azul e o hover definidos.
        btn_por_criterios = MeuBotao("Gerar por Critérios (Sorteio)", tipo="acao")
        btn_por_ids = MeuBotao("Gerar por IDs (Pré-definido)", tipo="acao")
        
        layout.addWidget(btn_por_criterios)
        layout.addWidget(btn_por_ids)

        btn_por_criterios.clicked.connect(self.abrir_gerador_por_criterios)
        btn_por_ids.clicked.connect(self.abrir_gerador_por_ids)

    def abrir_gerador_por_criterios(self):
        self.choice = 'criterios'
        self.accept()

    def abrir_gerador_por_ids(self):
        self.choice = 'ids'
        self.accept()