# interface/log_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QApplication
from PyQt5.QtCore import Qt
from .custom_widgets import MeuTextEdit, EstilosApp

class LogDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Progresso da Geração")
        self.setModal(False)
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        self.log_text_edit = MeuTextEdit()
        self.log_text_edit.setReadOnly(True)
        layout.addWidget(self.log_text_edit)
        
        self.close_button = QPushButton("Fechar")
        self.close_button.setEnabled(False)
        self.close_button.clicked.connect(self.accept)
        
        EstilosApp.aplicar(
            botao=self.close_button,
            estilo="cinza",
            font_size=16,
            min_height=40
        )
        
        layout.addWidget(self.close_button)
        
        self.append_log("Iniciando a geração das provas...")

    def append_log(self, message):
        """Adiciona uma mensagem ao log"""
        self.log_text_edit.append(message)
        QApplication.processEvents()  # Força a interface a se atualizar

    '''def append_cache_stats(self):
        """Adiciona estatísticas do cache ao log de forma formatada"""
        from motor_gerador import get_cache_stats_formatted
        
        stats_text = get_cache_stats_formatted()
        self.append_log(stats_text)'''

    def finish(self, success=True):
        """Finaliza o processo, habilitando o botão de fechar"""
        if success:
            self.append_log("\n--- Processo Finalizado com Sucesso! ---")
            # Adiciona estatísticas do cache ao final com sucesso
            #self.append_cache_stats()
        else:
            self.append_log("\n--- Processo Interrompido por Erro ---")
        self.close_button.setEnabled(True)