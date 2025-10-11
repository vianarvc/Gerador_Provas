import random
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

class BancoQuestoes:
    def __init__(self):
        self.questoes = []

    def adicionar_questao(self, questao):
        self.questoes.append(questao)

    def selecionar_questoes(self, tema, dificuldade, quantidade):
        filtradas = [q for q in self.questoes if q.tema == tema and q.dificuldade == dificuldade]
        return random.sample(filtradas, min(quantidade, len(filtradas)))