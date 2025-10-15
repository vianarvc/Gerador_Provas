# interface/worker_gerador.py

from PyQt5.QtCore import QObject, pyqtSignal
from motor_gerador import gerar_versoes_prova

class GeradorWorker(QObject):
    """
    Um trabalhador que executa a geração de provas em uma thread separada
    para não congelar a interface.
    """
    # Sinais que o trabalhador pode emitir
    finished = pyqtSignal(list)  # Emite a lista de versões geradas quando termina
    error = pyqtSignal(str)      # Emite uma mensagem de erro se algo der errado
    progress = pyqtSignal(str)   # Emite atualizações de progresso (opcional, mas bom ter)

    def __init__(self, questoes_base, num_versoes, opcoes_geracao):
        super().__init__()
        self.questoes_base = questoes_base
        self.num_versoes = num_versoes
        self.opcoes_geracao = opcoes_geracao
        self.is_running = True

    def run(self):
        """
        Este é o método que será executado na thread secundária.
        """
        try:
            # Chama a função pesada
            versoes_geradas = gerar_versoes_prova(
                self.questoes_base, 
                self.num_versoes, 
                self.opcoes_geracao
            )
            
            if not versoes_geradas:
                raise Exception("O motor gerador não retornou nenhuma versão.")

            # Se tudo deu certo, emite o sinal de 'finished' com os resultados
            self.finished.emit(versoes_geradas)

        except Exception as e:
            # Se deu erro, emite o sinal de 'error'
            self.error.emit(str(e))