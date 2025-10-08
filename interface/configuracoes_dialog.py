# interface/configuracoes_dialog.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QPushButton, QDialogButtonBox, QMessageBox
)
from database import salvar_configuracoes, carregar_configuracoes

class ConfiguracoesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações de Identificação")
        self.setMinimumWidth(950)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.campos = {
            "sigla_curso": QLineEdit(),
            "nome_curso": QLineEdit(),
            "nome_professor": QLineEdit(),
            "nome_escola": QLineEdit(),
            "email_contato": QLineEdit()
        }

        form_layout.addRow("Sigla do Curso (Ex: CCTECC):", self.campos["sigla_curso"])
        form_layout.addRow("Nome Completo do Curso:", self.campos["nome_curso"])
        form_layout.addRow("Nome do Professor(a):", self.campos["nome_professor"])
        form_layout.addRow("Nome da Instituição/Campus:", self.campos["nome_escola"])
        form_layout.addRow("E-mail/Contato:", self.campos["email_contato"])
        
        layout.addLayout(form_layout)

        # Botões Salvar e Cancelar
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept) # Conecta ao salvamento
        button_box.rejected.connect(self.reject)
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
        """Salva os dados antes de fechar."""
        dados_para_salvar = {
            "sigla_curso": self.campos["sigla_curso"].text(),
            "nome_curso": self.campos["nome_curso"].text(),
            "nome_professor": self.campos["nome_professor"].text(),
            "nome_escola": self.campos["nome_escola"].text(),
            "email_contato": self.campos["email_contato"].text()
        }
        salvar_configuracoes(dados_para_salvar)
        QMessageBox.information(self, "Sucesso", "Configurações salvas!")
        super().accept()