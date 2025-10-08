# interface/MenuInicial.py

import sys, os, shutil
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QDesktopWidget, 
    QApplication, QLabel, QAction, QMenuBar, QDialog, QFileDialog, QMessageBox
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QSize

# Importa as outras janelas
from .cadastro_questao import CadastroQuestaoWindow
from .gerador_provas import GeradorProvasWindow
from .visualizar_questoes import VisualizarQuestoesWindow
from database import exportar_base_de_dados, importar_base_de_dados
from .selecao_modo_geracao import SelecaoModoGeracaoDialog
from .gerador_por_id import GeradorPorIdWindow
from .configuracoes_dialog import ConfiguracoesDialog

# MUDANÇA: A classe herda de QMainWindow para suportar a barra de menu
class MenuInicialWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Menu Principal")
        self.resize(400, 350) 
        
        self._aplicar_estilos() 

        # 1. Configura o Menu Superior (Ações)
        self._criar_menu_superior() 
        
        # 2. Configura a Área Central (Botões)
        central_widget = QWidget() 
        self.setCentralWidget(central_widget)
        
        # 3. Layout da Área Central
        layout_principal = QVBoxLayout(central_widget)
        layout_principal.setAlignment(Qt.AlignCenter) 
        layout_principal.setContentsMargins(50, 50, 50, 50)
        layout_principal.setSpacing(15)

        # Guarda referências para as janelas
        self.cadastro_window = None
        self.gerador_window = None
        self.visualizador_window = None
        self.dialogo_gerador = None

        # Título do Menu
        titulo = QLabel("Gerador de Provas")
        titulo.setObjectName("TituloMenu") 
        layout_principal.addWidget(titulo)
        
        # Botões do menu
        btn_visualizar = QPushButton("Banco de Questões")
        btn_cadastrar = QPushButton("Cadastrar Questão")
        btn_gerar = QPushButton("Gerar Prova")

        # Estilizando e adicionando os botões
        for btn in [btn_visualizar, btn_cadastrar, btn_gerar]:
            btn.setMinimumHeight(50) 
            btn.setFont(QFont("Arial", 12, QFont.Bold))
            layout_principal.addWidget(btn)

        # Conectando os botões às suas funções
        btn_visualizar.clicked.connect(self.abrir_visualizador)
        btn_cadastrar.clicked.connect(self.abrir_cadastro)
        btn_gerar.clicked.connect(self.abrir_gerador)

        self._center()

    def _criar_menu_superior(self):
        menu_bar = self.menuBar()
        
        # --- MENU DADOS (Exportar/Importar) ---
        menu_dados = menu_bar.addMenu("&Dados") 

        # Ação de Exportar (criação e conexão)
        action_exportar = QAction("Exportar Base de Dados (.db)", self)
        action_exportar.triggered.connect(self._exportar_db) 
        menu_dados.addAction(action_exportar)

        # Ação de Importar (criação e conexão)
        action_importar = QAction("Importar Base de Dados (.db)", self)
        action_importar.triggered.connect(self._importar_db)
        menu_dados.addAction(action_importar)
        
        # --- MENU CONFIGURAÇÕES ---
        menu_config = menu_bar.addMenu("&Configurações")
        action_identificacao = QAction("Identificação...", self)
        action_identificacao.triggered.connect(self.abrir_configuracoes)
        menu_config.addAction(action_identificacao)

    def _aplicar_estilos(self):
        """Define e aplica o Qt Style Sheet (QSS) para dar estilo ao menu."""
        style = """
        /* Estilo da Janela Principal (QMainWindow) */
        QMainWindow {
            background-color: #f7f7f7; 
        }

        /* Estilo da Barra de Menu */
        QMenuBar {
            background-color: #34495e; /* Azul Escuro */
            color: white;
            border: 1px solid #34495e;
        }
        
        QMenuBar::item:selected {
            background: #2c3e50;
        }

        QMenu {
            background-color: #34495e;
            color: white;
            border: 1px solid #2c3e50;
        }

        QMenu::item:selected {
            background-color: #3498db; /* Azul Claro */
        }
        
        QWidget#centralWidget { 
             background-color: #f7f7f7;
        }
        #TituloMenu {
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50; 
            margin-bottom: 20px;
            padding-bottom: 5px;
            border-bottom: 2px solid #3498db; 
        }

        QPushButton {
            background-color: #3498db; 
            color: white;
            border: none;
            border-radius: 8px; 
            padding: 10px;
            font-size: 22px; 
            min-width: 250px;
        }

        QPushButton:hover {
            background-color: #2980b9;
        }
        
        QPushButton:pressed {
            background-color: #1a5276;
        }
        """
        self.setStyleSheet(style)
    
    def abrir_visualizador(self):
        self.visualizador_window = VisualizarQuestoesWindow()
        self.visualizador_window.show()

    def abrir_cadastro(self):
        self.cadastro_window = CadastroQuestaoWindow()
        if self.visualizador_window and self.visualizador_window.isVisible():
             self.cadastro_window.questao_atualizada.connect(self.visualizador_window.carregar_questoes)
        self.cadastro_window.show()

    def abrir_gerador(self):
        dialogo = SelecaoModoGeracaoDialog(self)
        resultado = dialogo.exec_() # Abre o diálogo e espera ele fechar

        # Se o usuário fechou o diálogo (clicou no X), não faz nada
        if resultado != QDialog.Accepted:
            return

        # Se o usuário escolheu uma opção, abre a janela correspondente
        if dialogo.choice == 'criterios':
            self.gerador_window = GeradorProvasWindow()
            self.gerador_window.show()
        elif dialogo.choice == 'ids':
            self.gerador_window = GeradorPorIdWindow()
            self.gerador_window.show()

    def _center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def abrir_configuracoes(self):
        dialog = ConfiguracoesDialog(self)
        dialog.exec_()

    def _exportar_db(self):
        """Abre um diálogo para salvar uma cópia do banco de dados."""
        db_path = "banco_questoes.db"
        if not os.path.exists(db_path):
            QMessageBox.critical(self, "Erro", "Arquivo do banco de dados não encontrado!")
            return

        # Abre o diálogo "Salvar como..."
        destination, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Base de Dados para...",
            os.path.expanduser("~/backup_banco_questoes.db"), # Sugestão de nome
            "Arquivos de Banco de Dados (*.db)"
    )

        if destination:
            try:
                shutil.copy(db_path, destination)
                QMessageBox.information(self, "Sucesso", f"Base de dados exportada com sucesso para:\n{destination}")
            except Exception as e:
                QMessageBox.critical(self, "Erro na Exportação", f"Não foi possível copiar o arquivo: {e}")

    def _importar_db(self):
        """Substitui o banco de dados atual por um arquivo selecionado pelo usuário."""
        db_path = "banco_questoes.db"

        # Alerta CRÍTICO para o usuário
        reply = QMessageBox.warning(
            self,
            "Atenção! Ação Irreversível!",
            "Esta ação irá **SUBSTITUIR** sua base de dados atual. Todo o seu trabalho não salvo será perdido.\n\n"
            "É altamente recomendável que você faça um backup (usando a função 'Exportar') antes de continuar.\n\n"
            "Deseja continuar com a importação?",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel
        )

        if reply != QMessageBox.Yes:
            return

        # Abre o diálogo "Abrir..."
        source, _ = QFileDialog.getOpenFileName(
            self,
            "Importar Base de Dados de...",
            os.path.expanduser("~"),
            "Arquivos de Banco de Dados (*.db)"
        )

        if source:
            try:
                shutil.copy(source, db_path)
                QMessageBox.information(
                    self, 
                    "Sucesso", 
                    "Base de dados importada com sucesso!\n\n"
                    "É recomendável **reiniciar o programa** para que todas as janelas carreguem os novos dados."
                )
            except Exception as e:
                QMessageBox.critical(self, "Erro na Importação", f"Não foi possível copiar o arquivo: {e}")