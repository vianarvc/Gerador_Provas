# interface/main_window.py

import sys
import os
import shutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QDesktopWidget, QAction,
    QMessageBox, QFileDialog, QDialog, QScrollArea, QVBoxLayout, QLabel,
    QPushButton
)
from PyQt5.QtCore import Qt

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
        self.setWindowTitle("Gerador de Provas")

        self.is_first_show = True
        self._aplicar_estilos()
        self._criar_menu_superior()

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        self.stacked_widget.currentChanged.connect(self._on_screen_changed)
        
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
        self.visualizar_screen.back_to_main_menu_pressed.connect(self.show_main_menu)
        self.visualizar_screen.edit_questao_pressed.connect(self.show_cadastro_para_edicao)
        self.cadastro_screen.cadastro_concluido.connect(self.show_visualizar_questoes)
        self.cadastro_screen.voltar_pressed.connect(self.navigate_back)
        self.gerador_id_screen.voltar_pressed.connect(self.show_main_menu)
        self.gerador_criterios_screen.voltar_pressed.connect(self.show_main_menu)

        self.gerador_window = None
        self.previous_screen = None

        # Chamada inicial
        self.stacked_widget.setCurrentWidget(self.main_menu)

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

    def _aplicar_estilos(self):
        style = """
            QMainWindow { background-color: #f7f7f7; }
            
            /* --- TEMA AZUL ESCURO --- */
            
            /* Cor principal da barra (Azul Marinho) */
            QMenuBar, QMenu { 
                background-color: #001f3f; 
                color: white; 
                border: 1px solid #001f3f; 
            }
            
            /* Cor da barra ao passar o mouse (um pouco mais escura) */
            QMenuBar::item:selected { 
                background: #001a33; 
            }
            
            /* Cor do item selecionado no menu (Azul Royal para destaque) */
            QMenu::item:selected { 
                background-color: #4169E1; 
            }
        """
        self.setStyleSheet(style)

    def _center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def show_main_menu(self):
        self.stacked_widget.setCurrentWidget(self.main_menu)
        self.resize(self.main_menu.sizeHint())
        self._center()

    def show_visualizar_questoes(self):
        self.visualizar_screen.refresh_geral() 
        self.stacked_widget.setCurrentWidget(self.visualizar_screen)
        self.resize(self.visualizar_screen.sizeHint())
        self._center()

    def show_cadastro_para_criacao(self):
        self.previous_screen = self.stacked_widget.currentWidget()
        self.cadastro_screen.abrir_para_criacao()
        self.stacked_widget.setCurrentWidget(self.cadastro_screen)
        self.resize(self.cadastro_screen.sizeHint())
        self._center()

    def show_cadastro_para_edicao(self, questao_id):
        self.previous_screen = self.stacked_widget.currentWidget()
        self.cadastro_screen.abrir_para_edicao(questao_id)
        self.stacked_widget.setCurrentWidget(self.cadastro_screen)
        self.resize(self.cadastro_screen.sizeHint())
        self._center()

    def show_gerador_por_id(self):
        self.gerador_id_screen._limpar_campos()
        self.stacked_widget.setCurrentWidget(self.gerador_id_screen)
        self.resize(self.gerador_id_screen.sizeHint())
        self._center()

    def show_gerador_por_criterios(self):
        """Prepara e exibe a tela de geração por critérios."""
        self.gerador_criterios_screen._limpar_campos()
        self.stacked_widget.setCurrentWidget(self.gerador_criterios_screen)
        self.resize(self.gerador_criterios_screen.sizeHint())
        self._center()
    
    def navigate_back(self):
        # A lógica aqui está correta e chamará os métodos acima, que agora têm a correção.
        if self.previous_screen:
            # Reutiliza a lógica dos métodos show_... para garantir o resize correto
            if self.previous_screen == self.main_menu:
                self.show_main_menu()
            elif self.previous_screen == self.visualizar_screen:
                self.show_visualizar_questoes()
            # Adicione outros casos 'elif' se necessário no futuro
            else:
                self.show_main_menu() # Fallback
        else:
            self.show_main_menu()

    # --- O resto dos seus métodos originais (sem alterações) ---
    def _criar_menu_superior(self):
        menu_bar = self.menuBar()
        menu_dados = menu_bar.addMenu("&Dados") 
        action_exportar = QAction("Exportar Base de Dados", self)
        action_exportar.triggered.connect(self._exportar_db) 
        menu_dados.addAction(action_exportar)
        action_importar = QAction("Importar Base de Dados", self)
        action_importar.triggered.connect(self._importar_db)
        menu_dados.addAction(action_importar)
        menu_config = menu_bar.addMenu("&Configurações")
        action_identificacao = QAction("Identificação...", self)
        action_identificacao.triggered.connect(self.abrir_configuracoes)
        menu_config.addAction(action_identificacao)
        menu_ajuda = menu_bar.addMenu("&Ajuda")
        action_sobre = QAction("Sobre...", self)
        action_sobre.triggered.connect(self._mostrar_janela_sobre)
        menu_ajuda.addAction(action_sobre)

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
        texto_licenca = """<h3>Gerador de Provas Automático v1.0</h3><p>Copyright (c) 2025 Raphael Viana Cruz.</p><hr><p>Este software é licenciado sob a <b>Creative Commons Atribuição-NãoComercial-SemDerivações 4.0 Internacional (CC BY-NC-ND 4.0)</b>.</p><p><b>Você tem a liberdade de:</b></p><ul><li><b>Compartilhar</b> — copiar e redistribuir o material em qualquer suporte ou formato para fins não comerciais.</li></ul><p><b>Sob os seguintes termos:</b></p><ul><li><b>Atribuição</b> — Você deve dar o crédito apropriado ao autor original.</li><li><b>NãoComercial</b> — Você não pode usar o material para fins comerciais.</li><li><b>SemDerivações</b> — Se você modificar ou transformar o material, você não pode distribuir o material modificado.</li><li><b>Sem restrições adicionais</b> — Você não pode aplicar termos legais ou medidas de caráter tecnológico que restrinjam legalmente outros de fazerem algo que a licença permita.</li></ul><p>Qualquer uso para fins comerciais ou distribuição de versões modificadas requer autorização prévia e por escrito do autor.</p><p>Este é um resumo legível por humanos. Para ler a licença completa, acesse:</p><p><a href="http://creativecommons.org/licenses/by-nc-nd/4.0/">creativecommons.org/licenses/by-nc-nd/4.0</a></p><br><p><b>Contato:</b> raphael.cruz@gsuite.iff.edu.br</p>"""
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
        """Chamado quando a tela do QStackedWidget muda."""
        current_widget = self.stacked_widget.widget(index)
        if current_widget:
            # Pega o título da tela atual e define como o título da janela
            self.setWindowTitle(f"Gerador de Provas - {current_widget.windowTitle()}")
            self.setFixedSize(current_widget.sizeHint())
            self._center()