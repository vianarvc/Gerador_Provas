# interface/main_window.py

import os
import shutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QDesktopWidget, QAction,
    QMessageBox, QFileDialog, QDialog, QScrollArea, QVBoxLayout, QLabel,
    QPushButton, QToolBar, QAction, QToolButton, QMenu
)
from PyQt5.QtCore import Qt
from .custom_widgets import MeuBotao, EstilosApp

from .MenuInicial import MenuInicialWindow as MainMenuScreen
from .visualizar_questoes import VisualizarQuestoesScreen
from .cadastro_questao import CadastroQuestaoScreen
from .gerador_por_id import GeradorPorIdScreen
from .gerador_provas import GeradorProvasScreen

from .configuracoes_dialog import ConfiguracoesDialog
from .selecao_modo_geracao import SelecaoModoGeracaoDialog
from .filtro_cardapio_dialog import FiltroCardapioDialog
from .log_dialog import LogDialog
import motor_gerador

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.navigation_history = []
        self.setWindowTitle("Gerador de Provas")
        self.is_first_show = True
        EstilosApp.aplicar_estilo_janela_principal(self)
        
        # 1. Chamamos o novo método que cria nossa barra superior única
        self._criar_barra_superior_unificada()
        
        # 2. O QStackedWidget continua sendo o widget central
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Criação das telas
        self.main_menu = MainMenuScreen()
        self.visualizar_screen = VisualizarQuestoesScreen()
        self.cadastro_screen = CadastroQuestaoScreen()
        self.gerador_id_screen = GeradorPorIdScreen()
        self.gerador_criterios_screen = GeradorProvasScreen()

        # Adição à pilha
        self.stacked_widget.addWidget(self.main_menu)
        self.stacked_widget.addWidget(self.visualizar_screen)
        self.stacked_widget.addWidget(self.cadastro_screen)
        self.stacked_widget.addWidget(self.gerador_id_screen)
        self.stacked_widget.addWidget(self.gerador_criterios_screen)

        # Conexões de sinais
        self.main_menu.cadastrar_questao_pressed.connect(self.show_cadastro_para_criacao)
        self.main_menu.visualizar_questoes_pressed.connect(self.show_visualizar_questoes)
        self.main_menu.gerar_cardapio_pressed.connect(self._abrir_gerador_cardapio)
        self.main_menu.gerar_prova_pressed.connect(self.abrir_gerador_prova)
        
        # --- CONEXÕES DA TELA DE VISUALIZAÇÃO ---
        self.visualizar_screen.back_to_main_menu_pressed.connect(self.navigate_back)
        self.visualizar_screen.edit_questao_pressed.connect(self.show_cadastro_para_edicao)
        
        # --- CONEXÕES DA TELA DE CADASTRO ---
        self.cadastro_screen.cadastro_concluido.connect(self.ao_concluir_cadastro)
        self.cadastro_screen.voltar_pressed.connect(self.navigate_back)
        
        # --- CONEXÕES DOS GERADORES ---
        self.gerador_id_screen.voltar_pressed.connect(self.navigate_back)
        self.gerador_criterios_screen.voltar_pressed.connect(self.navigate_back)

        self.gerador_window = None
        self.previous_screen = None

        # CONECTA O SINAL DE TROCA DE TELA AO MÉTODO DE AJUSTE
        self.stacked_widget.currentChanged.connect(self._on_screen_changed)

        # FORÇA UMA CHAMADA INICIAL PARA AJUSTAR LOGO AO ABRIR
        self._on_screen_changed(self.stacked_widget.currentIndex())

    def show_cadastro_para_edicao(self, questao_id):
        """Abre a tela de cadastro para edição de uma questão existente"""
        self.cadastro_screen.abrir_para_edicao(questao_id)
        self._navigate_to(self.cadastro_screen)

    def ao_concluir_cadastro(self, questao_id=None):
        """
        Chamado quando uma questão é salva (criação ou edição)
        Se questao_id for None, é uma nova questão
        """
        # Volta para a tela de visualização
        self.stacked_widget.setCurrentWidget(self.visualizar_screen)
        
        # Atualiza a lista de questões
        self.visualizar_screen.refresh_geral()
        
        # Se foi uma edição (questao_id existe), atualiza os detalhes
        if questao_id is not None:
            self.visualizar_screen.atualizar_detalhes_apos_edicao(questao_id)
        
        # Opcional: Mostra mensagem de sucesso
        if questao_id:
            QMessageBox.information(self, "Sucesso", f"Questão ID {questao_id} salva com sucesso!")
        else:
            QMessageBox.information(self, "Sucesso", "Nova questão criada com sucesso!")

    def showEvent(self, event):
        """ É chamado ANTES de a janela ser exibida. """
        super().showEvent(event)
        # Se for a primeira vez...
        if self.is_first_show:
            # ...redimensiona para o menu e centraliza.
            self.resize(self.main_menu.sizeHint())
            self._center()
            # Desativa a flag para não executar novamente.
            self.is_first_show = False

    def _center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def show_main_menu(self):
        self.navigation_history.clear() # Limpa o histórico ao voltar para o menu
        self.stacked_widget.setCurrentWidget(self.main_menu)
        '''self.resize(self.main_menu.sizeHint())
        self._center()'''

    def show_visualizar_questoes(self):
        self.visualizar_screen.refresh_geral() 
        self.stacked_widget.setCurrentWidget(self.visualizar_screen)
        '''self.resize(self.visualizar_screen.sizeHint())
        self._center()'''

    def show_cadastro_para_criacao(self):
        """Abre a tela de cadastro para criar uma nova questão"""
        self.cadastro_screen.abrir_para_criacao()
        self._navigate_to(self.cadastro_screen)

    def show_cadastro_para_edicao(self, questao_id):
        self.cadastro_screen.abrir_para_edicao(questao_id)
        self._navigate_to(self.cadastro_screen)
        '''self.resize(self.cadastro_screen.sizeHint())
        self._center()'''

    def show_gerador_por_id(self):
        self.gerador_id_screen._limpar_campos()
        self._navigate_to(self.gerador_id_screen)
        '''self.resize(self.gerador_id_screen.sizeHint())
        self._center()'''

    def show_gerador_por_criterios(self):
        """Prepara e exibe a tela de geração por critérios."""
        self.gerador_criterios_screen._limpar_campos()
        self._navigate_to(self.gerador_criterios_screen)
        '''self.resize(self.gerador_criterios_screen.sizeHint())
        self._center()'''
    
    def navigate_back(self):
        """
        Volta para a tela anterior. Primeiro tenta a navegação interna da tela atual.
        """
        current_widget = self.stacked_widget.currentWidget()

        # Verifica se a tela atual tem um método para navegação interna
        if hasattr(current_widget, 'navigate_back_internal'):
            # Tenta executar a navegação interna e verifica se foi bem-sucedida
            was_handled = current_widget.navigate_back_internal()
            if was_handled:
                return  # Se a tela filha resolveu, o trabalho da MainWindow termina aqui.

        # Se a navegação interna não foi tratada (ou não existe),
        # usa o histórico principal da MainWindow.
        if self.navigation_history:
            previous_widget = self.navigation_history.pop()
            self.stacked_widget.setCurrentWidget(previous_widget)
        else:
            self.show_main_menu() # Fallback de segurança

    def _navigate_to(self, target_widget):
        """Função central para navegar, registrando o histórico antes de trocar de tela."""
        current = self.stacked_widget.currentWidget()
        # Adiciona ao histórico apenas se estivermos realmente mudando de tela
        if current != target_widget:
            self.navigation_history.append(current)
        self.stacked_widget.setCurrentWidget(target_widget)

    def _criar_barra_superior_unificada(self):
        # 1. Crie a QToolBar, que será nossa única barra superior
        self.top_bar = QToolBar("Barra Principal")
        self.top_bar.setMovable(False)
        self.top_bar.setObjectName("TopBar")

        # 2. Altera o botão Voltar para ser um ícone (QToolButton)
        self.btn_voltar_fixo = QToolButton()
        self.btn_voltar_fixo.setText("←") # Ícone de seta para a esquerda
        self.btn_voltar_fixo.setObjectName("VoltarToolButton")
        self.btn_voltar_fixo.setToolTip("Voltar ao Menu") # Dica de ferramenta
        self.btn_voltar_fixo.clicked.connect(self.navigate_back)
        self.top_bar.addWidget(self.btn_voltar_fixo)
        
        # --- Menu Dados ---
        menu_dados_btn = QToolButton()
        menu_dados_btn.setText("Dados")
        menu_dados_btn.setObjectName("MenuToolButton")
        menu_dados = QMenu(self)
        action_exportar = QAction("Exportar Base de Dados", self)
        action_exportar.triggered.connect(self._exportar_db)
        action_importar = QAction("Importar Base de Dados", self)
        action_importar.triggered.connect(self._importar_db)
        menu_dados.addAction(action_exportar)
        menu_dados.addAction(action_importar)
        menu_dados_btn.setMenu(menu_dados)
        menu_dados_btn.setPopupMode(QToolButton.InstantPopup)
        self.top_bar.addWidget(menu_dados_btn)

        # --- Menu Configurações ---
        menu_config_btn = QToolButton()
        menu_config_btn.setText("Configurações")
        menu_config_btn.setObjectName("MenuToolButton")
        menu_config = QMenu(self)
        action_identificacao = QAction("Identificação...", self)
        action_identificacao.triggered.connect(self.abrir_configuracoes)
        menu_config.addAction(action_identificacao)
        menu_config_btn.setMenu(menu_config)
        menu_config_btn.setPopupMode(QToolButton.InstantPopup)
        self.top_bar.addWidget(menu_config_btn)

        # --- Menu Ajuda ---
        menu_ajuda_btn = QToolButton()
        menu_ajuda_btn.setText("Ajuda")
        menu_ajuda_btn.setObjectName("MenuToolButton")
        menu_ajuda = QMenu(self)
        action_sobre = QAction("Sobre...", self)
        action_sobre.triggered.connect(self._mostrar_janela_sobre)
        menu_ajuda.addAction(action_sobre)
        menu_ajuda_btn.setMenu(menu_ajuda)
        menu_ajuda_btn.setPopupMode(QToolButton.InstantPopup)
        self.top_bar.addWidget(menu_ajuda_btn)

        # 5. Adiciona a barra unificada à janela
        self.addToolBar(self.top_bar)

    def abrir_gerador_prova(self):
        dialogo = SelecaoModoGeracaoDialog(self)
        if dialogo.exec_() != QDialog.Accepted: return
        if dialogo.choice == 'criterios':
            self.show_gerador_por_criterios()
        elif dialogo.choice == 'ids':
            self.show_gerador_por_id()

    def abrir_configuracoes(self):
        dialog = ConfiguracoesDialog(self)
        dialog.exec_()

    def _exportar_db(self):
        db_path = "banco_questoes.db"
        if not os.path.exists(db_path):
            QMessageBox.critical(self, "Erro", "Arquivo do banco de dados não encontrado!")
            return
        destination, _ = QFileDialog.getSaveFileName(self, "Exportar Base de Dados para...", os.path.expanduser("~/backup_banco_questoes.db"), "Arquivos de Banco de Dados (*.db)")
        if destination:
            try:
                shutil.copy(db_path, destination)
                QMessageBox.information(self, "Sucesso", f"Base de dados exportada com sucesso para:\n{destination}")
            except Exception as e:
                QMessageBox.critical(self, "Erro na Exportação", f"Não foi possível copiar o arquivo: {e}")

    def _importar_db(self):
        db_path = "banco_questoes.db"
        reply = QMessageBox.warning(self, "Atenção! Ação Irreversível!", "Esta ação irá **SUBSTITUIR** sua base de dados atual. Todo o seu trabalho não salvo será perdido.\n\n" "É altamente recomendável que você faça um backup (usando a função 'Exportar') antes de continuar.\n\n" "Deseja continuar com a importação?", QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
        if reply != QMessageBox.Yes: return
        source, _ = QFileDialog.getOpenFileName(self, "Importar Base de Dados de...", os.path.expanduser("~"), "Arquivos de Banco de Dados (*.db)")
        if source:
            try:
                shutil.copy(source, db_path)
                QMessageBox.information(self, "Sucesso", "Base de dados importada com sucesso!\n\n" "É recomendável **reiniciar o programa**.")
            except Exception as e:
                QMessageBox.critical(self, "Erro na Importação", f"Não foi possível copiar o arquivo: {e}")

    def _mostrar_janela_sobre(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Sobre o Gerador de Provas")
        dialog.setFixedSize(800, 500)
        layout = QVBoxLayout(dialog)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        texto_licenca = """<h3>Gerador de Provas Automático v1.0
        </h3><p>Copyright (c) 2025 Raphael Viana Cruz.
        </p><hr><p>Este software é licenciado sob a <b>Creative Commons Atribuição-NãoComercial-SemDerivações 4.0 Internacional (CC BY-NC-ND 4.0)</b>.
        </p><p><b>Você tem a liberdade de:</b></p><ul><li><b>Compartilhar</b> — copiar e redistribuir o material em qualquer suporte ou formato para fins não comerciais.</li></ul><p><b>Sob os seguintes termos:</b></p><ul><li><b>Atribuição</b> — Você deve dar o crédito apropriado ao autor original.</li><li><b>NãoComercial</b> — Você não pode usar o material para fins comerciais.</li><li><b>SemDerivações</b> — Se você modificar ou transformar o material, você não pode distribuir o material modificado.</li><li><b>Sem restrições adicionais</b> — Você não pode aplicar termos legais ou medidas de caráter tecnológico que restrinjam legalmente outros de fazerem algo que a licença permita.</li></ul><p>Qualquer uso para fins comerciais ou distribuição de versões modificadas requer autorização prévia e por escrito do autor.</p><p>Este é um resumo legível por humanos. Para ler a licença completa, acesse:</p><p><a href="http://creativecommons.org/licenses/by-nc-nd/4.0/">creativecommons.org/licenses/by-nc-nd/4.0</a></p><br><p><b>Contato:</b> raphael.cruz@gsuite.iff.edu.br</p>"""
        label_texto = QLabel(texto_licenca)
        label_texto.setWordWrap(True)
        label_texto.setAlignment(Qt.AlignTop)
        label_texto.setContentsMargins(10, 10, 10, 10)
        scroll_area.setWidget(label_texto)
        botao_ok = QPushButton("OK")
        botao_ok.clicked.connect(dialog.accept)
        layout.addWidget(scroll_area)
        layout.addWidget(botao_ok)
        dialog.exec_()

    def _abrir_gerador_cardapio(self):
        dialogo_filtro = FiltroCardapioDialog(self)
        if dialogo_filtro.exec_() != QDialog.Accepted: return
        disciplina_id = dialogo_filtro.disciplina_id
        tema = dialogo_filtro.tema
        caminho_sugerido = os.path.expanduser("~/Cardapio_de_Questoes.pdf")
        caminho_salvar, _ = QFileDialog.getSaveFileName(self, "Salvar Cardápio como...", caminho_sugerido, "Arquivos PDF (*.pdf)")
        if not caminho_salvar: return
        log_dialog = LogDialog(self)
        log_dialog.show()
        try:
            sucesso, mensagem = motor_gerador.gerar_cardapio_questoes(caminho_salvar, disciplina_id, tema, log_dialog)
            log_dialog.finish(success=sucesso)
            if sucesso:
                QMessageBox.information(self, "Sucesso", mensagem)
            else:
                QMessageBox.critical(self, "Erro na Geração", mensagem)
        except Exception as e:
            if log_dialog: log_dialog.finish(success=False)
            QMessageBox.critical(self, "Erro Inesperado", f"Ocorreu um erro fatal:\n{e}")

    def _on_screen_changed(self, index):
        current_widget = self.stacked_widget.widget(index)
        if current_widget:
            self.setWindowTitle(f"Gerador de Provas - {current_widget.windowTitle()}")

            # Controle do botão "Voltar"
            is_main_menu = (current_widget == self.main_menu)
            self.btn_voltar_fixo.setVisible(not is_main_menu)

            # --- DIMENSIONAMENTO PRECISO E TRAVADO ---

            # Ajusta tamanhos para obter valores reais
            self.top_bar.adjustSize()
            current_widget.adjustSize()

            bar_width = self.top_bar.minimumSizeHint().width()
            screen_hint = current_widget.sizeHint()

            # Calcula a largura final com base na tela atual
            final_width = max(screen_hint.width(), bar_width)

            # Adiciona altura da barra ao total
            total_height = screen_hint.height() + self.top_bar.height()

            # Define o tamanho fixo e centraliza
            self.setFixedSize(final_width, total_height)
            self._center()