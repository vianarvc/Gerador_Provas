# interface/worker_gerador.py

from PyQt5.QtCore import QObject, pyqtSignal
from motor_gerador.core import gerar_versoes_prova, gerar_prova_por_ids

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
            self.progress.emit(f"Iniciando geração de {self.num_versoes} versões...")
            
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

class GeradorPorIdWorker(QObject):
    """
    Um trabalhador que executa a geração de provas por IDs em uma thread separada
    para não congelar a interface. ESPECIALIZADA em lidar com rotação de grupos.
    """
    # Sinais que o trabalhador pode emitir
    finished = pyqtSignal(list)  # Emite a lista de versões geradas quando termina
    error = pyqtSignal(str)      # Emite uma mensagem de erro se algo der errado
    progress = pyqtSignal(str)   # Emite atualizações de progresso

    def __init__(self, lista_ids, num_versoes, opcoes_geracao):
        super().__init__()
        self.lista_ids = lista_ids
        self.num_versoes = num_versoes
        self.opcoes_geracao = opcoes_geracao
        self.is_running = True

    def run(self):
        """
        Este é o método que será executado na thread secundária.
        ESPECIALIZADO para geração por IDs com rotação de grupos.
        """
        try:
            self.progress.emit(f"Iniciando geração de {self.num_versoes} versões por IDs...")
            self.progress.emit(f"IDs das questões: {self.lista_ids}")
            
            # Chama a função ESPECÍFICA para geração por IDs (que aplica rotação de grupos)
            versoes_geradas = gerar_prova_por_ids(
                self.lista_ids, 
                self.num_versoes, 
                self.opcoes_geracao
            )
            
            if not versoes_geradas:
                raise Exception("O motor gerador não retornou nenhuma versão.")

            # ⭐⭐ CONVERTER a estrutura de dados para o formato esperado pelo PDF
            versoes_formatadas = self._formatar_versoes_para_pdf(versoes_geradas)
            
            # Se tudo deu certo, emite o sinal de 'finished' com os resultados
            self.finished.emit(versoes_formatadas)

        except Exception as e:
            # Se deu erro, emite o sinal de 'error'
            self.error.emit(str(e))

    def _formatar_versoes_para_pdf(self, versoes_geradas):
        """
        Converte a estrutura [ [questoes], [questoes] ] para 
        [ {'letra': 'A', 'questoes': [...]}, {'letra': 'B', 'questoes': [...]} ]
        E formata as questões para o template LaTeX
        """
        versoes_formatadas = []
        
        for i, versao in enumerate(versoes_geradas):
            letra_versao = chr(65 + i)  # A, B, C, ...
            
            # ⭐⭐ FORMATA CADA QUESTÃO DA VERSÃO
            questões_formatadas = []
            for questao in versao:
                questao_formatada = self._formatar_questao_para_pdf(questao)
                if questao_formatada:
                    questões_formatadas.append(questao_formatada)
            
            versao_formatada = {
                'letra': letra_versao,
                'questoes': questões_formatadas
            }
            versoes_formatadas.append(versao_formatada)
        
        return versoes_formatadas

    def _formatar_questao_para_pdf(self, questao):
        """
        Formata uma questão individual para o formato esperado pelo template LaTeX
        """
        try:
            questao_formatada = questao.copy()
            
            # ⭐⭐ CONVERTE alternativas_valores (lista) para alternativas (dicionário)
            if (questao.get('formato_questao') == 'Múltipla Escolha' and 
                'alternativas_valores' in questao and 
                'alternativas' not in questao):
                
                alternativas_valores = questao.get('alternativas_valores', [])
                alternativas_dict = {}
                letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                
                # Ordena as alternativas para ordem consistente
                alternativas_ordenadas = sorted(alternativas_valores)
                
                for idx, texto in enumerate(alternativas_ordenadas):
                    if idx < len(letras):
                        letra = letras[idx]
                        alternativas_dict[letra] = texto
                
                questao_formatada['alternativas'] = alternativas_dict
            
            return questao_formatada
            
        except Exception as e:
            print(f"Erro ao formatar questão para PDF: {e}")
            return None