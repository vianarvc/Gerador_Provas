# interface/visualizar_questoes.py

import os
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QPushButton, 
    QTextEdit, QScrollArea, QMessageBox, QDesktopWidget, QStackedWidget,
    QComboBox
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt

# Importações de funções do banco de dados (incluindo as de disciplina)
from database import (
    obter_disciplinas, obter_disciplina_id_por_nome, obter_temas, 
    obter_questoes_por_tema, excluir_questao, salvar_ordem_temas, obter_disciplina_nome_por_id
)
from .cadastro_questao import CadastroQuestaoWindow
from .custom_widgets import NoScrollComboBox

class VisualizarQuestoesWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visualizar Banco de Questões")
        self.resize(1100, 750)
        
        self.edit_window = None
        self.questoes_atuais = []
        self.id_questao_selecionada = None

        # --- Estrutura Principal com QStackedWidget ---
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        self.stacked_widget = QStackedWidget()
        layout_principal.addWidget(self.stacked_widget)

        # --- Cria as duas "telas" ---
        self.tela_listagem = self._criar_tela_listagem()
        self.tela_detalhes = self._criar_tela_detalhes()

        self.stacked_widget.addWidget(self.tela_listagem)
        self.stacked_widget.addWidget(self.tela_detalhes)

        # Aplica o estilo e carrega os dados iniciais
        self._aplicar_estilos()
        self._carregar_disciplinas()
        self._center()

    def _aplicar_estilos(self):
        style = """
        /* ... (O seu QSS completo que você já me enviou) ... */
        /* GERAL */
        QWidget { background-color: #f7f7f7; font-family: Arial; }
        /* TÍTULOS */
        #TituloSecundario { font-size: 16px; font-weight: bold; color: #2c3e50; padding: 5px 0; border-bottom: 1px solid #bdc3c7; }
        /* PAINEL DE LISTAS (Temas e Questões) */
        QListWidget { border: 1px solid #bdc3c7; border-radius: 5px; padding: 5px; background-color: white; outline: 0; }
        QListWidget::item { padding: 5px; border-bottom: 1px solid #ecf0f1; }
        QListWidget::item:selected { background-color: #3498db; color: white; }
        /* COMBOBOX */
        QComboBox { border: 1px solid #bdc3c7; border-radius: 5px; padding: 5px; background-color: white; }
        /* SCROLL AREA DOS DETALHES */
        #ScrollDetalhes { border: 1px solid #bdc3c7; border-radius: 5px; background-color: #ffffff; }
        /* TEXT EDITORS (Enunciado/Parâmetros) */
        QTextEdit { border: 1px solid #bdc3c7; border-radius: 4px; padding: 5px; background-color: #fdfdfd; }
        /* BOTÕES DE AÇÃO (GERAL) */
        QPushButton {
            border: none;
            border-radius: 5px;
            padding: 8px 15px;
            font-size: 26px; /* Aumenta a fonte de todos os botões */
            font-weight: bold;
            min-height: 30px;
            margin-top: 5px;
        }

        /* BOTÃO PRIMÁRIO (Editar) */
        #BotaoPrimario {
            background-color: #3498db; /* Azul */
            color: white;
        }
        #BotaoPrimario:hover {
            background-color: #2980b9; 
        }

        /* BOTÃO DE EXCLUIR */
        #BotaoExcluir {
            background-color: #e74c3c; /* Vermelho */
            color: white;
        }
        #BotaoExcluir:hover {
            background-color: #c0392b;
        }

        /* BOTÃO VOLTAR */
        #BotaoVoltar {
            background-color: #95a5a6; /* Cinza */
            color: white;
        /* A linha 'font-weight: normal;' foi removida para herdar o 'bold' do estilo geral */
        }
        #BotaoVoltar:hover {
            background-color: #7f8c8d;
        }
        /* LABELS NO DETALHE */
        QLabel { color: #2c3e50; padding-top: 5px; }
        """
        self.setStyleSheet(style)

    def _criar_tela_listagem(self):
        """Cria e retorna o widget da tela de listagem."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # --- Filtro de Disciplina (Topo) ---
        filtro_layout = QHBoxLayout()
        label_disciplina = QLabel("<b>Disciplina:</b>")
        self.disciplina_combo = NoScrollComboBox()
        filtro_layout.addWidget(label_disciplina)
        filtro_layout.addWidget(self.disciplina_combo, 1)
        layout.addLayout(filtro_layout)

        # --- Painéis de Listas (Meio) ---
        listas_layout = QHBoxLayout()
        
        # Painel Esquerdo: Temas
        painel_temas = QWidget()
        layout_temas = QVBoxLayout(painel_temas)
        label_temas = QLabel("<h3>Temas</h3>")
        label_temas.setObjectName("TituloSecundario")
        self.lista_temas = QListWidget()
        self.lista_temas.setDragDropMode(QListWidget.InternalMove) # Reordenar
        self.lista_temas.model().rowsMoved.connect(self._salvar_ordem_atual_temas)
        self.lista_temas.setSortingEnabled(False)
        layout_temas.addWidget(label_temas)
        layout_temas.addWidget(self.lista_temas)
        listas_layout.addWidget(painel_temas,1)

        # Painel Direito: Questões
        painel_questoes = QWidget()
        layout_questoes = QVBoxLayout(painel_questoes)
        label_questoes = QLabel("<h3>Questões</h3>")
        label_questoes.setObjectName("TituloSecundario")
        self.lista_questoes = QListWidget()
        layout_questoes.addWidget(label_questoes)
        layout_questoes.addWidget(self.lista_questoes)
        listas_layout.addWidget(painel_questoes,3)

        layout.addLayout(listas_layout)

        # --- Conexões dos Sinais ---
        self.disciplina_combo.activated.connect(self._disciplina_selecionada)
        self.lista_temas.itemClicked.connect(self._tema_selecionado)
        self.lista_questoes.itemClicked.connect(self.exibir_detalhes_questao)

        return widget

    def _criar_tela_detalhes(self):
        """Cria e retorna o widget da tela de detalhes."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        self.scroll_detalhes = QScrollArea()
        self.scroll_detalhes.setWidgetResizable(True)
        self.scroll_detalhes.setObjectName("ScrollDetalhes")
        
        self.widget_conteudo_detalhes = QWidget()
        self.layout_conteudo_detalhes = QVBoxLayout(self.widget_conteudo_detalhes)
        self.layout_conteudo_detalhes.setContentsMargins(15, 15, 15, 15)
        self.layout_conteudo_detalhes.setAlignment(Qt.AlignTop)
        self.scroll_detalhes.setWidget(self.widget_conteudo_detalhes)
        
        # --- NOVO BLOCO: Botões de Ação da Questão (Criados apenas uma vez) ---
        botoes_inferiores_layout = QHBoxLayout()
        botoes_inferiores_layout.addStretch() # Empurra TODOS os botões para a direita

        # Cria e adiciona o botão Editar
        self.btn_editar = QPushButton("✏️ Editar Questão")
        self.btn_editar.setObjectName("BotaoPrimario")
        self.btn_editar.clicked.connect(self.abrir_edicao)
        botoes_inferiores_layout.addWidget(self.btn_editar)
        
        # Cria e adiciona o botão Excluir
        self.btn_excluir = QPushButton("❌ Excluir Questão")
        self.btn_excluir.setObjectName("BotaoExcluir")
        self.btn_excluir.clicked.connect(self.confirmar_exclusao)
        botoes_inferiores_layout.addWidget(self.btn_excluir)

        # Cria e adiciona o botão Voltar
        self.btn_voltar_lista = QPushButton("↩️ Voltar para a Lista")
        self.btn_voltar_lista.setObjectName("BotaoVoltar")
        self.btn_voltar_lista.clicked.connect(self._voltar_para_lista)
        botoes_inferiores_layout.addWidget(self.btn_voltar_lista)
        
        # Adiciona o scroll de detalhes e o layout unificado dos botões ao layout principal
        layout.addWidget(self.scroll_detalhes)
        layout.addLayout(botoes_inferiores_layout)
        
        return widget

    # --- Lógica de Carregamento de Dados ---
    def _carregar_disciplinas(self):
        self.disciplina_combo.clear()
        disciplinas = obter_disciplinas() # Sua função já retorna com "Todas"
        
        # Adicionamos um placeholder para forçar a seleção
        disciplinas.insert(0, "-- Selecione uma Disciplina --")
        
        if disciplinas:
            self.disciplina_combo.addItems(disciplinas)
        
        # Limpa as listas de baixo para um estado inicial limpo
        self.lista_temas.clear()
        self.lista_questoes.clear()

    def _disciplina_selecionada(self):
        disciplina_nome = self.disciplina_combo.currentText()

        # --- LINHAS NOVAS ---
        # Se o placeholder estiver selecionado, limpa as listas e não faz nada
        if disciplina_nome == "-- Selecione uma Disciplina --":
            self.lista_temas.clear()
            self.lista_questoes.clear()
            return
        # --- FIM DAS LINHAS NOVAS ---
            
        disciplina_id = obter_disciplina_id_por_nome(disciplina_nome)
        
        self.lista_temas.clear()
        self.lista_questoes.clear()
        
        temas = obter_temas(disciplina_id=disciplina_id)
        if temas:
            self.lista_temas.addItems(temas)
    
    def _tema_selecionado(self, item):
        if not item: return
        tema = item.text()
        disciplina_id = obter_disciplina_id_por_nome(self.disciplina_combo.currentText())

        self.lista_questoes.clear()
        self.questoes_atuais = obter_questoes_por_tema(tema, disciplina_id)
        for q in self.questoes_atuais:
            status = "[ATIVA]" if q.get("ativa", 1) else "[INATIVA]"
            resumo = q["enunciado"].replace('\n', ' ')
            if len(resumo) > 70: resumo = resumo[:70] + "..."
            self.lista_questoes.addItem(f"{status} ID {q['id']}: {resumo}")

    # --- Lógica de Navegação e Exibição ---
    def exibir_detalhes_questao(self, item):
        indice = self.lista_questoes.currentRow()
        if indice < 0 or indice >= len(self.questoes_atuais): return
        
        questao = self.questoes_atuais[indice]
        self.id_questao_selecionada = questao['id']
        
        # Limpa o layout de detalhes anterior
        while self.layout_conteudo_detalhes.count():
            child = self.layout_conteudo_detalhes.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        # Preenche com os novos detalhes
        fonte_normal = QFont("Arial", 12)

        self.layout_conteudo_detalhes.addWidget(self.criar_label(f"<b>ID da Questão:</b> {questao['id']}", fonte_normal))
        
        status_texto = "ATIVA" if questao.get("ativa", 1) else "INATIVA"
        status_cor = "green" if questao.get("ativa", 1) else "red"
        self.layout_conteudo_detalhes.addWidget(self.criar_label(f"<b>Status:</b> <span style='color:{status_cor};'>{status_texto}</span>", fonte_normal))
        
        # Adiciona a Disciplina 
        disciplina_nome = obter_disciplina_nome_por_id(questao.get("disciplina_id"))
        self.layout_conteudo_detalhes.addWidget(self.criar_label(f"<b>Disciplina:</b> {disciplina_nome}", fonte_normal))
        
        self.layout_conteudo_detalhes.addWidget(self.criar_label(f"<b>Tema:</b> {questao['tema']}", fonte_normal))
        self.layout_conteudo_detalhes.addWidget(self.criar_label(f"<b>Formato:</b> {questao['formato_questao']}", fonte_normal))
        self.layout_conteudo_detalhes.addWidget(self.criar_label(f"<b>Dificuldade:</b> {questao['dificuldade']}", fonte_normal))
        if questao.get("fonte"):
            self.layout_conteudo_detalhes.addWidget(self.criar_label(f"<b>Fonte:</b> {questao['fonte']}", fonte_normal))
        
        self.layout_conteudo_detalhes.addWidget(self.criar_label("<b>Enunciado:</b>", fonte_normal))
        txt_enunciado = QTextEdit()
        txt_enunciado.setReadOnly(True)
        txt_enunciado.setPlainText(questao["enunciado"])
        txt_enunciado.document().adjustSize()
        txt_enunciado.setFixedHeight(int(txt_enunciado.document().size().height() + 10))
        self.layout_conteudo_detalhes.addWidget(txt_enunciado)
        
        caminho_imagem = questao.get("imagem")
        if caminho_imagem and os.path.exists(caminho_imagem):
            self.layout_conteudo_detalhes.addWidget(self.criar_label("<b>Imagem:</b>", fonte_normal))
            lbl_imagem = QLabel()
            pixmap = QPixmap(caminho_imagem)
            lbl_imagem.setPixmap(pixmap.scaledToWidth(400, Qt.SmoothTransformation))
            self.layout_conteudo_detalhes.addWidget(lbl_imagem)
            
        if questao.get("parametros"):
            self.layout_conteudo_detalhes.addWidget(self.criar_label(f"<b>Parâmetros ({questao.get('tipo_questao', 'N/A')}):</b>", fonte_normal))
            txt_parametros = QTextEdit()
            txt_parametros.setReadOnly(True)
            txt_parametros.setFont(QFont("Courier", 10))
            try:
                txt_parametros.setText(json.dumps(json.loads(questao["parametros"]), indent=4, ensure_ascii=False))
            except:
                txt_parametros.setText(questao.get("parametros", ""))
            txt_parametros.setFixedHeight(150)
            self.layout_conteudo_detalhes.addWidget(txt_parametros)
        
        if questao['formato_questao'] == 'Múltipla Escolha':
            self.layout_conteudo_detalhes.addWidget(self.criar_label("<b>Alternativas e Resposta:</b>", fonte_normal))
            if questao.get("gerar_alternativas_auto"):
                self.layout_conteudo_detalhes.addWidget(self.criar_label("<i>As alternativas são geradas numericamente.</i>", fonte_normal))
            else:
                for letra in ["a", "b", "c", "d", "e"]:
                    alt = questao.get(f"alternativa_{letra}")
                    if alt: self.layout_conteudo_detalhes.addWidget(self.criar_label(f"&nbsp;&nbsp;<b>{letra.upper()})</b> {alt}", fonte_normal))
                if questao.get("resposta_correta"):
                    self.layout_conteudo_detalhes.addWidget(self.criar_label(f"<b>Resposta Correta:</b> <span style='color:green;'>{questao['resposta_correta']}</span>", fonte_normal))

        self.stacked_widget.setCurrentWidget(self.tela_detalhes)

    def _voltar_para_lista(self):
        self.stacked_widget.setCurrentWidget(self.tela_listagem)
        self.refresh_geral() # Atualiza as listas ao voltar

    # --- Funções Auxiliares (Editar, Excluir, etc.) ---
    def abrir_edicao(self):
        if self.id_questao_selecionada is None: return
        self.edit_window = CadastroQuestaoWindow(questao_id=self.id_questao_selecionada)
        self.edit_window.questao_atualizada.connect(self.refresh_geral)
        self.edit_window.show()

    def confirmar_exclusao(self):
        if self.id_questao_selecionada is None: return
        reply = QMessageBox.question(self, "Confirmar Exclusão", f"Tem certeza que deseja excluir a questão ID {self.id_questao_selecionada}?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if excluir_questao(self.id_questao_selecionada):
                QMessageBox.information(self, "Sucesso", "Questão excluída!")
                self._voltar_para_lista()
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível excluir a questão.")

    def refresh_geral(self):
        disciplina_selecionada_texto = self.disciplina_combo.currentText()
        tema_selecionado_item = self.lista_temas.currentItem()
        tema_selecionado_texto = tema_selecionado_item.text() if tema_selecionado_item else None
        
        self._carregar_disciplinas()
        
        # Tenta reselecionar a disciplina
        index_disc = self.disciplina_combo.findText(disciplina_selecionada_texto)
        if index_disc != -1:
            self.disciplina_combo.setCurrentIndex(index_disc)
            self._disciplina_selecionada() # Recarrega os temas
        
        # Tenta reselecionar o tema
        if tema_selecionado_texto:
            items = self.lista_temas.findItems(tema_selecionado_texto, Qt.MatchExactly)
            if items:
                self.lista_temas.setCurrentItem(items[0])
                self._tema_selecionado(items[0]) # Recarrega as questões
    
    def criar_label(self, texto, fonte):
        lbl = QLabel(texto); lbl.setFont(fonte); lbl.setWordWrap(True); return lbl

    def _center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # Adicione este novo método à sua classe VisualizarQuestoesWindow
    def _salvar_ordem_atual_temas(self):
        """Pega a ordem atual dos temas da lista e a salva instantaneamente."""
        try:
            disciplina_nome = self.disciplina_combo.currentText()
            disciplina_id = obter_disciplina_id_por_nome(disciplina_nome)

            # Só salva se uma disciplina específica estiver selecionada
            if disciplina_id:
                ordem_atual_temas = []
                for i in range(self.lista_temas.count()):
                    ordem_atual_temas.append(self.lista_temas.item(i).text())

                # Remove "Todos" da lista antes de salvar, se ele existir
                if "Todos" in ordem_atual_temas:
                    ordem_atual_temas.remove("Todos")

                if ordem_atual_temas:
                    salvar_ordem_temas(ordem_atual_temas, disciplina_id)
        except Exception as e:
            print(f"Erro ao salvar a ordem dos temas: {e}")