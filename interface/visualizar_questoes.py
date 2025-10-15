# interface/visualizar_questoes.py

import os
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QPushButton,
    QTextEdit, QScrollArea, QMessageBox, QDesktopWidget, QStackedWidget,
    QComboBox, QMenu, QInputDialog
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, QSize  # --- MUDANÇA 1: Novas importações ---

# Importações de funções do banco de dados (sem alteração)
from database import (
    obter_disciplinas, obter_disciplina_id_por_nome, obter_temas,
    obter_questoes_por_tema, excluir_questao, salvar_ordem_temas, 
    obter_disciplina_nome_por_id, renomear_tema
)
# A importação do CadastroQuestaoWindow não é mais necessária aqui
# from .cadastro_questao import CadastroQuestaoWindow
from .custom_widgets import (
    NoScrollComboBox, MeuBotao, MeuLineEdit, 
    MeuComboBox, MeuGroupBox, MeuCheckBox, MeuLabel, EstilosApp
)

# --- MUDANÇA 2: Renomear a classe para "Screen" ---
class VisualizarQuestoesScreen(QWidget):
    # --- MUDANÇA 3: Sinais para comunicação com a MainWindow ---
    # Sinal emitido para voltar ao menu principal
    back_to_main_menu_pressed = pyqtSignal()
    # Sinal emitido para abrir a tela de edição, levando o ID da questão
    edit_questao_pressed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Banco de Questões")

        self.questoes_atuais = []
        self.id_questao_selecionada = None

        # A estrutura interna com QStackedWidget para alternar entre lista e detalhes continua a mesma
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        self.stacked_widget = QStackedWidget()
        layout_principal.addWidget(self.stacked_widget)

        self.tela_listagem = self._criar_tela_listagem()
        self.tela_detalhes = self._criar_tela_detalhes()

        self.stacked_widget.addWidget(self.tela_listagem)
        self.stacked_widget.addWidget(self.tela_detalhes)

        self._carregar_disciplinas()

    # --- MUDANÇA 5: Adicionar o método sizeHint ---
    def sizeHint(self):
        """Informa à MainWindow qual o tamanho ideal para esta tela."""
        return QSize(1100, 750)

    def _criar_tela_listagem(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # Filtro de Disciplina
        filtro_layout = QHBoxLayout()
        label_disciplina = QLabel("<b>Disciplina:</b>")
        # --- MUDANÇA 1: Usa MeuComboBox ---
        self.disciplina_combo = MeuComboBox()
        filtro_layout.addWidget(label_disciplina)
        filtro_layout.addWidget(self.disciplina_combo, 1)
        layout.addLayout(filtro_layout)

        # Painéis de Listas
        listas_layout = QHBoxLayout()
        painel_temas = QWidget()
        layout_temas = QVBoxLayout(painel_temas)
        label_temas = QLabel("<h3>Temas</h3>")
        label_temas.setObjectName("TituloSecundario")
        self.lista_temas = QListWidget()
        self.lista_temas.setMinimumWidth(300)
        self.lista_temas.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lista_temas.customContextMenuRequested.connect(self._abrir_menu_contexto_tema)
        self.lista_temas.setDragDropMode(QListWidget.InternalMove)
        self.lista_temas.model().rowsMoved.connect(self._salvar_ordem_atual_temas)
        self.lista_temas.setSortingEnabled(False)
        layout_temas.addWidget(label_temas)
        layout_temas.addWidget(self.lista_temas)
        listas_layout.addWidget(painel_temas, 1)

        painel_questoes = QWidget()
        layout_questoes = QVBoxLayout(painel_questoes)
        label_questoes = QLabel("<h3>Questões</h3>")
        label_questoes.setObjectName("TituloSecundario")
        self.lista_questoes = QListWidget()
        layout_questoes.addWidget(label_questoes)
        layout_questoes.addWidget(self.lista_questoes)
        listas_layout.addWidget(painel_questoes, 3)
        layout.addLayout(listas_layout)

        # --- MUDANÇA 2: Usa MeuBotao ---
        '''self.btn_voltar_menu = MeuBotao("↩️ Voltar ao Menu", tipo="voltar")
        self.btn_voltar_menu.clicked.connect(self.back_to_main_menu_pressed.emit)
        
        # Adiciona o botão no canto inferior esquerdo
        botoes_layout = QHBoxLayout()
        botoes_layout.addWidget(self.btn_voltar_menu)
        botoes_layout.addStretch()
        layout.addLayout(botoes_layout)'''

        # Conexões de sinais
        self.disciplina_combo.activated.connect(self._disciplina_selecionada)
        self.lista_temas.itemClicked.connect(self._tema_selecionado)
        self.lista_questoes.itemClicked.connect(self.exibir_detalhes_questao)

        return widget

    def _criar_tela_detalhes(self):
        # A criação desta tela interna continua a mesma
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
        
        botoes_inferiores_layout = QHBoxLayout()
        botoes_inferiores_layout.addStretch()

        # --- MUDANÇA: Substitui QPushButton por MeuBotao ---
        '''self.btn_voltar_lista = MeuBotao("↩️ Voltar para a Lista", tipo="voltar")
        self.btn_voltar_lista.clicked.connect(self._voltar_para_lista)
        botoes_inferiores_layout.addWidget(self.btn_voltar_lista)'''

        self.btn_editar = MeuBotao("✏️ Editar Questão", tipo="editar")
        self.btn_editar.clicked.connect(self.abrir_edicao)
        botoes_inferiores_layout.addWidget(self.btn_editar)
        
        self.btn_excluir = MeuBotao("❌ Excluir Questão", tipo="excluir")
        self.btn_excluir.clicked.connect(self.confirmar_exclusao)
        botoes_inferiores_layout.addWidget(self.btn_excluir)
        
        layout.addWidget(self.scroll_detalhes)
        layout.addLayout(botoes_inferiores_layout)
        
        return widget

    # --- Lógica de Carregamento (sem grandes alterações) ---
    def _carregar_disciplinas(self):
        # ... seu código aqui permanece o mesmo
        self.disciplina_combo.clear()
        disciplinas = obter_disciplinas()
        disciplinas.insert(0, "-- Selecione uma Disciplina --")
        if disciplinas:
            self.disciplina_combo.addItems(disciplinas)
        self.lista_temas.clear()
        self.lista_questoes.clear()

    def _disciplina_selecionada(self):
        # ... seu código aqui permanece o mesmo
        disciplina_nome = self.disciplina_combo.currentText()
        if disciplina_nome == "-- Selecione uma Disciplina --":
            self.lista_temas.clear()
            self.lista_questoes.clear()
            return
        disciplina_id = obter_disciplina_id_por_nome(disciplina_nome)
        self.lista_temas.clear()
        self.lista_questoes.clear()
        temas = obter_temas(disciplina_id=disciplina_id)
        if temas:
            self.lista_temas.addItems(temas)
    
    def _tema_selecionado(self, item):
        # ... seu código aqui permanece o mesmo
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

    # --- Lógica de Navegação e Exibição (com uma mudança crucial) ---
    def exibir_detalhes_questao(self, item):
        indice = self.lista_questoes.currentRow()
        if indice < 0 or indice >= len(self.questoes_atuais):
            return
        
        questao = self.questoes_atuais[indice]
        self.id_questao_selecionada = questao['id']
        
        # Limpa o layout de detalhes de qualquer conteúdo anterior
        while self.layout_conteudo_detalhes.count():
            child = self.layout_conteudo_detalhes.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Preenche o layout com os novos detalhes da questão
        fonte_normal = QFont("Arial", 12)

        self.layout_conteudo_detalhes.addWidget(self.criar_label(f"<b>ID da Questão:</b> {questao['id']}", fonte_normal))
        
        status_texto = "ATIVA" if questao.get("ativa", 1) else "INATIVA"
        status_cor = "green" if questao.get("ativa", 1) else "red"
        self.layout_conteudo_detalhes.addWidget(self.criar_label(f"<b>Status:</b> <span style='color:{status_cor};'>{status_texto}</span>", fonte_normal))
        
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
            # Tenta formatar o JSON para melhor legibilidade
            try:
                # Carrega o JSON string e o re-escreve com indentação
                params_formatted = json.dumps(json.loads(questao["parametros"]), indent=4, ensure_ascii=False)
                txt_parametros.setText(params_formatted)
            except:
                # Se falhar (ex: não for JSON), exibe o texto bruto
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
                    if alt:
                        self.layout_conteudo_detalhes.addWidget(self.criar_label(f"&nbsp;&nbsp;<b>{letra.upper()})</b> {alt}", fonte_normal))
                if questao.get("resposta_correta"):
                    resposta_texto = str(questao['resposta_correta']).upper()
                    self.layout_conteudo_detalhes.addWidget(self.criar_label(f"<b>Resposta Correta:</b> <span style='color:green;'>{resposta_texto}</span>", fonte_normal))

        # Muda para a tela de detalhes
        self.stacked_widget.setCurrentWidget(self.tela_detalhes)

    def _voltar_para_lista(self):
        # Esta função interna está correta
        self.stacked_widget.setCurrentWidget(self.tela_listagem)
        self.refresh_geral()

    # --- MUDANÇA 7: Ações agora emitem sinais ---
    def abrir_edicao(self):
        """Em vez de abrir uma janela, emite um sinal com o ID da questão."""
        if self.id_questao_selecionada is not None:
            self.edit_questao_pressed.emit(self.id_questao_selecionada)

    def confirmar_exclusao(self):
        # Este método pode continuar como está, pois usa um QMessageBox que é modal
        if self.id_questao_selecionada is None: return
        reply = QMessageBox.question(self, "Confirmar Exclusão", f"Tem certeza que deseja excluir a questão ID {self.id_questao_selecionada}?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if excluir_questao(self.id_questao_selecionada):
                QMessageBox.information(self, "Sucesso", "Questão excluída!")
                self._voltar_para_lista()
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível excluir a questão.")

    def refresh_geral(self):
        # Seu código aqui permanece o mesmo, é uma função pública útil
        disciplina_selecionada_texto = self.disciplina_combo.currentText()
        tema_selecionado_item = self.lista_temas.currentItem()
        tema_selecionado_texto = tema_selecionado_item.text() if tema_selecionado_item else None
        
        self._carregar_disciplinas()
        
        index_disc = self.disciplina_combo.findText(disciplina_selecionada_texto)
        if index_disc != -1:
            self.disciplina_combo.setCurrentIndex(index_disc)
            self._disciplina_selecionada()
        
        if tema_selecionado_texto:
            items = self.lista_temas.findItems(tema_selecionado_texto, Qt.MatchExactly)
            if items:
                self.lista_temas.setCurrentItem(items[0])
                self._tema_selecionado(items[0])
    
    def criar_label(self, texto, fonte):
        lbl = QLabel(texto); lbl.setFont(fonte); lbl.setWordWrap(True); return lbl

    # O método _center() não é mais necessário aqui
    # def _center(self): ...

    def _salvar_ordem_atual_temas(self):
        # Seu código aqui permanece o mesmo
        try:
            disciplina_nome = self.disciplina_combo.currentText()
            disciplina_id = obter_disciplina_id_por_nome(disciplina_nome)
            if disciplina_id:
                ordem_atual_temas = []
                for i in range(self.lista_temas.count()):
                    ordem_atual_temas.append(self.lista_temas.item(i).text())
                if "Todos" in ordem_atual_temas:
                    ordem_atual_temas.remove("Todos")
                if ordem_atual_temas:
                    salvar_ordem_temas(ordem_atual_temas, disciplina_id)
        except Exception as e:
            print(f"Erro ao salvar a ordem dos temas: {e}")

    def navigate_back_internal(self):
        """
        Processa a ação de 'voltar' dentro desta tela.
        Retorna True se a ação foi tratada, False caso contrário.
        """
        # Verifica se a tela de detalhes é a que está ativa no momento
        if self.stacked_widget.currentWidget() == self.tela_detalhes:
            # Se for, volta para a tela de listagem
            self.stacked_widget.setCurrentWidget(self.tela_listagem)
            # Retorna True para avisar a MainWindow que o "voltar" foi resolvido aqui
            return True
        
        # Se já estivermos na tela de listagem, não há para onde voltar internamente.
        # Retorna False para que a MainWindow possa assumir o controle.
        return False
    
    # Adicione este novo método à classe VisualizarQuestoesScreen
    def _abrir_menu_contexto_tema(self, pos):
        """
        Abre o menu de contexto ao clicar com o botão direito na lista de temas.
        """
        item = self.lista_temas.itemAt(pos)
        if not item:
            return # Se o clique foi em uma área vazia, não faz nada

        nome_antigo = item.text()

        # Cria o menu e adiciona a ação de renomear
        menu = QMenu()
        acao_renomear = menu.addAction("Renomear Tema...")

        # Mostra o menu na posição do cursor e aguarda a escolha do usuário
        acao_selecionada = menu.exec_(self.lista_temas.mapToGlobal(pos))

        # Se a ação de renomear foi clicada
        if acao_selecionada == acao_renomear:
            # Pede ao usuário o novo nome usando um diálogo simples
            nome_novo, ok = QInputDialog.getText(self, 
                                                "Renomear Tema", 
                                                f"Digite o novo nome para '{nome_antigo}':",
                                                text=nome_antigo)

            # Se o usuário clicou "OK" e o nome é válido
            if ok and nome_novo and nome_novo.strip():
                nome_novo = nome_novo.strip()
                if nome_novo != nome_antigo:
                    # Chama a função do banco de dados para fazer a mágica
                    if renomear_tema(nome_antigo, nome_novo):
                        QMessageBox.information(self, "Sucesso", "Tema renomeado com sucesso em todas as questões.")
                        # Atualiza a lista de temas na tela para refletir a mudança
                        self._disciplina_selecionada()
                    else:
                        QMessageBox.critical(self, "Erro", "Não foi possível renomear o tema no banco de dados.")