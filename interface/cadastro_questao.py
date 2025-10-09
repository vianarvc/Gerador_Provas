# interface/cadastro_questao.py

import json, os, re
from textwrap import dedent
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, 
    QPushButton, QScrollArea, QMessageBox, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QGroupBox, QApplication,
    QSlider, QToolButton, QRadioButton, QButtonGroup, QDesktopWidget
)
from PyQt5.QtGui import QFont, QPixmap, QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from database import salvar_questao, obter_questao_por_id, atualizar_questao, obter_temas, obter_disciplinas, obter_disciplina_id_por_nome, salvar_disciplina, obter_disciplina_nome_por_id
import gerenciador_imagens
from .custom_widgets import NoScrollComboBox
import random

UNIDADES_COMUNS = ["", "C", "S", "V", "A", "Ω", "W", "F", "H", "Hz", "s", "m", "g", "kg", "N", "J"]

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

class CadastroQuestaoWindow(QWidget):
    questao_atualizada = pyqtSignal()
    
    def __init__(self, questao_id=None):
        super().__init__()
        self.questao_id = questao_id
        self.imagem_path = ""
        self.alternativas_inputs = {} # Corrigido o erro anterior
        self.simbolos_latex = {
            '-- Símbolos --': '',
            'Ω (Ohm)': '$\\Omega$',
            'µ (micro)': '$\\mu$',
            'π (pi)': '$\\pi$',
            'Δ (delta)': '$\\Delta$',
            'α (alfa)': '$\\alpha$',
            'β (beta)': '$\\beta$',
            'θ (theta)': '$\\theta$',
            '° (graus)': '^{\\circ}',
            '± (mais/menos)': '$\\pm$',
            '√ (raiz)': '$\\sqrt{{}}$',
            'v (vetor)': '$\\vec{{}}$'
        }
        self.setWindowTitle("Cadastro de Questão")
        self.resize(950, 800)
        self._aplicar_estilos() 

        layout_principal = QVBoxLayout(self)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll.setWidget(content)
        
        # Adiciona margens internas à área de conteúdo
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout_principal.addWidget(scroll)

        # Configura o Título Principal
        self.titulo_label = QLabel("Cadastro de Questão")
        self.titulo_label.setObjectName("TituloPrincipal") 
        layout.addWidget(self.titulo_label)
        
        config_layout = QHBoxLayout()
        self.check_ativa = QCheckBox("Questão Ativa (incluir no sorteio de provas)")
        self.check_ativa.setChecked(True)
        config_layout.addWidget(self.check_ativa)
        config_layout.addStretch()
        layout.addLayout(config_layout)
        
        # Estrutura de Campos (Formato, Tema, Dificuldade, Grupo) em duas colunas
        campos_layout = QHBoxLayout()
        
        # Coluna Esquerda
        col_esq = QVBoxLayout()
        col_esq.addWidget(QLabel("Formato da Questão:"))
        self.formato_combo = NoScrollComboBox()
        self.formato_combo.addItems(["Múltipla Escolha", "Verdadeiro ou Falso", "Discursiva"])
        col_esq.addWidget(self.formato_combo)
       
        # AJUSTE 1: Checkbox Teórica fica abaixo do Formato
        self.check_teorica = QCheckBox("Múltipla Escolha Teórica (alternativas fixas)")
        self.check_teorica.toggled.connect(self.atualizar_ui_formato)
        col_esq.addWidget(self.check_teorica)
        col_esq.addSpacing(10) # Espaçamento após a checkbox
        
        # CAMPO DISCIPLINA (Utilizando self.tema_input, conforme solicitado)
        col_esq.addWidget(QLabel("Disciplina:"))
        # ATENÇÃO: self.tema_input será redefinido logo abaixo na col_dir
        self.disciplina_input = NoScrollComboBox() 
        self.disciplina_input.setEditable(True)
        self.disciplina_input.addItems(obter_disciplinas()) # Presumindo 'obter_disciplinas'
        self.disciplina_input.lineEdit().setPlaceholderText("Selecione ou digite uma nova disciplina")
        self.disciplina_input.activated.connect(self._atualizar_lista_temas)
        col_esq.addWidget(self.disciplina_input)
        col_esq.addStretch(1) # Preenche o espaço
        
        # Coluna Direita
        col_dir = QVBoxLayout()
        col_dir.addWidget(QLabel("Dificuldade:"))
        self.dificuldade_combo = NoScrollComboBox()
        self.dificuldade_combo.addItems(["Fácil", "Média", "Difícil"])
        col_dir.addWidget(self.dificuldade_combo)
        col_dir.addSpacing(20)
        col_dir.addStretch(1)

        # CAMPO TEMA (Redefinindo self.tema_input, alinhado com o campo Disciplina acima)
        col_dir.addWidget(QLabel("Tema:"))
        self.tema_input = NoScrollComboBox() # SOBRESCRITA: esta é a instância final de self.tema_input
        self.tema_input.setEditable(True)
        self.tema_input.addItems(obter_temas())
        self.tema_input.lineEdit().setPlaceholderText("Selecione ou digite um novo tema")
        col_dir.addWidget(self.tema_input)

        # Campo Grupo (Movido para logo abaixo do Tema)
        self.grupo_label = QLabel("Grupo (opcional):")
        self.grupo_input = QLineEdit()
        self.grupo_input.setPlaceholderText("Ex: CONCEITO-LEI-OHM")
        col_dir.addWidget(self.grupo_label)
        col_dir.addWidget(self.grupo_input)
        
        #Campo Principal
        campos_layout.addLayout(col_esq)
        campos_layout.addSpacing(30)
        campos_layout.addLayout(col_dir)
        layout.addLayout(campos_layout)
        layout.addSpacing(15) # Espaçamento para separar do bloco de cima
        layout.addWidget(QLabel("Fonte da Questão (opcional):"))
        self.fonte_input = QLineEdit()
        self.fonte_input.setPlaceholderText("Ex: Livro X, Ed. Y, p. 123")
        layout.addWidget(self.fonte_input)
        
        layout.addWidget(QLabel("Enunciado da Questão (pode usar comandos LaTeX):"))

        # Toolbar do Enunciado
        toolbar_enunciado = QHBoxLayout()
        btn_bold = self._criar_botao_formatacao("B", self.aplicar_latex_bold, "Negrito (\\textbf{})")
        btn_italic = self._criar_botao_formatacao("I", self.aplicar_latex_italic, "Itálico (\\textit{})")
        btn_underline = self._criar_botao_formatacao("U", self.aplicar_latex_underline, "Sublinhado (\\underline{})")
        btn_superscript = self._criar_botao_formatacao("x²", self.aplicar_latex_superscript, "Sobrescrito ($^{})")
        btn_subscript = self._criar_botao_formatacao("x₂", self.aplicar_latex_subscript, "Subscrito ($_{})")

        toolbar_enunciado.addWidget(btn_bold)
        toolbar_enunciado.addWidget(btn_italic)
        toolbar_enunciado.addWidget(btn_underline)
        toolbar_enunciado.addSpacing(10)
        toolbar_enunciado.addWidget(btn_superscript)
        toolbar_enunciado.addWidget(btn_subscript)
        
        toolbar_enunciado.addSpacing(20)
        self.simbolo_combo = NoScrollComboBox()
        self.simbolo_combo.addItems(self.simbolos_latex.keys())
        self.simbolo_combo.activated[str].connect(self._inserir_simbolo)
        toolbar_enunciado.addWidget(self.simbolo_combo)

        toolbar_enunciado.addStretch()
        layout.addLayout(toolbar_enunciado)

        # AJUSTE 2: Altura maior para o Enunciado
        self.enunciado_input = QTextEdit()
        self.enunciado_input.setPlaceholderText("Use {variavel} para inserir valores...")
        self.enunciado_input.setFixedHeight(180) # Aumentado de 120 para 180
        layout.addWidget(self.enunciado_input)

        # Grupo Imagem
        group_imagem = QGroupBox("Imagem da Questão")
        layout_imagem = QVBoxLayout(group_imagem)
        botoes_imagem_layout = QHBoxLayout()
        btn_inserir_imagem = QPushButton("📎 Inserir do Arquivo")
        btn_colar_imagem = QPushButton("📋 Colar Imagem")
        btn_remover_imagem = QPushButton("❌ Remover Imagem")
        
        btn_inserir_imagem.clicked.connect(self._inserir_imagem_arquivo)
        btn_colar_imagem.clicked.connect(self._colar_imagem_clipboard)
        btn_remover_imagem.clicked.connect(self._remover_imagem)
        botoes_imagem_layout.addWidget(btn_inserir_imagem)
        botoes_imagem_layout.addWidget(btn_colar_imagem)
        botoes_imagem_layout.addWidget(btn_remover_imagem)
        layout_imagem.addLayout(botoes_imagem_layout)

        self.imagem_preview_label = QLabel("Nenhuma imagem selecionada.")
        self.imagem_preview_label.setAlignment(Qt.AlignCenter)
        self.imagem_preview_label.setMinimumHeight(80)
        self.imagem_preview_label.setObjectName("ImagemPreview") 
        layout_imagem.addWidget(self.imagem_preview_label)

        slider_layout = QHBoxLayout()
        self.largura_label = QLabel("Largura na Prova: 50%")
        self.largura_slider = QSlider(Qt.Horizontal)
        self.largura_slider.setRange(10, 100)
        self.largura_slider.setValue(50)
        self.largura_slider.valueChanged.connect(lambda v: self.largura_label.setText(f"Largura na Prova: {v}%"))
        slider_layout.addWidget(self.largura_label)
        slider_layout.addWidget(self.largura_slider)
        layout_imagem.addLayout(slider_layout)
        layout.addWidget(group_imagem)

        # Grupo Variáveis
        self.group_variaveis = QGroupBox("Geração de Variáveis e Resposta Numérica")
        layout_vars = QVBoxLayout(self.group_variaveis)
        # AJUSTE 3: Padding menor para o QGroupBox de Variáveis via QSS, mas mantendo o layout
        layout_vars.setContentsMargins(10, 10, 10, 10) # Reduz o padding interno do layout
        layout_vars.setSpacing(0)
        
        # Combobox Tipo Geração
        tipo_layout = QHBoxLayout()
        tipo_layout.addWidget(QLabel("Tipo de Geração de Variáveis:"))
        self.tipo_combo = NoScrollComboBox()
        self.tipo_combo.addItems(["Código (Python)", "Tabela (Visual)"])
        tipo_layout.addWidget(self.tipo_combo)
        tipo_layout.addStretch()
        layout_vars.addLayout(tipo_layout)

        self.stacked_widget = QStackedWidget()
        layout_vars.addWidget(self.stacked_widget)
        self.tipo_combo.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)

        # Widget Código (Python)
        widget_codigo = QWidget()
        layout_codigo = QVBoxLayout(widget_codigo)
        snippet_layout = QHBoxLayout()
        snippet_layout.addWidget(QLabel("<b>Inserir Snippet:</b>"))

        self.snippet_combo = NoScrollComboBox()
        self.snippet_combo.addItems([
            "-- Selecione --", 
            "Sortear Inteiro (randint)", 
            "Sortear Decimal (uniform)", 
            "Sortear de Lista (choice)", 
            "Definir Resposta (Simples)",
            "Definir Resposta Múltipla (Auto)"
        ]) 
        self.snippet_combo.activated[str].connect(self._inserir_snippet)

        snippet_layout.addWidget(self.snippet_combo)
        snippet_layout.addStretch()
        layout_codigo.addLayout(snippet_layout)

        self.parametros_input = QTextEdit()
        self.parametros_input.setFont(QFont("Courier", 12))
        self.parametros_input.setPlaceholderText("# Defina suas variáveis...")
        #self.parametros_input.setFixedHeight(150)
        self.parametros_input.setMinimumHeight(100) # Define uma altura mínima menor, mas não fixa
        layout_codigo.addWidget(self.parametros_input)

        self.highlighter = PythonHighlighter(self.parametros_input.document())
        layout_codigo.addStretch() 
        self.stacked_widget.addWidget(widget_codigo)

        # Widget Tabela (Visual)
        widget_tabela = QWidget()
        layout_tabela = QVBoxLayout(widget_tabela)
        layout_tabela.addWidget(QLabel("<b>Tabela de Variáveis:</b>"))
        self.tabela_vars = QTableWidget()
        self.tabela_vars.setColumnCount(3)
        self.tabela_vars.setHorizontalHeaderLabels(["Nome", "Tipo", "Valores"])
        self.tabela_vars.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela_vars.setMinimumHeight(150)
        layout_tabela.addWidget(self.tabela_vars)

        botoes_tabela_layout = QHBoxLayout()
        btn_add_var = QPushButton("➕ Adicionar")
        btn_rem_var = QPushButton("➖ Remover")
        
        btn_add_var.setObjectName("BotaoAcao")
        btn_rem_var.setObjectName("BotaoAcao")
        
        btn_add_var.clicked.connect(self._adicionar_linha_tabela)
        btn_rem_var.clicked.connect(self._remover_linha_tabela)
        botoes_tabela_layout.addWidget(btn_add_var)
        botoes_tabela_layout.addWidget(btn_rem_var)
        botoes_tabela_layout.addStretch()
        layout_tabela.addLayout(botoes_tabela_layout)

        layout_tabela.addWidget(QLabel("<b>Fórmula da Resposta (em Python):</b>"))
        self.formula_resposta_input = QLineEdit()
        self.formula_resposta_input.setPlaceholderText("Use os Nomes das Variáveis. Ex: V / R")
        layout_tabela.addWidget(self.formula_resposta_input)
        self.stacked_widget.addWidget(widget_tabela)

        # Unidade de Medida
        unidade_layout = QHBoxLayout()
        self.label_unidade_input = QLabel("<b>Unidade de Medida da Resposta:</b>")
        unidade_layout.addWidget(self.label_unidade_input)

        self.unidade_input = NoScrollComboBox()
        self.unidade_input.setEditable(True)
        self.unidade_input.addItems(UNIDADES_COMUNS)
        self.unidade_input.lineEdit().setPlaceholderText("Selecione ou digite uma unidade")
        unidade_layout.addWidget(self.unidade_input)
        unidade_layout.addStretch()
        layout_vars.addLayout(unidade_layout)

        layout.addWidget(self.group_variaveis)

        # Grupo Alternativas
        self.group_alternativas = QGroupBox("Alternativas e Resposta")
        layout_alternativas = QVBoxLayout(self.group_alternativas)

        self.alternativas_stack = QStackedWidget()
        layout_alternativas.addWidget(self.alternativas_stack)

        # Página Múltipla Escolha (ME)
        page_me = QWidget()
        layout_me = QVBoxLayout(page_me)

        auto_layout = QHBoxLayout()
        self.check_gerar_auto = QCheckBox("Gerar alternativas numericamente")
        self.check_gerar_auto.toggled.connect(self.atualizar_ui_formato)
        auto_layout.addWidget(self.check_gerar_auto)
        self.check_permitir_negativos = QCheckBox("Permitir alternativas negativas")
        auto_layout.addWidget(self.check_permitir_negativos)
        auto_layout.addStretch()
        layout_me.addLayout(auto_layout)

        self.widget_alternativas_manuais = QWidget()
        layout_manuais = QVBoxLayout(self.widget_alternativas_manuais)
        layout_manuais.setSpacing(5)

        # AJUSTE 4: Alternativas alinhadas na vertical
        grid_alternativas = QWidget()
        grid_layout = QVBoxLayout(grid_alternativas) # Alterado de QHBoxLayout para QVBoxLayout
        grid_layout.setSpacing(5)

        for i, letra in enumerate(["A", "B", "C", "D", "E"]):
            alt_layout_h = QHBoxLayout() # Novo layout horizontal para cada alternativa
            
            # Label da letra da alternativa
            lbl_letra = QLabel(f"{letra})")
            lbl_letra.setFixedWidth(20) # Define uma largura fixa
            alt_layout_h.addWidget(lbl_letra)
            
            alternativa = QLineEdit()
            alternativa.setPlaceholderText(f"Conteúdo da alternativa {letra}")
            self.alternativas_inputs[letra] = alternativa
            alt_layout_h.addWidget(alternativa)
            
            grid_layout.addLayout(alt_layout_h)

        layout_manuais.addWidget(grid_alternativas)

        # --- BLOCO MODIFICADO ---
        self.resposta_correta_widget = QWidget()
        resp_layout = QHBoxLayout(self.resposta_correta_widget)
        resp_layout.setContentsMargins(0, 10, 0, 0) # Adiciona um espaçamento superior
        resp_layout.addWidget(QLabel("Resposta Correta:"))
        self.resposta_correta_combo = NoScrollComboBox()
        self.resposta_correta_combo.addItems(["A", "B", "C", "D", "E"])
        self.resposta_correta_combo.setFixedWidth(50)
        resp_layout.addWidget(self.resposta_correta_combo)
        resp_layout.addStretch()
        layout_manuais.addWidget(self.resposta_correta_widget)
        # --- FIM DO BLOCO MODIFICADO ---

        layout_me.addWidget(self.widget_alternativas_manuais)
        self.alternativas_stack.addWidget(page_me)

        # Página Verdadeiro ou Falso (VF)
        page_vf = QWidget()
        layout_vf = QVBoxLayout(page_vf)
        layout_vf.addWidget(QLabel("Resposta Correta:"))

        self.vf_verdadeiro_radio = QRadioButton("Verdadeiro")
        self.vf_falso_radio = QRadioButton("Falso")

        self.vf_button_group = QButtonGroup(self)
        self.vf_button_group.addButton(self.vf_verdadeiro_radio)
        self.vf_button_group.addButton(self.vf_falso_radio)

        self.vf_verdadeiro_radio.setChecked(True)

        layout_vf.addWidget(self.vf_verdadeiro_radio)
        layout_vf.addWidget(self.vf_falso_radio)
        layout_vf.addStretch()
        self.alternativas_stack.addWidget(page_vf)

        # Página Discursiva
        page_disc = QWidget()
        layout_disc = QVBoxLayout(page_disc)
        layout_disc.addWidget(QLabel("Questões discursivas não possuem gabarito pré-definido e são corrigidas manualmente."))
        layout_disc.addStretch()
        self.alternativas_stack.addWidget(page_disc)

        layout.addWidget(self.group_alternativas)

        self.formato_combo.currentIndexChanged.connect(self.atualizar_ui_formato)

        # Botão Salvar
        self.btn_salvar = QPushButton("💾 Salvar Questão")
        self.btn_salvar.setObjectName("BotaoSalvarPrincipal") 
        self.btn_salvar.setMinimumHeight(45)
        self.btn_salvar.clicked.connect(self.salvar_alterar_questao)
        layout.addWidget(self.btn_salvar)

        self._center() 
        self.configurar_modo()
        self.atualizar_ui_formato()

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

    def _aplicar_estilos(self):
        """Define e aplica o Qt Style Sheet (QSS) para o formulário."""
        style = """
        /* GERAL */
        QWidget {
            background-color: #f7f7f7;
            font-family: Arial;
        }

        /* TÍTULO PRINCIPAL */
        #TituloPrincipal {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 2px solid #3498db;
        }

        /* GROUP BOXES (Seções) */
        QGroupBox {
            font-weight: bold;
            color: #34495e; 
            margin-top: 10px;
            padding-top: 20px;
            border: 1px solid #bdc3c7;
            border-radius: 5px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 10px;
            background-color: #ecf0f1; 
            border-radius: 3px;
        }

        /* CAMPOS DE INPUT E TEXTAREA (QLineEdit, QTextEdit, QComboBox) */
        QLineEdit, QTextEdit, QComboBox {
            border: 1px solid #bdc3c7;
            border-radius: 5px;
            padding: 5px;
            background-color: white;
            selection-background-color: #3498db;
        }
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
            border: 1px solid #3498db;
        }
        
        QTableWidget {
            gridline-color: #ecf0f1;
            border: 1px solid #bdc3c7;
            selection-background-color: #95a5a6;
        }

        /* TOOLBUTTONS (Botões B, I, U, etc.) */
        QToolButton {
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            background-color: #ecf0f1;
            padding: 3px;
            font-weight: bold;
            color: #2c3e50;
        }
        QToolButton:hover {
            background-color: #c9d2d7;
        }
        
        /* BOTÕES DE AÇÃO PRINCIPAL (Salvar) */
        #BotaoSalvarPrincipal {
            background-color: #2ecc71;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 26px;
            font-weight: bold;
            margin-top: 15px;
        }
        #BotaoSalvarPrincipal:hover {
            background-color: #27ae60;
        }

        /* BOTÕES SECUNDÁRIOS (Imagem, Adicionar/Remover Tabela) */
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 5px 10px;
            font-size: 22px;
            min-height: 25px;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
        
        /* Botões de ação dentro da tabela (Adicionar/Remover) */
        #BotaoAcao {
            min-width: 80px;
            font-size: 12px;
            background-color: #95a5a6;
        }
        #BotaoAcao:hover {
            background-color: #7f8c8d;
        }
        
        /* PRÉ-VISUALIZAÇÃO DA IMAGEM */
        #ImagemPreview {
            border: 2px dashed #95a5a6;
            border-radius: 5px;
            color: #7f8c8d;
        }
        """
        self.setStyleSheet(style)

    def _center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def _adicionar_linha_tabela(self):
        row = self.tabela_vars.rowCount()
        self.tabela_vars.insertRow(row)
        # Cria e insere o ComboBox customizado na tabela
        combo = NoScrollComboBox()
        combo.addItems(["Intervalo Inteiro", "Intervalo Decimal", "Lista de Valores"])
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
    
    def carregar_dados_questao(self):
        dados = obter_questao_por_id(self.questao_id)
        self._atualizar_lista_temas()
        self.tema_input.setCurrentText(dados.get("tema", ""))
        self.fonte_input.setText(dados.get("fonte", ""))
        if not dados: return
        
        self.check_ativa.setChecked(bool(dados.get("ativa", 1)))
        self.grupo_input.setText(dados.get("grupo", ""))
        self.check_permitir_negativos.setChecked(bool(dados.get("permitir_negativos", 0)))
        
        formato = dados.get("formato_questao", "Múltipla Escolha")
        self.formato_combo.setCurrentText(formato)
        self.check_teorica.setChecked(bool(dados.get("is_teorica", 0)))
        # Carrega o nome da disciplina usando o ID
        disciplina_id = dados.get("disciplina_id")
        disciplina_nome = obter_disciplina_nome_por_id(disciplina_id)
        self.disciplina_input.setCurrentText(disciplina_nome)
        self._atualizar_lista_temas()
        self.tema_input.setCurrentText(dados.get("tema", ""))
        self.dificuldade_combo.setCurrentText(dados.get("dificuldade", "Fácil"))
        self.fonte_input.setText(dados.get("fonte", ""))
        self.enunciado_input.setPlainText(dados.get("enunciado", ""))
        self.unidade_input.setCurrentText(dados.get("unidade_resposta", ""))
        self.imagem_path = dados.get("imagem", "")
        self.largura_slider.setValue(dados.get("imagem_largura_percentual") or 50)
        self._atualizar_preview_imagem()
        
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
                
        tipo_questao = dados.get("tipo_questao", "Código (Python)")
        if tipo_questao == "Tabela (Visual)":
            self.tipo_combo.setCurrentIndex(1)
            try:
                parametros = json.loads(dados.get("parametros", "{}"))
            except json.JSONDecodeError:
                parametros = {}
            
            self.formula_resposta_input.setText(parametros.get("formula_resposta", ""))
            self.tabela_vars.setRowCount(0)
            
            for var in parametros.get("variaveis", []):
                self._adicionar_linha_tabela()
                row = self.tabela_vars.rowCount() - 1
                self.tabela_vars.setItem(row, 0, QTableWidgetItem(var.get("nome")))
                self.tabela_vars.cellWidget(row, 1).setCurrentText(var.get("tipo"))
                self.tabela_vars.setItem(row, 2, QTableWidgetItem(var.get("valores")))
        else:
            self.tipo_combo.setCurrentIndex(0)
            self.parametros_input.setPlainText(dados.get("parametros", ""))
            
        self.atualizar_ui_formato()
    
    # (Substitua a sua função salvar_alterar_questao inteira por esta)

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
        
        # Inicializa variáveis que serão preenchidas
        parametros_finais = ""
        tipo_questao_final = ""

        # --- ETAPA 3: LÓGICA DE CONVERSÃO E COLETA DOS PARÂMETROS ---
        if not is_teorica and formato != "Discursiva":
            tipo_geracao_selecionado = self.tipo_combo.currentText()
            
            if tipo_geracao_selecionado == "Código (Python)":
                parametros_finais = self.parametros_input.toPlainText().strip()
                tipo_questao_final = "Código (Python)"
                
                if not parametros_finais:
                    QMessageBox.warning(self, "Erro", "O bloco de Código (Python) não pode ser vazio para questões calculadas.")
                    return

            elif tipo_geracao_selecionado == "Tabela (Visual)":
                # --- INÍCIO DA NOVA LÓGICA DE CONVERSÃO ---
                try:
                    variaveis_tabela = []
                    for row in range(self.tabela_vars.rowCount()):
                        nome_item = self.tabela_vars.item(row, 0)
                        tipo_var_widget = self.tabela_vars.cellWidget(row, 1)
                        val_item = self.tabela_vars.item(row, 2)
                        
                        nome = nome_item.text().strip() if nome_item else ""
                        tipo_var = tipo_var_widget.currentText() if tipo_var_widget else ""
                        valores = val_item.text().strip() if val_item else ""
                        
                        if not (nome and valores):
                            QMessageBox.warning(self, "Erro de Validação", f"A linha {row + 1} da tabela de variáveis está incompleta.")
                            return

                        # Validação crucial: só permite 'Lista de Valores' para o modo Tabela
                        if tipo_var != "Lista de Valores":
                            QMessageBox.warning(self, "Erro de Validação", 
                                                "Para geração determinística, o modo 'Tabela (Visual)' "
                                                "só suporta o tipo 'Lista de Valores'.")
                            return

                        variaveis_tabela.append({"nome": nome, "valores": valores})

                    formula = self.formula_resposta_input.text().strip()
                    if not formula:
                         raise ValueError("A Fórmula da Resposta é obrigatória no modo Tabela.")

                    # Monta o dicionário para o conversor
                    dados_para_converter = {
                        "variaveis": variaveis_tabela,
                        "formula_resposta": formula
                    }
                    
                    # Chama o tradutor!
                    parametros_finais = self.converter_tabela_para_python(dados_para_converter)
                    tipo_questao_final = "Código (Python)" # Engana o sistema!

                except ValueError as e:
                    QMessageBox.warning(self, "Erro na Tabela", str(e))
                    return
                # --- FIM DA NOVA LÓGICA DE CONVERSÃO ---
        
        # Para questões teóricas, não há parâmetros nem tipo de questão
        else:
            parametros_finais = ""
            tipo_questao_final = ""

        # --- ETAPA 4: Montar o dicionário final com todos os dados ---
        dados_questao = {
            "disciplina_id": disciplina_id,
            "tema": self.tema_input.currentText().strip(),
            "fonte": self.fonte_input.text().strip(),
            "ativa": int(self.check_ativa.isChecked()),
            "grupo": self.grupo_input.text().strip(),
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
            "tipo_questao": tipo_questao_final
        }

        # Coleta de Alternativas e Resposta (depende do formato)
        if formato == "Múltipla Escolha":
            dados_questao["resposta_correta"] = self.resposta_correta_combo.currentText()
            for letra, input_widget in self.alternativas_inputs.items():
                dados_questao[f"alternativa_{letra.lower()}"] = input_widget.text().strip()
        elif formato == "Verdadeiro ou Falso":
            dados_questao["resposta_correta"] = "Verdadeiro" if self.vf_verdadeiro_radio.isChecked() else "Falso"

        # --- ETAPA 5: Salvar ou Atualizar no Banco de Dados ---
        try:
            if self.questao_id:
                atualizar_questao(self.questao_id, dados_questao)
                QMessageBox.information(self, "Sucesso", "Questão atualizada com sucesso!")
            else:
                salvar_questao(dados_questao)
                QMessageBox.information(self, "Sucesso", "Questão salva com sucesso!")
            
            self.questao_atualizada.emit()
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Erro no Banco de Dados", f"Não foi possível salvar a questão:\n{e}")
    
    def _criar_botao_formatacao(self, text, func, tooltip):
        btn = QToolButton()
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
            "Sortear Inteiro (randint)": "numero = random.randint(min, max)",
            "Sortear Decimal (uniform)": "numero = random.uniform(min, max)",
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
    
    def _inserir_imagem_arquivo(self):
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