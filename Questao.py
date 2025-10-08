import tkinter as tk
from tkinter import ttk, messagebox
import random
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

class Questao:
    def __init__(self, tema, dificuldade, enunciado, linguagem_formula, parametros, alternativas, resposta_correta, imagem):
        self.tema = tema
        self.dificuldade = dificuldade
        self.enunciado = enunciado
        self.linguagem_formula = linguagem_formula
        self.parametros = parametros
        self.alternativas = alternativas
        self.resposta_correta = resposta_correta
        self.imagem = imagem

    '''def to_dict(self):
        return {
            "tema": self.tema,
            "dificuldade": self.dificuldade,
            "enunciado": self.enunciado,
            "linguagem": self.linguagem_formula,
            "parametros": self.parametros,
            "alternativa_a": self.alternativas[0],
            "alternativa_b": self.alternativas[1],
            "alternativa_c": self.alternativas[2],
            "alternativa_d": self.alternativas[3],
            "alternativa_e": self.alternativas[4],
            "correta": self.resposta_correta,        
            "imagem": self.imagem
        }'''
    
    def to_dict(self):
        dados = {
            "tema": self.tema,
            "dificuldade": self.dificuldade,
            "enunciado": self.enunciado,
            "imagem": self.imagem,
            "linguagem": self.linguagem_formula,
            "parametros": self.parametros,
            "resposta_correta": self.resposta_correta,
        }

        # Se alternativas for dict (com letras), usa diretamente
        if isinstance(self.alternativas, dict):
            for letra in ["A", "B", "C", "D", "E"]:
                chave = f"alternativa_{letra}"
                dados[chave] = self.alternativas.get(letra)
        else:
            # caso seja lista
            for i, letra in enumerate(["A", "B", "C", "D", "E"]):
                chave = f"alternativa_{letra}"
                dados[chave] = self.alternativas[i] if i < len(self.alternativas) else None

        #print(dados.to_dict())
        return {
        "tema": self.tema,
        "dificuldade": self.dificuldade,
        "enunciado": self.enunciado,
        "linguagem": self.linguagem_formula,
        "parametros": self.parametros,
        "alternativa_a": self.alternativas.get("A"),
        "alternativa_b": self.alternativas.get("B"),
        "alternativa_c": self.alternativas.get("C"),
        "alternativa_d": self.alternativas.get("D"),
        "alternativa_e": self.alternativas.get("E"),  # já vem no formato correto
        "resposta_correta": self.resposta_correta,
        "imagem": self.imagem
    }

    def gerar_variante(self, seed=None):
        random.seed(seed)
        v1 = random.randint(10, 100)
        v2 = random.randint(1, 10)
        variaveis = {"v1": v1, "v2": v2}

        enunciado = self.enunciado_base.format(**variaveis)
        alternativas = [alt.format(**variaveis) for alt in self.alternativas_base]
        correta = self.formula_resposta(**variaveis)

        return {
            "enunciado": enunciado,
            "alternativas": alternativas,
            "correta": correta
        }
