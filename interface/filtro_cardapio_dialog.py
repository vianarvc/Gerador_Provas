# interface/filtro_cardapio_dialog.py

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout
from database import obter_disciplinas, obter_temas, obter_disciplina_id_por_nome
# --- MUDANÇA 1: Importa os widgets customizados ---
from .custom_widgets import MeuLabel, MeuComboBox, MeuBotao

class FiltroCardapioDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filtros para o Cardápio")
        #self.setFixedSize(700, 300)

        self.disciplina_id = None
        self.tema = None

        layout = QVBoxLayout(self)

        # --- MUDANÇA 2: Usa os widgets customizados ---
        # Layout da Disciplina
        layout.addWidget(MeuLabel("<b>1. Escolha a Disciplina:</b>", tamanho=14))
        self.combo_disciplina = MeuComboBox()
        self.combo_disciplina.addItems(obter_disciplinas())
        layout.addWidget(self.combo_disciplina)

        # Layout do Tema
        layout.addWidget(MeuLabel("<b>2. Escolha o Tema:</b>", tamanho=14))
        self.combo_tema = MeuComboBox()
        layout.addWidget(self.combo_tema)

        #layout.addStretch()
        layout.addSpacing(20)

        # Botões OK e Cancelar
        botoes_layout = QHBoxLayout()
        botoes_layout.addStretch()
        self.btn_cancelar = MeuBotao("Cancelar", tipo="voltar")
        self.btn_ok = MeuBotao("🚀 Gerar Cardápio", tipo="principal")
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