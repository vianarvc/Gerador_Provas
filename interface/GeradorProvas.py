import tkinter as tk
from tkinter import ttk, messagebox
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from BancoQuestoes import BancoQuestoes
from Questao import Questao


class AplicacaoGeradorProvas(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gerador de Provas")
        self.geometry("600x500")

        self.banco = BancoQuestoes()
        self.temas = ["Circuitos", "Instalações", "Máquinas"]
        self.inicializar_banco()

        self.frame_configuracao()

    def inicializar_banco(self):
        # Exemplo: adiciona uma questão para teste
        self.banco.adicionar_questao(Questao(
            tema="Circuitos",
            dificuldade="Fácil",
            enunciado="Calcule a corrente para uma resistência de {v1} Ohms e tensão de {v2} Volts.",
            alternativas=["{v2}/{v1}", "{v1}/{v2}", "{v2}+{v1}", "{v2}-{v1}"],
            formula_resposta=lambda v1, v2: round(v2 / v1, 2)
        ))
        # Você pode adicionar mais questões com temas e dificuldades variados

    def frame_configuracao(self):
        self.frame = ttk.Frame(self)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(self.frame, text="Número de versões da prova:").pack(anchor=tk.W)
        self.entry_versoes = ttk.Entry(self.frame)
        self.entry_versoes.pack(fill=tk.X)

        self.quantidades = {}

        for tema in self.temas:
            tema_frame = ttk.LabelFrame(self.frame, text=tema)
            tema_frame.pack(fill=tk.X, pady=5)
            self.quantidades[tema] = {}

            for nivel in ["Fácil", "Média", "Difícil"]:
                row = ttk.Frame(tema_frame)
                row.pack(fill=tk.X, pady=2)
                ttk.Label(row, text=f"{nivel}:", width=10).pack(side=tk.LEFT)
                entry = ttk.Entry(row, width=5)
                entry.pack(side=tk.LEFT)
                self.quantidades[tema][nivel] = entry

        ttk.Button(self.frame, text="Pré-visualizar", command=self.pre_visualizar).pack(pady=10)

    def pre_visualizar(self):
        try:
            n_versoes = int(self.entry_versoes.get())
        except ValueError:
            messagebox.showerror("Erro", "Número de versões inválido")
            return

        criterios = {}
        for tema, niveis in self.quantidades.items():
            criterios[tema] = {}
            for nivel, entry in niveis.items():
                try:
                    criterios[tema][nivel] = int(entry.get())
                except ValueError:
                    criterios[tema][nivel] = 0

        self.exibir_pre_visualizacao(n_versoes, criterios)

    def exibir_pre_visualizacao(self, n_versoes, criterios):
        self.frame.pack_forget()
        self.frame_pre = ttk.Frame(self)
        self.frame_pre.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(self.frame_pre, text="Pré-visualização das versões").pack()

        self.versoes_geradas = []

        for v in range(n_versoes):
            ttk.Label(self.frame_pre, text=f"Versão {v+1}", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=5)
            text = tk.Text(self.frame_pre, height=10)
            text.pack(fill=tk.X)

            questoes = []
            for tema, niveis in criterios.items():
                for nivel, qtd in niveis.items():
                    selecionadas = self.banco.selecionar_questoes(tema, nivel, qtd)
                    for q in selecionadas:
                        variante = q.gerar_variante(seed=v)
                        questoes.append(variante)

            self.versoes_geradas.append(questoes)

            for i, q in enumerate(questoes):
                text.insert(tk.END, f"{i+1}) {q['enunciado']}\n")
                for letra, alt in zip("ABCD", q['alternativas']):
                    text.insert(tk.END, f"   {letra}) {alt}\n")
                text.insert(tk.END, "\n")

            text.config(state=tk.DISABLED)

        ttk.Button(self.frame_pre, text="Voltar", command=self.voltar_configuracao).pack(side=tk.LEFT, padx=10, pady=10)
        ttk.Button(self.frame_pre, text="Confirmar e gerar PDF", command=self.gerar_pdf).pack(side=tk.RIGHT, padx=10, pady=10)

    def voltar_configuracao(self):
        self.frame_pre.pack_forget()
        self.frame.pack(fill=tk.BOTH, expand=True)

    def gerar_pdf(self):
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm

        for idx, versao in enumerate(self.versoes_geradas):
            c = canvas.Canvas(f"Prova_V{idx+1}.pdf", pagesize=A4)
            width, height = A4

            # Capa simples
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(width/2, height - 3*cm, f"Prova - Versão {idx+1}")

            c.setFont("Helvetica", 12)
            y = height - 4*cm

            for i, q in enumerate(versao):
                texto = f"{i+1}) {q['enunciado']}"
                c.drawString(2*cm, y, texto)
                y -= 1*cm

                for letra, alt in zip("ABCD", q['alternativas']):
                    c.drawString(3*cm, y, f"{letra}) {alt}")
                    y -= 0.7*cm

                y -= 0.5*cm

                if y < 4*cm:
                    c.showPage()
                    y = height - 3*cm

            c.save()

        # Gabarito
        c = canvas.Canvas("Gabarito.pdf", pagesize=A4)
        width, height = A4
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width/2, height - 3*cm, "Gabarito das Provas")

        c.setFont("Helvetica", 12)
        y = height - 4*cm
        for idx, versao in enumerate(self.versoes_geradas):
            c.drawString(2*cm, y, f"Versão {idx+1}")
            y -= 1*cm

            for i, q in enumerate(versao):
                c.drawString(3*cm, y, f"{i+1}) Resposta correta: {q['correta']}")
                y -= 0.7*cm

                if y < 4*cm:
                    c.showPage()
                    y = height - 3*cm

            y -= 1*cm

        c.save()

        messagebox.showinfo("Sucesso", "PDFs das provas e gabarito gerados com sucesso!")