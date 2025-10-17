# interface/cadastro_questao.py

import json, os, re
from textwrap import dedent
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, 
    QPushButton, QScrollArea, QMessageBox, QStackedWidget, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QGroupBox, QApplication,
    QToolButton, QRadioButton, QButtonGroup, QDesktopWidget, QGridLayout, QComboBox
)
from PyQt5.QtGui import QFont, QPixmap, QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from database import salvar_questao, obter_questao_por_id, atualizar_questao, obter_temas, obter_disciplinas, obter_disciplina_id_por_nome, salvar_disciplina, obter_disciplina_nome_por_id, obter_grupos_por_tema, atualizar_imagem_questao
import gerenciador_imagens
from .custom_widgets import (
    MeuBotao, MeuLineEdit, MeuComboBox, MeuGroupBox, MeuLabel, 
    MeuTableWidget, MeuToolButton, MeuCheckBox, MeuTextEdit, 
    MeuSpinBox, NoScrollSlider, NoScrollComboBox, MeuImagemPreviewLabel,
    )
import random
import io
import sys
from contextlib import redirect_stdout
from motor_gerador.core import _gerar_variante_questao
from constants import UNIDADES_PARA_DROPDOWN

class PythonHighlighter(QSyntaxHighlighter):
    """Classe para realçar a sintaxe Python dentro do QTextEdit."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlightingRules = []
        
        # Formato para Palavras-chave (Keywords)
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor("#B000B0"))  # Roxo
        keywordFormat.setFontWeight(QFont.Bold)
        keywords = ["and", "as", "assert", "break", "class", "continue", "def", "del", "elif", "else", "except", "False", "finally", "for", "from", "global", "if", "import", "in", "is", "lambda", "None", "nonlocal", "not", "or", "pass", "raise", "return", "True", "try", "while", "with", "yield"]
        self.highlightingRules += [(re.compile(r'\b' + kw + r'\b'), keywordFormat) for kw in keywords]
        
        # Formato para Nomes de Função
        functionFormat = QTextCharFormat()
        functionFormat.setForeground(QColor("#0000FF"))  # Azul
        self.highlightingRules.append((re.compile(r'\b[A-Za-z0-9_]+(?=\()'), functionFormat))
        
        # Formato para Strings (Aspas)
        quotationFormat = QTextCharFormat()
        quotationFormat.setForeground(QColor("#008000"))  # Verde
        self.highlightingRules.append((re.compile(r'".*?"'), quotationFormat))
        self.highlightingRules.append((re.compile(r"'.*?'"), quotationFormat))
        
        # Formato para Comentários
        singleLineCommentFormat = QTextCharFormat()
        singleLineCommentFormat.setForeground(QColor("#808080"))  # Cinza
        self.highlightingRules.append((re.compile(r'#[^\n]*'), singleLineCommentFormat))
    
    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            for match in re.finditer(pattern, text): 
                self.setFormat(match.start(), match.end() - match.start(), format)

class CadastroQuestaoScreen(QWidget):
    cadastro_concluido = pyqtSignal(int)  # ← AGORA COM PARÂMETRO
    voltar_pressed = pyqtSignal() # Sinal para avisar que quer cancelar/voltar
    questao_atualizada = pyqtSignal()

    def __init__(self, questao_id=None):
        super().__init__()
        self.questao_id = questao_id
        self.imagem_path = ""
        self.alternativas_inputs = {}
        self.simbolos_latex = {
            '-- Símbolos --': 
            '', 
            'Ω (Ohm)': 'Ω',
            'ω (frequência angular)': 'ω',
            'µ (micro)': 'µ', 
            'ρ (rho)': 'ρ', 
            'ε (epsilon)': 'ε', 
            'η (eta)': 'η',
            'Δ (delta)': 'Δ', 
            'α (alfa)': 'α', 
            'β (beta)': 'β', 
            'θ (theta)': 'θ',
            'π (pi)': 'π', 
            '° (graus)': '°', 
            '± (mais/menos)': '±', 
            '√ (raiz)': '√',
            'v (vetor)': '$\\vec{{}}$'
        }

        layout_principal = QVBoxLayout(self)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll.setWidget(content)
        
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout_principal.addWidget(scroll)

        self.titulo_label = MeuLabel("Cadastro de Questão")
        #self.titulo_label.setObjectName("TituloPrincipal")
        layout.addWidget(self.titulo_label)
        
        config_layout = QHBoxLayout()
        # --- MUDANÇA: Usa MeuCheckBox ---
        self.check_ativa = MeuCheckBox("Questão Ativa (incluir no sorteio de provas)")
        self.check_ativa.setChecked(True)
        config_layout.addWidget(self.check_ativa)
        config_layout.addStretch()
        layout.addLayout(config_layout)
        
        campos_layout = QHBoxLayout()
        
        col_esq = QVBoxLayout()
        col_esq.addWidget(QLabel("Formato da Questão:"))
        # --- MUDANÇA: Usa MeuComboBox ---
        self.formato_combo = MeuComboBox()
        self.formato_combo.addItems(["Múltipla Escolha", "Verdadeiro ou Falso", "Discursiva"])
        col_esq.addWidget(self.formato_combo)
        
        # --- MUDANÇA: Usa MeuCheckBox ---
        self.check_teorica = MeuCheckBox("Múltipla Escolha Teórica (alternativas fixas)")
        self.check_teorica.toggled.connect(self.atualizar_ui_formato)
        col_esq.addWidget(self.check_teorica)
        col_esq.addSpacing(10)
        
        col_esq.addWidget(QLabel("Disciplina:"))
        # --- MUDANÇA: Usa MeuComboBox ---
        self.disciplina_input = MeuComboBox()
        self.disciplina_input.setEditable(True)
        self.disciplina_input.addItems(obter_disciplinas())
        self.disciplina_input.lineEdit().setPlaceholderText("Selecione ou digite uma nova disciplina")
        col_esq.addWidget(self.disciplina_input)
        col_esq.addStretch(1)
        
        col_dir = QVBoxLayout()
        col_dir.addWidget(QLabel("Dificuldade:"))
        # --- MUDANÇA: Usa MeuComboBox ---
        self.dificuldade_combo = MeuComboBox()
        self.dificuldade_combo.addItems(["Fácil", "Média", "Difícil"])
        col_dir.addWidget(self.dificuldade_combo)
        col_dir.addSpacing(20)
        col_dir.addStretch(1)

        col_dir.addWidget(QLabel("Tema:"))
        # --- MUDANÇA: Usa MeuComboBox ---
        self.tema_input = MeuComboBox()
        self.tema_input.setEditable(True)
        self.tema_input.setInsertPolicy(QComboBox.NoInsert)
        self.tema_input.lineEdit().setPlaceholderText("Selecione ou digite um novo tema")
        col_dir.addWidget(self.tema_input)

        self.grupo_label = QLabel("Grupo (opcional):")
        # --- MUDANÇA: Usa MeuLineEdit ---
        self.grupo_input = MeuComboBox()
        self.grupo_input.setEditable(True)
        self.grupo_input.setInsertPolicy(QComboBox.NoInsert)
        self.grupo_input.lineEdit().setPlaceholderText("Ex: CONCEITO-LEI-OHM")
        col_dir.addWidget(self.grupo_label)
        col_dir.addWidget(self.grupo_input)
        
        campos_layout.addLayout(col_esq)
        campos_layout.addSpacing(30)
        campos_layout.addLayout(col_dir)
        layout.addLayout(campos_layout)
        layout.addSpacing(15)
        layout.addWidget(QLabel("Fonte da Questão (opcional):"))
        # --- MUDANÇA: Usa MeuLineEdit ---
        self.fonte_input = MeuLineEdit()
        self.fonte_input.setPlaceholderText("Ex: Livro X, Ed. Y, p. 123")
        layout.addWidget(self.fonte_input)
        
        layout.addWidget(QLabel("Enunciado da Questão (Comandos LaTeX):"))

        toolbar_enunciado = QHBoxLayout()
        btn_bold = self._criar_botao_formatacao("B", self.aplicar_latex_bold, "Negrito (\\textbf{})")
        btn_italic = self._criar_botao_formatacao("I", self.aplicar_latex_italic, "Itálico (\\textit{})")
        btn_underline = self._criar_botao_formatacao("U", self.aplicar_latex_underline, "Sublinhado (\\underline{})")
        btn_superscript = self._criar_botao_formatacao("x²", self.aplicar_latex_superscript, "Sobrescrito ($^{})")
        btn_subscript = self._criar_botao_formatacao("x₂", self.aplicar_latex_subscript, "Subscrito ($_{})")
        toolbar_enunciado.addWidget(btn_bold); toolbar_enunciado.addWidget(btn_italic); toolbar_enunciado.addWidget(btn_underline)
        toolbar_enunciado.addSpacing(10); toolbar_enunciado.addWidget(btn_superscript); toolbar_enunciado.addWidget(btn_subscript)
        toolbar_enunciado.addSpacing(20)
        
        # --- MUDANÇA: Usa MeuComboBox ---
        self.simbolo_combo = MeuComboBox()
        self.simbolo_combo.addItems(self.simbolos_latex.keys())
        self.simbolo_combo.activated[str].connect(self._inserir_simbolo)
        toolbar_enunciado.addWidget(self.simbolo_combo)
        toolbar_enunciado.addStretch()
        layout.addLayout(toolbar_enunciado)

        # --- MUDANÇA: Usa MeuTextEdit ---
        self.enunciado_input = MeuTextEdit()
        self.enunciado_input.setPlaceholderText("Use {variavel} para inserir valores...")
        self.enunciado_input.setFixedHeight(180) 
        layout.addWidget(self.enunciado_input)

        # --- MUDANÇA: Usa MeuGroupBox e MeuBotao ---
        group_imagem = MeuGroupBox("Imagem da Questão")
        layout_imagem = QVBoxLayout(group_imagem)
        botoes_imagem_layout = QHBoxLayout()
        btn_inserir_imagem = MeuBotao("📎 Inserir do Arquivo", tipo="acao")
        btn_colar_imagem = MeuBotao("📋 Colar Imagem", tipo="acao")
        btn_remover_imagem = MeuBotao("❌ Remover Imagem", tipo="remover")
        
        btn_inserir_imagem.clicked.connect(self._inserir_imagem_arquivo)
        btn_colar_imagem.clicked.connect(self._colar_imagem_clipboard)
        btn_remover_imagem.clicked.connect(self._remover_imagem)
        botoes_imagem_layout.addWidget(btn_inserir_imagem)
        botoes_imagem_layout.addWidget(btn_colar_imagem)
        botoes_imagem_layout.addWidget(btn_remover_imagem)
        layout_imagem.addLayout(botoes_imagem_layout)

        self.imagem_preview_label = MeuImagemPreviewLabel("Nenhuma imagem selecionada.")
        layout_imagem.addWidget(self.imagem_preview_label)

        slider_layout = QHBoxLayout()
        self.largura_label = QLabel("Largura na Prova: 40%")
        self.largura_slider = NoScrollSlider(Qt.Horizontal)
        self.largura_slider.setRange(10, 100); self.largura_slider.setValue(40)
        self.largura_slider.valueChanged.connect(lambda v: self.largura_label.setText(f"Largura na Prova: {v}%"))
        slider_layout.addWidget(self.largura_label)
        slider_layout.addWidget(self.largura_slider)
        layout_imagem.addLayout(slider_layout)
        layout.addWidget(group_imagem)

        # --- MUDANÇA: Usa MeuGroupBox e widgets customizados ---
        self.group_variaveis = MeuGroupBox("Geração de Variáveis e Resposta Numérica")
        layout_vars = QVBoxLayout(self.group_variaveis)
        layout_vars.setContentsMargins(10, 10, 10, 10); layout_vars.setSpacing(0)
        
        tipo_layout = QHBoxLayout()
        tipo_layout.addWidget(QLabel("Tipo de Geração de Variáveis:"))
        self.tipo_combo = MeuComboBox()
        self.tipo_combo.addItems(["Código (Python)", "Tabela (Visual)"])
        tipo_layout.addWidget(self.tipo_combo); tipo_layout.addStretch()
        layout_vars.addLayout(tipo_layout)

        self.stacked_widget = QStackedWidget()
        layout_vars.addWidget(self.stacked_widget)
        self.tipo_combo.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)

        widget_codigo = QWidget()
        layout_codigo = QVBoxLayout(widget_codigo)
        snippet_layout = QHBoxLayout()
        snippet_layout.addWidget(QLabel("<b>Inserir Snippet:</b>"))
        self.snippet_combo = MeuComboBox()
        self.snippet_combo.addItems(["-- Selecione --", "Sortear de Lista (choice)", "Definir Resposta (Simples)", "Definir Resposta Múltipla (Auto)"]) 
        self.snippet_combo.activated[str].connect(self._inserir_snippet)
        snippet_layout.addWidget(self.snippet_combo); snippet_layout.addStretch()
        layout_codigo.addLayout(snippet_layout)
        
        self.parametros_input = MeuTextEdit()
        self.parametros_input.setFont(QFont("Courier", 12))
        self.parametros_input.setPlaceholderText("# Defina suas variáveis...")
        self.parametros_input.setMinimumHeight(100)
        layout_codigo.addWidget(self.parametros_input)
        self.highlighter = PythonHighlighter(self.parametros_input.document())
        layout_codigo.addStretch() 
        self.stacked_widget.addWidget(widget_codigo)

        widget_tabela = QWidget()
        layout_tabela = QVBoxLayout(widget_tabela)
        layout_tabela.addWidget(QLabel("<b>Tabela de Variáveis:</b>"))
        self.tabela_vars = MeuTableWidget()
        self.tabela_vars.setColumnCount(3); self.tabela_vars.setHorizontalHeaderLabels(["Nome", "Tipo", "Valores"])
        self.tabela_vars.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela_vars.setMinimumHeight(150)
        layout_tabela.addWidget(self.tabela_vars)

        botoes_tabela_layout = QHBoxLayout()
        btn_add_var = MeuBotao("➕ Adicionar", tipo="acao")
        btn_rem_var = MeuBotao("➖ Remover", tipo="remover")
        btn_add_var.clicked.connect(self._adicionar_linha_tabela)
        btn_rem_var.clicked.connect(self._remover_linha_tabela)
        botoes_tabela_layout.addWidget(btn_add_var); botoes_tabela_layout.addWidget(btn_rem_var); botoes_tabela_layout.addStretch()
        layout_tabela.addLayout(botoes_tabela_layout)

        self.label_formula_resposta = QLabel("<b>Fórmula da Resposta (em Python):</b>")
        self.label_formula_resposta.setObjectName("label_formula_resposta") 
        layout_tabela.addWidget(self.label_formula_resposta)
        self.formula_resposta_input = MeuLineEdit()
        self.formula_resposta_input.setPlaceholderText("Use os Nomes das Variáveis. Ex: V / R")
        layout_tabela.addWidget(self.formula_resposta_input)

        self.check_tabela_modo1 = MeuCheckBox("Gerar Resposta Múltipla")
        layout_tabela.addWidget(self.check_tabela_modo1)
        
        self.group_modo1 = MeuGroupBox("Variáveis de Saída e Formatação")
        layout_modo1 = QVBoxLayout(self.group_modo1)
        layout_modo1.addWidget(QLabel("<b>Tabela de Variáveis de Saída (Cálculos):</b>"))
        self.tabela_saidas = MeuTableWidget()
        self.tabela_saidas.setColumnCount(2); self.tabela_saidas.setHorizontalHeaderLabels(["Nome da Saída", "Fórmula de Cálculo"])
        self.tabela_saidas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela_saidas.setMinimumHeight(100)
        layout_modo1.addWidget(self.tabela_saidas)
        
        botoes_saida_layout = QHBoxLayout()
        btn_add_saida = MeuBotao("➕ Adicionar Saída", tipo="acao")
        btn_rem_saida = MeuBotao("➖ Remover Saída", tipo="remover")
        btn_add_saida.clicked.connect(lambda: self.tabela_saidas.insertRow(self.tabela_saidas.rowCount()))
        btn_rem_saida.clicked.connect(lambda: self.tabela_saidas.removeRow(self.tabela_saidas.currentRow()))
        botoes_saida_layout.addWidget(btn_add_saida); botoes_saida_layout.addWidget(btn_rem_saida); botoes_saida_layout.addStretch()
        layout_modo1.addLayout(botoes_saida_layout)

        formato_layout = QHBoxLayout()
        formato_layout.addWidget(QLabel("<b>Formato da Alternativa:</b>"))
        self.formato_texto_input = MeuLineEdit()
        self.formato_texto_input.setPlaceholderText("Ex: I1={I1}A; I2={I2}A")
        formato_layout.addWidget(self.formato_texto_input)
        self.btn_gerar_sugestao = MeuBotao("Gerar Sugestão", tipo="acao")
        formato_layout.addWidget(self.btn_gerar_sugestao)
        layout_modo1.addLayout(formato_layout)
        layout_tabela.addWidget(self.group_modo1)
        self.group_modo1.setVisible(False)
        self.stacked_widget.addWidget(widget_tabela)

        unidade_layout = QHBoxLayout()
        self.label_unidade_input = QLabel("<b>Unidade de Medida da Resposta:</b>")
        unidade_layout.addWidget(self.label_unidade_input)
        self.unidade_input = MeuComboBox()
        self.unidade_input.setEditable(True); self.unidade_input.addItems(UNIDADES_PARA_DROPDOWN)
        self.unidade_input.lineEdit().setPlaceholderText("Selecione ou digite uma unidade")
        unidade_layout.addWidget(self.unidade_input); unidade_layout.addStretch()
        layout_vars.addLayout(unidade_layout)
        layout.addWidget(self.group_variaveis)

        self.group_alternativas = MeuGroupBox("Alternativas e Resposta")
        layout_alternativas = QVBoxLayout(self.group_alternativas)
        self.alternativas_stack = QStackedWidget()
        layout_alternativas.addWidget(self.alternativas_stack)

        page_me = QWidget()
        layout_me = QVBoxLayout(page_me)
        auto_layout = QHBoxLayout()
        self.check_gerar_auto = MeuCheckBox("Gerar alternativas numericamente")
        self.check_gerar_auto.toggled.connect(self.atualizar_ui_formato)
        self.check_permitir_negativos = MeuCheckBox("Permitir alternativas negativas")
        auto_layout.addWidget(self.check_gerar_auto); auto_layout.addWidget(self.check_permitir_negativos); auto_layout.addStretch()
        layout_me.addLayout(auto_layout)

        self.widget_alternativas_manuais = QWidget()
        layout_manuais = QVBoxLayout(self.widget_alternativas_manuais)
        layout_manuais.setSpacing(5)
        grid_alternativas = QWidget()
        grid_layout = QVBoxLayout(grid_alternativas)
        grid_layout.setSpacing(5)

        for i, letra in enumerate(["A", "B", "C", "D", "E"]):
            alt_layout_h = QHBoxLayout()
            lbl_letra = QLabel(f"{letra})"); lbl_letra.setFixedWidth(20)
            alt_layout_h.addWidget(lbl_letra)
            # --- MUDANÇA: Usa MeuLineEdit ---
            alternativa = MeuLineEdit()
            alternativa.setPlaceholderText(f"Conteúdo da alternativa {letra}")
            self.alternativas_inputs[letra] = alternativa
            alt_layout_h.addWidget(alternativa)
            grid_layout.addLayout(alt_layout_h)

        layout_manuais.addWidget(grid_alternativas)
        self.resposta_correta_widget = QWidget()
        resp_layout = QHBoxLayout(self.resposta_correta_widget)
        resp_layout.setContentsMargins(0, 10, 0, 0)
        resp_layout.addWidget(QLabel("Resposta Correta:"))
        # --- MUDANÇA: Usa MeuComboBox ---
        self.resposta_correta_combo = MeuComboBox()
        self.resposta_correta_combo.addItems(["A", "B", "C", "D", "E"]); self.resposta_correta_combo.setFixedWidth(50)
        resp_layout.addWidget(self.resposta_correta_combo); resp_layout.addStretch()
        layout_manuais.addWidget(self.resposta_correta_widget)
        layout_me.addWidget(self.widget_alternativas_manuais)
        self.alternativas_stack.addWidget(page_me)

        page_vf = QWidget()
        layout_vf = QVBoxLayout(page_vf)
        layout_vf.addWidget(QLabel("Resposta Correta:"))
        self.vf_verdadeiro_radio = QRadioButton("Verdadeiro"); self.vf_falso_radio = QRadioButton("Falso")
        self.vf_button_group = QButtonGroup(self); self.vf_button_group.addButton(self.vf_verdadeiro_radio); self.vf_button_group.addButton(self.vf_falso_radio)
        self.vf_verdadeiro_radio.setChecked(True)
        layout_vf.addWidget(self.vf_verdadeiro_radio); layout_vf.addWidget(self.vf_falso_radio); layout_vf.addStretch()
        self.alternativas_stack.addWidget(page_vf)

        page_disc = QWidget()
        layout_disc = QVBoxLayout(page_disc)
        layout_disc.addWidget(QLabel("Questões discursivas não possuem gabarito pré-definido..."))
        layout_disc.addStretch()
        self.alternativas_stack.addWidget(page_disc)
        layout.addWidget(self.group_alternativas)
        self.formato_combo.currentIndexChanged.connect(self.atualizar_ui_formato)

        # --- MUDANÇA FINAL: Usa MeuBotao para os botões principais ---
        #self.btn_voltar = MeuBotao("↩️ Voltar/Cancelar", tipo="voltar")
        self.btn_testar = MeuBotao("✔ Testar Código", tipo="testar")
        self.btn_salvar = MeuBotao("💾 Salvar Questão", tipo="principal")

        self.btn_salvar.clicked.connect(self.salvar_alterar_questao)
        #self.btn_voltar.clicked.connect(self.voltar_pressed.emit)
        self.btn_testar.clicked.connect(self._testar_codigo)

        botoes_layout = QGridLayout()
        #botoes_layout.addWidget(self.btn_voltar, 0, 0)
        botoes_layout.addWidget(self.btn_testar, 0, 0)
        botoes_layout.addWidget(self.btn_salvar, 0, 1)
        layout.addLayout(botoes_layout)

        self.disciplina_input.activated.connect(self._atualizar_lista_temas)
        self.tema_input.currentTextChanged.connect(self._atualizar_grupos_combo)
        self._atualizar_lista_temas()
        self.configurar_modo()
        self.atualizar_ui_formato()
        self.check_tabela_modo1.toggled.connect(self._atualizar_ui_tabela)
        self.btn_gerar_sugestao.clicked.connect(self._gerar_sugestao_formato)
        self.findChild(QLabel, "label_formula_resposta").setObjectName("label_formula_resposta")

    def _atualizar_ui_tabela(self):
        """Controla a visibilidade dos widgets do MODO 1 vs MODO 2 na aba Tabela."""
        is_modo1 = self.check_tabela_modo1.isChecked()
        self.group_modo1.setVisible(is_modo1)
        self.formula_resposta_input.setVisible(not is_modo1)
        # Opcional: Altera o label para clareza
        self.findChild(QLabel, "label_formula_resposta").setVisible(not is_modo1)


    def _gerar_sugestao_formato(self):
        """Lê a tabela de saídas e gera um formato de texto padrão."""
        nomes_saida = []
        for row in range(self.tabela_saidas.rowCount()):
            item = self.tabela_saidas.item(row, 0)
            if item and item.text():
                nome = item.text().strip()
                nomes_saida.append(f"{nome}={{{nome}}}")
        
        sugestao = "; ".join(nomes_saida)
        self.formato_texto_input.setText(sugestao)

    @staticmethod
    def converter_tabela_para_python_modo1(dados_tabela):
        """Converte os dados da Tabela (MODO 1) para um script Python complexo."""
        script_linhas = []

        # 1. Gera as linhas de random.choice para as ENTRADAS
        for var in dados_tabela.get("entradas", []):
            linha = f"{var['nome']} = random.choice([{var['valores']}])"
            script_linhas.append(linha)
        
        script_linhas.append("") # Linha em branco para separar

        # 2. Gera as linhas de cálculo para as SAÍDAS
        saidas_dict_keys = []
        for var in dados_tabela.get("saidas", []):
            linha = f"{var['nome']} = {var['formula']}"
            script_linhas.append(linha)
            saidas_dict_keys.append(f"'{var['nome']}': {var['nome']}")

        script_linhas.append("")

        # 3. Gera o dicionário final 'resposta_valor'
        formato_texto = dados_tabela.get("formato_texto", "")
        dict_keys_str = ", ".join(saidas_dict_keys)
        
        # Usar repr() no formato_texto é crucial para lidar com aspas e caracteres especiais
        linha_final = f"resposta_valor = {{'valores': {{{dict_keys_str}}}, 'formato_texto': {repr(formato_texto)}}}"
        script_linhas.append(linha_final)
        
        return "\n".join(script_linhas)

    @staticmethod
    def converter_tabela_para_python(dados_tabela):
        script_linhas = []
        
        # 1. Converte cada variável em uma linha de random.choice
        for var in dados_tabela.get("variaveis", []):
            nome_var = var.get("nome")
            valores_str = var.get("valores")
            
            if not nome_var or not valores_str:
                continue
                
            # Constrói a lista de valores para o random.choice
            # Isso assume que os valores são números separados por vírgula.
            # Adicione tratamento de erro se os valores puderem ser texto.
            lista_de_valores = f"[{valores_str}]"
            
            linha_codigo = f"{nome_var} = random.choice({lista_de_valores})"
            script_linhas.append(linha_codigo)
            
        # 2. Adiciona a linha da fórmula de resposta
        formula = dados_tabela.get("formula_resposta")
        if formula:
            script_linhas.append(f"resposta_valor = {formula}")
            
        # 3. Junta tudo em um único script
        return "\n".join(script_linhas)

    def _adicionar_linha_tabela(self):
        row = self.tabela_vars.rowCount()
        self.tabela_vars.insertRow(row)
        # Cria e insere o ComboBox customizado na tabela
        combo = NoScrollComboBox()
        combo.addItems([#"Intervalo Inteiro", 
                        #"Intervalo Decimal", 
                        "Lista de Valores"])
        self.tabela_vars.setCellWidget(row, 1, combo)

    def atualizar_ui_formato(self, *args, **kwargs):
        formato = self.formato_combo.currentText()
        self.alternativas_stack.setCurrentIndex(self.formato_combo.currentIndex())
        is_me = (formato == "Múltipla Escolha")
        is_teorica = self.check_teorica.isChecked()
        is_gerar_auto = self.check_gerar_auto.isChecked()
        
        # Lógica de visibilidade
        show_grupo = is_me and is_teorica
        self.grupo_label.setVisible(show_grupo)
        self.grupo_input.setVisible(show_grupo)
        self.check_teorica.setVisible(is_me)
        self.check_gerar_auto.setVisible(is_me and not is_teorica)
        self.check_permitir_negativos.setVisible(is_me and is_gerar_auto and not is_teorica)
        self.widget_alternativas_manuais.setDisabled(is_gerar_auto)
        
        # Títulos e estados de grupos
        self.group_alternativas.setTitle("Alternativas e Resposta" if is_me or formato == "Verdadeiro ou Falso" else "Alternativas (Não Aplicável)")
        self.group_variaveis.setDisabled(is_teorica and is_me)
        
        # Consistência de estado
        if not is_me or is_teorica:
            self.check_gerar_auto.setChecked(False)
        
        # Unidade de resposta
        if formato == "Discursiva":
            self.label_unidade_input.setVisible(False)
            self.unidade_input.setVisible(False)
        else:
            self.label_unidade_input.setVisible(True)
            self.unidade_input.setVisible(True)

        self.resposta_correta_widget.setVisible(is_me and not is_gerar_auto)

    def _atualizar_lista_temas(self):
        """
        Atualiza o ComboBox de temas com base na disciplina selecionada.
        """
        # Guarda o texto atual do tema para tentar restaurá-lo depois
        texto_tema_atual = self.tema_input.currentText()
        
        disciplina_nome = self.disciplina_input.currentText()
        
        # Busca o ID da disciplina (seu database.py já tem essa função)
        # A função obter_disciplina_id_por_nome retorna None se a disciplina não for encontrada ou for "Todas"
        disciplina_id = obter_disciplina_id_por_nome(disciplina_nome)
        
        # Busca os temas filtrados (seu database.py também já está pronto para isso)
        temas_filtrados = obter_temas(disciplina_id=disciplina_id)
        
        # Atualiza o ComboBox de temas
        self.tema_input.clear()
        self.tema_input.addItems(temas_filtrados)
        
        # Tenta restaurar a seleção anterior do tema, se ainda estiver na nova lista
        index = self.tema_input.findText(texto_tema_atual)
        if index != -1:
            self.tema_input.setCurrentIndex(index)
        else:
            # Se o tema não estiver na nova lista, simplesmente mantém o texto antigo no campo.
            # Como o ComboBox é editável, isso preserva a informação.
            self.tema_input.setCurrentText(texto_tema_atual)

    def _atualizar_grupos_combo(self):
        """
        Atualiza a combobox de grupos com base na disciplina e no tema selecionados.
        """
        # Salva o texto que o usuário pode estar digitando
        texto_atual = self.grupo_input.currentText()

        self.grupo_input.clear()

        disciplina_nome = self.disciplina_input.currentText()
        tema_selecionado = self.tema_input.currentText()

        disciplina_id = obter_disciplina_id_por_nome(disciplina_nome)

        # Só busca os grupos se uma disciplina e um tema válidos estiverem selecionados
        if disciplina_id and tema_selecionado:
            grupos = obter_grupos_por_tema(disciplina_id, tema_selecionado)
            if grupos:
                # Adiciona os grupos encontrados, desabilitando os sinais para evitar loops
                self.grupo_input.blockSignals(True)
                self.grupo_input.addItems(grupos)
                self.grupo_input.blockSignals(False)

        # Restaura o texto que o usuário estava digitando, caso ele não esteja na lista
        self.grupo_input.setCurrentText(texto_atual)

    def carregar_dados_questao(self):
        dados = obter_questao_por_id(self.questao_id)
        if not dados: return
        
        # --- ETAPA 1: Carrega todos os campos de texto e seleções simples ---
        self.check_ativa.setChecked(bool(dados.get("ativa", 1)))
        self._atualizar_grupos_combo()
        self.grupo_input.setCurrentText(dados.get("grupo", "")) # Use setCurrentText para QComboBox
        self.check_permitir_negativos.setChecked(bool(dados.get("permitir_negativos", 0)))
        
        formato = dados.get("formato_questao", "Múltipla Escolha")
        self.formato_combo.setCurrentText(formato)
        self.check_teorica.setChecked(bool(dados.get("is_teorica", 0)))
        
        disciplina_id = dados.get("disciplina_id")
        disciplina_nome = obter_disciplina_nome_por_id(disciplina_id)
        self.disciplina_input.setCurrentText(disciplina_nome)
        
        self._atualizar_lista_temas() # Atualiza a lista de temas com base na disciplina
        self.tema_input.setCurrentText(dados.get("tema", "")) # Agora define o tema

        self._atualizar_grupos_combo() # 1. Popula a lista de grupos
        self.grupo_input.setCurrentText(dados.get("grupo", ""))
        
        self.dificuldade_combo.setCurrentText(dados.get("dificuldade", "Fácil"))
        self.fonte_input.setText(dados.get("fonte", ""))
        
        # --- LINHA CORRIGIDA ---
        # Esta linha estava faltando na minha versão anterior
        self.enunciado_input.setPlainText(dados.get("enunciado", ""))
        
        self.unidade_input.setCurrentText(dados.get("unidade_resposta", ""))
        self.imagem_path = dados.get("imagem", "")
        self.largura_slider.setValue(dados.get("imagem_largura_percentual") or 50)
        self._atualizar_preview_imagem()
        
        # Carrega dados específicos do formato da questão (alternativas, V/F)
        if formato == "Múltipla Escolha":
            self.check_gerar_auto.setChecked(bool(dados.get("gerar_alternativas_auto", 0)))
            self.resposta_correta_combo.setCurrentText(dados.get("resposta_correta", "A"))
            for letra in ["A", "B", "C", "D", "E"]:
                self.alternativas_inputs[letra].setText(dados.get(f"alternativa_{letra.lower()}", ""))
        elif formato == "Verdadeiro ou Falso":
            if dados.get("resposta_correta") == "Verdadeiro":
                self.vf_verdadeiro_radio.setChecked(True)
            else:
                self.vf_falso_radio.setChecked(True)

        # --- ETAPA 2: Lógica de decisão para carregar os PARÂMETROS ---
        parametros_tabela_json = dados.get("parametros_tabela_json")

        if parametros_tabela_json:
            # A QUESTÃO FOI CRIADA NA TABELA!
            self.tipo_combo.setCurrentText("Tabela (Visual)")
            try:
                dados_tabela_salvos = json.loads(parametros_tabela_json)
                is_modo1 = dados_tabela_salvos.get("modo1", False)
                dados_originais = dados_tabela_salvos.get("dados", {})

                # Preenche a Tabela de Entradas
                self.tabela_vars.setRowCount(0)
                entradas = dados_originais.get("variaveis", []) or dados_originais.get("entradas", [])
                for var in entradas:
                    self._adicionar_linha_tabela()
                    row = self.tabela_vars.rowCount() - 1
                    self.tabela_vars.setItem(row, 0, QTableWidgetItem(var.get("nome")))
                    self.tabela_vars.cellWidget(row, 1).setCurrentText("Lista de Valores")
                    self.tabela_vars.setItem(row, 2, QTableWidgetItem(var.get("valores")))

                # Marca o checkbox MODO 1 e preenche os campos correspondentes
                self.check_tabela_modo1.setChecked(is_modo1)
                if is_modo1:
                    self.formato_texto_input.setText(dados_originais.get("formato_texto", ""))
                    self.tabela_saidas.setRowCount(0)
                    for var in dados_originais.get("saidas", []):
                        self.tabela_saidas.insertRow(self.tabela_saidas.rowCount())
                        row = self.tabela_saidas.rowCount() - 1
                        self.tabela_saidas.setItem(row, 0, QTableWidgetItem(var.get("nome")))
                        self.tabela_saidas.setItem(row, 1, QTableWidgetItem(var.get("formula")))
                else: # Modo 2
                    self.formula_resposta_input.setText(dados_originais.get("formula_resposta", ""))

            except (json.JSONDecodeError, AttributeError):
                 self.tipo_combo.setCurrentText("Código (Python)")
                 self.parametros_input.setPlainText(dados.get("parametros", "# Erro ao carregar dados da Tabela."))
        else:
            # É UMA QUESTÃO DE CÓDIGO "PURA" OU TEÓRICA
            self.tipo_combo.setCurrentText("Código (Python)")
            self.parametros_input.setPlainText(dados.get("parametros", ""))

        # --- ETAPA 3: Atualiza a visibilidade de todos os widgets ---
        self.atualizar_ui_formato()
        self._atualizar_ui_tabela()
    
    def salvar_alterar_questao(self):
        # --- ETAPA 1: Obter e validar a disciplina ---
        disciplina_nome = self.disciplina_input.currentText().strip()
        if not disciplina_nome:
            QMessageBox.warning(self, "Erro", "O campo Disciplina é obrigatório.")
            return
        disciplina_id = salvar_disciplina(disciplina_nome)

        # --- ETAPA 2: Coletar todos os outros dados da tela ---
        formato = self.formato_combo.currentText()
        is_teorica = self.check_teorica.isChecked() and formato == "Múltipla Escolha"
        
        parametros_finais = ""
        tipo_questao_final = ""
        parametros_tabela_json = None # <<< INICIALIZA A NOVA VARIÁVEL

        # --- ETAPA 3: LÓGICA DE CONVERSÃO E COLETA DOS PARÂMETROS ---
        if not is_teorica and formato != "Discursiva":
            tipo_geracao_selecionado = self.tipo_combo.currentText()
            
            if tipo_geracao_selecionado == "Código (Python)":
                parametros_finais = self.parametros_input.toPlainText().strip()
                tipo_questao_final = "Código (Python)"
                if not parametros_finais:
                    QMessageBox.warning(self, "Erro", "O bloco de Código (Python) não pode ser vazio.")
                    return

            elif tipo_geracao_selecionado == "Tabela (Visual)":
                try:
                    # Coleta das variáveis de ENTRADA (Tabela 1)
                    entradas = []
                    for row in range(self.tabela_vars.rowCount()):
                        # ... (lógica para ler a tabela de entradas)
                        nome = self.tabela_vars.item(row, 0).text().strip()
                        tipo_var = self.tabela_vars.cellWidget(row, 1).currentText()
                        valores = self.tabela_vars.item(row, 2).text().strip()
                        if not (nome and valores):
                            raise ValueError(f"A linha {row + 1} da Tabela de Entradas está incompleta.")
                        if tipo_var != "Lista de Valores":
                            raise ValueError("Para geração determinística, a Tabela de Entradas só suporta 'Lista de Valores'.")
                        entradas.append({"nome": nome, "valores": valores})
                    
                    is_modo1 = self.check_tabela_modo1.isChecked()
                    
                    if not is_modo1: # Modo 2 (Valor Único)
                        formula = self.formula_resposta_input.text().strip()
                        if not formula:
                            raise ValueError("A Fórmula da Resposta é obrigatória.")
                        
                        dados_para_converter = {"variaveis": entradas, "formula_resposta": formula}
                        parametros_finais = self.converter_tabela_para_python(dados_para_converter)

                        # --- NOVO: Salva a "origem" da tabela ---
                        parametros_tabela_json = json.dumps({"modo1": False, "dados": dados_para_converter})
                    
                    else: # Modo 1 (Múltiplas Respostas)
                        # Coleta das variáveis de SAÍDA (Tabela 2)
                        saidas = []
                        for row in range(self.tabela_saidas.rowCount()):
                            nome = self.tabela_saidas.item(row, 0).text().strip()
                            formula = self.tabela_saidas.item(row, 1).text().strip()
                            if not (nome and formula):
                                raise ValueError(f"A linha {row + 1} da Tabela de Saídas está incompleta.")
                            saidas.append({"nome": nome, "formula": formula})

                        formato_texto = self.formato_texto_input.text().strip()
                        if not saidas:
                            raise ValueError("A Tabela de Saídas não pode estar vazia no MODO 1.")
                        if not formato_texto:
                            raise ValueError("O Formato da Alternativa é obrigatório no MODO 1.")

                        dados_para_converter = {"entradas": entradas, "saidas": saidas, "formato_texto": formato_texto}
                        parametros_finais = self.converter_tabela_para_python_modo1(dados_para_converter)

                        # --- NOVO: Salva a "origem" da tabela ---
                        parametros_tabela_json = json.dumps({"modo1": True, "dados": dados_para_converter})

                    tipo_questao_final = "Código (Python)"

                except (ValueError, AttributeError) as e:
                    QMessageBox.warning(self, "Erro de Validação na Tabela", str(e))
                    return
        
        else: # Questão Teórica
            parametros_finais = ""
            tipo_questao_final = ""

        # --- ETAPA 4: Montar o dicionário final com todos os dados ---
        dados_questao = {
            "disciplina_id": disciplina_id,
            "tema": self.tema_input.currentText().strip(),
            "fonte": self.fonte_input.text().strip(),
            "ativa": int(self.check_ativa.isChecked()),
            "grupo": self.grupo_input.currentText().strip(),
            "formato_questao": formato,
            "dificuldade": self.dificuldade_combo.currentText(),
            "enunciado": self.enunciado_input.toPlainText().strip(),
            "unidade_resposta": self.unidade_input.currentText().strip(),
            "imagem": self.imagem_path,
            "imagem_largura_percentual": self.largura_slider.value(),
            "is_teorica": int(is_teorica),
            "gerar_alternativas_auto": int(self.check_gerar_auto.isChecked()),
            "permitir_negativos": int(self.check_permitir_negativos.isChecked()),
            "parametros": parametros_finais,
            "tipo_questao": tipo_questao_final,
            "parametros_tabela_json": parametros_tabela_json 
        }

        if formato == "Múltipla Escolha":
            dados_questao["resposta_correta"] = self.resposta_correta_combo.currentText()
            for letra, input_widget in self.alternativas_inputs.items():
                dados_questao[f"alternativa_{letra.lower()}"] = input_widget.text().strip()
        elif formato == "Verdadeiro ou Falso":
            dados_questao["resposta_correta"] = "Verdadeiro" if self.vf_verdadeiro_radio.isChecked() else "Falso"

        # --- ETAPA 5: Salvar ou Atualizar no Banco de Dados ---
        '''try:
            if self.questao_id:
                atualizar_questao(self.questao_id, dados_questao)
                QMessageBox.information(self, "Sucesso", "Questão atualizada com sucesso!")
                questao_id_salva = self.questao_id  # ← GUARDA O ID
            else:
                questao_id_salva = salvar_questao(dados_questao)  # ← CAPTURA O NOVO ID
                QMessageBox.information(self, "Sucesso", "Questão salva com sucesso!")
            
            # ⭐ MUDANÇA CRÍTICA: Emite o sinal com o ID da questão
            self.cadastro_concluido.emit(questao_id_salva)  # ← AGORA COM PARÂMETRO
            
        except Exception as e:
            QMessageBox.critical(self, "Erro no Banco de Dados", f"Não foi possível salvar a questão:\n{e}")'''
        
        # --- ETAPA 5: Salvar ou Atualizar no Banco de Dados ---
        # --- ETAPA 5: Salvar ou Atualizar no Banco de Dados ---
        try:
            # ✅ PRIMEIRO: Salva questão SEM imagem para obter ID real
            dados_sem_imagem = dados_questao.copy()
            dados_sem_imagem['imagem'] = ""
            
            if self.questao_id:
                atualizar_questao(self.questao_id, dados_sem_imagem)
                questao_id_salva = self.questao_id
            else:
                questao_id_salva = salvar_questao(dados_sem_imagem)

            # ✅ SEGUNDO: Processa imagem COM ID real
            caminho_imagem_final = ""
            if hasattr(self, 'imagem_path_original') and self.imagem_path_original:
                # Imagem de arquivo - processa com ID real
                caminho_imagem_final = gerenciador_imagens.processar_imagem_questao(
                    self.imagem_path_original, 
                    questao_id_salva,
                    "img"
                )
            elif hasattr(self, 'imagem_pixmap') and self.imagem_pixmap:
                # Imagem do clipboard - salva com ID real
                caminho_imagem_final = gerenciador_imagens.salvar_pixmap(
                    self.imagem_pixmap, 
                    f"questao_{questao_id_salva}"
                )

            # ✅ TERCEIRO: Atualiza questão com caminho correto
            if caminho_imagem_final:
                atualizar_imagem_questao(questao_id_salva, caminho_imagem_final)

            QMessageBox.information(self, "Sucesso", "Questão salva com sucesso!")
            self.cadastro_concluido.emit(questao_id_salva)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {e}")
    
    def _criar_botao_formatacao(self, text, func, tooltip):
        btn = MeuToolButton()
        btn.setText(text)
        btn.setToolTip(tooltip)
        btn.clicked.connect(func)
        btn.setFixedSize(30, 30)
        return btn
    
    def _aplicar_comando_latex(self, pre, post):
        cursor = self.enunciado_input.textCursor()
        texto_selecionado = cursor.selectedText()
        cursor.removeSelectedText()
        cursor.insertText(f"{pre}{texto_selecionado}{post}")
        cursor.setPosition(cursor.position() - len(post))
        self.enunciado_input.setTextCursor(cursor)
        self.enunciado_input.setFocus()

    def _inserir_simbolo(self, simbolo_selecionado):
        codigo_latex = self.simbolos_latex.get(simbolo_selecionado)
        if codigo_latex: 
            cursor = self.enunciado_input.textCursor()
            cursor.insertText(codigo_latex)

            # Caso especial para a raiz quadrada, para posicionar o cursor dentro das chaves
            if '{}' in codigo_latex:
                cursor.setPosition(cursor.position() - 1)
                self.enunciado_input.setTextCursor(cursor)

            self.enunciado_input.setFocus()
            
        # Reseta o ComboBox para a opção inicial
        self.simbolo_combo.setCurrentIndex(0)
    
    def aplicar_latex_bold(self): 
        self._aplicar_comando_latex("\\textbf{{", "}}")
    
    def aplicar_latex_italic(self): 
        self._aplicar_comando_latex("\\textit{{", "}}")
    
    def aplicar_latex_underline(self): 
        self._aplicar_comando_latex("\\underline{{", "}}")
    
    def aplicar_latex_superscript(self): 
        self._aplicar_comando_latex("$^{{", "}}$")
    
    def aplicar_latex_subscript(self): 
        self._aplicar_comando_latex("$_{{", "}}$")
    
    def _inserir_snippet(self, texto_selecionado):
        # Usando dedent para a formatação correta do snippet
        resposta_multipla_auto_snippet = dedent("""
        # Use este modelo para gerar alternativas com múltiplos
        # valores de forma 100% automática.
        resposta_valor = {
            "valores": {
                "Var1": var1,
                "Var2": var2
            },
            "formato_texto": "Var$_1$ = {Var1} \\\\ Var$_2$ = {Var2}"
        }
        """)
        snippets = {
            #"Sortear Inteiro (randint)": "numero = random.randint(min, max)",
            #"Sortear Decimal (uniform)": "numero = random.uniform(min, max)",
            "Sortear de Lista (choice)": "valor = random.choice([a, b, c, d, e]) #adicionar no mínimo 5 opções",
            "Definir Resposta (Simples)": "\nresposta_valor = ",
            "Definir Resposta Múltipla (Auto)": resposta_multipla_auto_snippet
        }
        snippet_code = snippets.get(texto_selecionado, "")
        if snippet_code:
            if self.parametros_input.toPlainText():
                self.parametros_input.insertPlainText("\n" + snippet_code)
            else:
                self.parametros_input.insertPlainText(snippet_code)

        self.snippet_combo.setCurrentIndex(0)
    
    def _alternar_modo_teorica(self, checked): 
        self.atualizar_ui_formato()
    
    def _atualizar_preview_imagem(self):
        if self.imagem_path and os.path.exists(self.imagem_path):
            pixmap = QPixmap(self.imagem_path)
            self.imagem_preview_label.setPixmap(pixmap.scaled(self.imagem_preview_label.width(), 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.imagem_preview_label.setText("Nenhuma imagem selecionada.")
            self.imagem_preview_label.setPixmap(QPixmap())
    
    '''def _inserir_imagem_arquivo(self):
        novo_caminho = gerenciador_imagens.selecionar_e_copiar_imagem()
        if novo_caminho:
            gerenciador_imagens.remover_imagem(self.imagem_path)
            self.imagem_path = novo_caminho
            self._atualizar_preview_imagem()
    
    def _colar_imagem_clipboard(self):
        clipboard = QApplication.clipboard()
        pixmap = clipboard.pixmap()
        if not pixmap.isNull():
            novo_caminho = gerenciador_imagens.salvar_pixmap(pixmap)
            if novo_caminho: 
                gerenciador_imagens.remover_imagem(self.imagem_path) 
                self.imagem_path = novo_caminho
                self._atualizar_preview_imagem()
        else: 
            QMessageBox.warning(self, "Aviso", "Nenhuma imagem na área de transferência.")'''
    
    def _inserir_imagem_arquivo(self):
        """Seleciona imagem mas NÃO copia para pasta img ainda"""
        caminho_original, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Imagem", "", 
            "Imagens (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if caminho_original:
            # ✅ Só guarda o caminho original, NÃO processa ainda
            self.imagem_path_original = caminho_original
            self._atualizar_preview_imagem()

    def _colar_imagem_clipboard(self):
        """Cola imagem mas NÃO salva na pasta img ainda"""
        clipboard = QApplication.clipboard()
        pixmap = clipboard.pixmap()
        if not pixmap.isNull():
            # ✅ Só guarda o pixmap, NÃO salva ainda
            self.imagem_pixmap = pixmap
            self.imagem_path_original = ""  # Indica que veio do clipboard
            self._atualizar_preview_imagem()
        else: 
            QMessageBox.warning(self, "Aviso", "Nenhuma imagem na área de transferência.")
    
    def _remover_imagem(self):
        gerenciador_imagens.remover_imagem(self.imagem_path)
        self.imagem_path = ""
        self._atualizar_preview_imagem()
    
    def _remover_linha_tabela(self):
        row = self.tabela_vars.currentRow()
        if row >= 0: 
            self.tabela_vars.removeRow(row)
    
    def _alternar_campos_alternativas(self, checked): 
        self.widget_alternativas_manuais.setDisabled(checked)
        self.atualizar_ui_formato()
    
    def configurar_modo(self):
        if self.questao_id: 
            self.titulo_label.setText("Editar Questão")
            self.btn_salvar.setText("💾 Salvar Alterações")
            self.carregar_dados_questao()
        else:
            self.titulo_label.setText("Cadastrar Nova Questão")
            self.btn_salvar.setText("💾 Salvar Questão")

    def _formatar_latex_para_html(self, texto_latex):
        """
        Converte uma string com LaTeX simples para um formato HTML/rich text
        aproximado, usando o dicionário de símbolos da própria classe.
        """
        if not texto_latex:
            return ""

        texto = texto_latex

        texto = texto.replace('R\\$', 'R$')
        texto = texto.replace('\\%', '%')
        #placeholder_real = "moeda"
        #texto = texto.replace('R$', placeholder_real)

        # 1. Substituições de símbolos usando o dicionário self.simbolos_latex
        for key, value in self.simbolos_latex.items():
            if key == '-- Símbolos --':
                continue # Pula o item placeholder do menu

            # Extrai o caractere unicode da chave (ex: 'Ω' de 'Ω (Ohm)')
            caractere_unicode = key.split(' ')[0]
            comando_latex = value
            
            # Casos especiais que precisam de tratamento diferente
            if '\\sqrt' in comando_latex:
                texto = texto.replace('\\sqrt', '√')
                continue
            if '\\vec' in comando_latex:
                # A conversão de \vec{...} para HTML é complexa. Ignoramos por simplicidade.
                continue

            # Para os outros, faz a substituição direta do comando pelo caractere
            if caractere_unicode:
                texto = texto.replace(comando_latex, caractere_unicode)

        # 2. Converte subscrito e sobrescrito (código anterior, ainda necessário)
        texto = re.sub(r'\\textbf\{([^}]+)\}', r'<b>\1</b>', texto)    # Negrito
        texto = re.sub(r'\\textit\{([^}]+)\}', r'<i>\1</i>', texto)    # Itálico
        texto = re.sub(r'\\underline\{([^}]+)\}', r'<u>\1</u>', texto) # Sublinhado
        # --- ATUALIZAÇÃO PARA SUBSCRITO/SOBRESCRITO ---
        # Primeiro, trata os casos com chaves (mais específicos)
        texto = re.sub(r'_\{([^}]+)\}', r'<sub>\1</sub>', texto)
        texto = re.sub(r'\^\{([^}]+)\}', r'<sup>\1</sup>', texto)
        
        # Depois, trata os casos de caractere único (mais simples)
        texto = re.sub(r'_([a-zA-Z0-9])', r'<sub>\1</sub>', texto)      # Ex: I_1 -> I<sub>1</sub>
        texto = re.sub(r'\^([a-zA-Z0-9])', r'<sup>\1</sup>', texto)      # Ex: x^2 -> x<sup>2</sup>
        # --- FIM DA ATUALIZAÇÃO ---

        # 3. Remove os delimitadores de ambiente matemático ($) que sobraram
        texto = texto.replace('$', '')
        #texto = texto.replace(placeholder_real, 'R$') # Restaura o 'R$'
        
        return texto

    def _testar_codigo(self):
        """
        Executa a geração da questão em um loop de busca para encontrar uma
        variante válida, e exibe o resultado ou o erro final em um pop-up.
        """
        # 1. Monta a "questão temporária" com os dados da tela
        try:
            num_alternativas = int(self.num_alternativas_input.value()) if hasattr(self, 'num_alternativas_input') else 5

            questao_base = {
                "id": self.questao_id or 0,
                "enunciado": self.enunciado_input.toPlainText(),
                "parametros": self.parametros_input.toPlainText(),
                "formato_questao": self.formato_combo.currentText(),
                "gerar_alternativas_auto": self.check_gerar_auto.isChecked(),
                "permitir_negativos": 1 if self.check_permitir_negativos.isChecked() else 0,
                "unidade_resposta": self.unidade_input.currentText(),
                "num_alternativas": num_alternativas,
                "alternativa_a": self.alternativas_inputs['A'].text(),
                "alternativa_b": self.alternativas_inputs['B'].text(),
                "alternativa_c": self.alternativas_inputs['C'].text(),
                "alternativa_d": self.alternativas_inputs['D'].text(),
                "alternativa_e": self.alternativas_inputs['E'].text(),
                "resposta_correta": self.resposta_correta_combo.currentText(),
            }
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Coletar Dados", f"Não foi possível ler os dados da interface para o teste:\n{e}")
            return

        # --- INÍCIO DA NOVA LÓGICA DE BUSCA ---
        variante_sucesso = None
        log_final_erro = ""
        max_tentativas = 100  # Um limite de segurança para encontrar uma variante válida

        for tentativa in range(max_tentativas):
            # Usamos uma sequência de sementes previsível para a busca (0, 1, 2, ...)
            seed_teste = tentativa

            log_stream = io.StringIO()
            with redirect_stdout(log_stream):
                try:
                    # Chama o motor dentro do loop com a semente da vez
                    variante_tentativa = _gerar_variante_questao(questao_base, seed=seed_teste)
                except Exception as e:
                    print(f"ERRO CRÍTICO DURANTE O TESTE (tentativa {tentativa}):\n{e}")
                    variante_tentativa = None

            log_output = log_stream.getvalue().strip()

            if variante_tentativa:
                # SUCESSO! Guardamos o resultado e paramos o loop de busca
                variante_sucesso = variante_tentativa
                break  # Interrompe o loop na primeira tentativa bem-sucedida
            else:
                # FALHA NESTA TENTATIVA. Guardamos o último log de erro para o caso de todas falharem.
                if log_output:
                    log_final_erro = log_output
        # --- FIM DA NOVA LÓGICA DE BUSCA ---

        # 3. Exibe o resultado final após o loop terminar
        if variante_sucesso:
            # SUCESSO
            titulo = "✅ Teste Bem-Sucedido!"
            
            variante = variante_sucesso
            resposta_str = self._formatar_latex_para_html(str(variante.get('resposta_valor')))
            alternativas_list = variante.get('alternativas_valores', [])
            alternativas_str = '<br>'.join([f"• {self._formatar_latex_para_html(str(val))}" for val in alternativas_list])
            if not alternativas_str:
                alternativas_str = "(Não aplicável ou não gerado)"
            enunciado_bruto = variante.get('enunciado', '(Não foi possível gerar o enunciado.)')
            enunciado_str = self._formatar_latex_para_html(enunciado_bruto)

            mensagem = (
                f"<b>Enunciado Gerado:</b><br>{enunciado_str}"
                f"<hr>"  # Cria uma linha divisória horizontal
                f"<b>Resposta Correta:</b><br>{resposta_str}"
                f"<hr>"  # Cria uma linha divisória horizontal
                f"<b>Alternativas Geradas:</b><br>{alternativas_str}"
            )
            QMessageBox.information(self, titulo, mensagem)
        else:
            # FALHA FINAL (após todas as tentativas)
            titulo = "❌ Teste Falhou Após Múltiplas Tentativas"
            
            if log_final_erro:
                mensagem = f"Após {max_tentativas} tentativas, não foi possível gerar uma variante válida.\n\nÚltimo erro encontrado:\n---\n{log_final_erro}"
            else:
                mensagem = f"Após {max_tentativas} tentativas, não foi possível gerar uma variante válida (o motor não retornou um erro específico)."
            
            QMessageBox.warning(self, titulo, mensagem)

    def sizeHint(self):
        """Informa à MainWindow qual o tamanho ideal para esta tela."""
        return QSize(1000, 800)
    
    def _limpar_formulario(self):
        """Reseta todos os campos do formulário para o estado inicial de forma segura."""
        self.check_ativa.setChecked(True)
        self.formato_combo.setCurrentIndex(0)
        
        self.disciplina_input.setCurrentIndex(-1)
        self.disciplina_input.lineEdit().clear()
        
        self.tema_input.clear()
        self.tema_input.lineEdit().clear()

        self.dificuldade_combo.setCurrentIndex(0)
        self.grupo_input.clear()
        self.fonte_input.clear()
        self.enunciado_input.clear()
        
        self._remover_imagem()
        
        # Antes de acessar os widgets das "páginas", verifica se eles existem
        if hasattr(self, 'parametros_input'):
            self.parametros_input.clear()

        self.unidade_input.setCurrentIndex(0)
        self.check_permitir_negativos.setChecked(False)
        self.check_teorica.setChecked(False)

        if hasattr(self, 'alternativas_inputs'):
            for letra in self.alternativas_inputs:
                self.alternativas_inputs[letra].clear()

        # Antes de acessar self.resposta_group, verifica se o atributo existe.
        if hasattr(self, 'resposta_group') and self.resposta_group.checkedButton():
            self.resposta_group.setExclusive(False)
            self.resposta_group.checkedButton().setChecked(False)
            self.resposta_group.setExclusive(True)

        # --- A NOVA CORREÇÃO ESTÁ AQUI ---
        # Antes de acessar self.radio_python, verifica se o atributo existe.
        if hasattr(self, 'radio_python'):
            self.radio_python.setChecked(True)

    def abrir_para_criacao(self):
        """Prepara a tela para cadastrar uma nova questão."""
        self.setWindowTitle("Cadastrar Nova Questão")
        self.questao_id = None
        self.titulo_label.setText("Cadastro de Nova Questão")
        self._limpar_formulario() # Usa seu método de limpar já existente
        self.atualizar_ui_formato()
        if not self.imagem_path:
            self.imagem_preview_label.setText("Nenhuma imagem selecionada.")

    def abrir_para_edicao(self, questao_id):
        """Prepara a tela para editar uma questão existente."""
        self.setWindowTitle(f"Editar Questão ID: {questao_id}")
        self.questao_id = questao_id
        if self.questao_id is None:
            # Se por algum motivo o ID for nulo, volta para a tela anterior
            self.voltar_pressed.emit()
            return
            
        self.titulo_label.setText(f"Editando Questão ID: {self.questao_id}")
        self._limpar_formulario()
        self.carregar_dados_questao() # Usa seu método de carregar já existente
        self.atualizar_ui_formato()
        if not self.imagem_path:
            self.imagem_preview_label.setText("Nenhuma imagem selecionada.")