# interface/configuracoes_dialog.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, 
    QDialogButtonBox, QMessageBox, QPushButton
)
from database import salvar_configuracoes, carregar_configuracoes
# --- MUDANÇA 1: Importa os widgets customizados ---
from .custom_widgets import MeuLineEdit, EstilosApp

class ConfiguracoesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações de Identificação")
        self.setMinimumWidth(950)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # --- MUDANÇA 2: Usa MeuLineEdit para os campos de entrada ---
        self.campos = {
            "sigla_curso": MeuLineEdit(),
            "nome_curso": MeuLineEdit(),
            "nome_professor": MeuLineEdit(),
            "nome_escola": MeuLineEdit(),
            "email_contato": MeuLineEdit()
        }

        form_layout.addRow("Sigla do Curso (Ex: CCTECC):", self.campos["sigla_curso"])
        form_layout.addRow("Nome Completo do Curso:", self.campos["nome_curso"])
        form_layout.addRow("Nome do Professor(a):", self.campos["nome_professor"])
        form_layout.addRow("Nome da Instituição/Campus:", self.campos["nome_escola"])
        form_layout.addRow("E-mail/Contato:", self.campos["email_contato"])
        
        layout.addLayout(form_layout)

        # Botões Salvar e Cancelar
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # --- MUDANÇA 3: Aplica o estilo customizado aos botões do QDialogButtonBox ---
        save_button = button_box.button(QDialogButtonBox.Save)
        save_button.setText("Salvar") # Opcional: muda o texto padrão
        EstilosApp.aplicar(save_button, estilo="verde", font_size=20, min_height=30, min_width=100)

        cancel_button = button_box.button(QDialogButtonBox.Cancel)
        cancel_button.setText("Cancelar") # Opcional: muda o texto padrão
        EstilosApp.aplicar(cancel_button, estilo="cinza", font_size=20, min_height=30, min_width=100)

        layout.addWidget(button_box)

        self.carregar_dados()

    def carregar_dados(self):
        """Carrega as configurações salvas e preenche os campos."""
        config = carregar_configuracoes()
        self.campos["sigla_curso"].setText(config.get("sigla_curso", ""))
        self.campos["nome_curso"].setText(config.get("nome_curso", ""))
        self.campos["nome_professor"].setText(config.get("nome_professor", ""))
        self.campos["nome_escola"].setText(config.get("nome_escola", ""))
        self.campos["email_contato"].setText(config.get("email_contato", ""))

    def accept(self):
        """
        Valida os campos. Se estiverem OK, salva e fecha.
        Se não, exibe um aviso e mantém a janela aberta.
        """
        dados_para_salvar = {
            "sigla_curso": self.campos["sigla_curso"].text().strip(),
            "nome_curso": self.campos["nome_curso"].text().strip(),
            "nome_professor": self.campos["nome_professor"].text().strip(),
            "nome_escola": self.campos["nome_escola"].text().strip(),
            "email_contato": self.campos["email_contato"].text().strip()
        }
        
        # --- VALIDAÇÃO ADICIONADA AQUI ---
        campos_obrigatorios = ["nome_professor", "nome_escola", "sigla_curso", "nome_curso"]
        for campo in campos_obrigatorios:
            if not dados_para_salvar.get(campo):
                QMessageBox.warning(self, "Campos Obrigatórios", 
                                    f"O campo '{campo.replace('_', ' ').title()}' é obrigatório. "
                                    "Por favor, preencha todos os campos.")
                return # Impede o salvamento e o fechamento da janela
        # --- FIM DA VALIDAÇÃO ---

        # Se a validação passou, o código continua para salvar e fechar
        salvar_configuracoes(dados_para_salvar)
        QMessageBox.information(self, "Sucesso", "Configurações salvas!")
        super().accept() # Chama o método original do QDialog para fechar a janela