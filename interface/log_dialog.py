# interface/log_dialog.py

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QApplication
from PyQt5.QtCore import Qt

class LogDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Progresso da Geração")
        self.setModal(False) # Permite interagir com a janela principal (se necessário)
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        layout.addWidget(self.log_text_edit)
        
        self.close_button = QPushButton("Fechar")
        self.close_button.setEnabled(False) # Começa desabilitado
        self.close_button.clicked.connect(self.accept)
        layout.addWidget(self.close_button)
        
        self.append_log("Iniciando a geração das provas...")

    def append_log(self, message):
        """ Adiciona uma mensagem ao log """
        self.log_text_edit.append(message)
        QApplication.processEvents() # Força a interface a se atualizar

    def finish(self, success=True):
        """ Finaliza o processo, habilitando o botão de fechar """
        if success:
            self.append_log("\n--- Processo Finalizado com Sucesso! ---")
        else:
            self.append_log("\n--- Processo Interrompido por Erro ---")
        self.close_button.setEnabled(True)