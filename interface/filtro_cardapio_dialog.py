# interface/filtro_cardapio_dialog.py

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
from database import obter_disciplinas, obter_temas, obter_disciplina_id_por_nome

class FiltroCardapioDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filtros para o Cardápio")
        self.setFixedSize(600, 200)

        self.disciplina_id = None
        self.tema = None

        layout = QVBoxLayout(self)

        # Layout da Disciplina
        layout.addWidget(QLabel("<b>1. Escolha a Disciplina:</b>"))
        self.combo_disciplina = QComboBox()
        self.combo_disciplina.addItems(obter_disciplinas())
        layout.addWidget(self.combo_disciplina)

        # Layout do Tema
        layout.addWidget(QLabel("<b>2. Escolha o Tema:</b>"))
        self.combo_tema = QComboBox()
        layout.addWidget(self.combo_tema)

        layout.addStretch()

        # Botões OK e Cancelar
        botoes_layout = QHBoxLayout()
        botoes_layout.addStretch()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_ok = QPushButton("Gerar")
        self.btn_ok.setDefault(True)
        botoes_layout.addWidget(self.btn_cancelar)
        botoes_layout.addWidget(self.btn_ok)
        layout.addLayout(botoes_layout)

        # Conectar Sinais
        self.combo_disciplina.activated.connect(self._atualizar_temas)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancelar.clicked.connect(self.reject)

        # Carregar temas iniciais
        self._atualizar_temas()

    def _atualizar_temas(self):
        """Atualiza a lista de temas com base na disciplina selecionada."""
        disciplina_selecionada = self.combo_disciplina.currentText()
        id_disciplina = obter_disciplina_id_por_nome(disciplina_selecionada)
        
        temas = obter_temas(disciplina_id=id_disciplina)
        self.combo_tema.clear()
        self.combo_tema.addItems(temas)

    def accept(self):
        """Ao clicar OK, armazena os valores selecionados antes de fechar."""
        disciplina_selecionada = self.combo_disciplina.currentText()
        self.disciplina_id = obter_disciplina_id_por_nome(disciplina_selecionada)
        self.tema = self.combo_tema.currentText()
        super().accept()