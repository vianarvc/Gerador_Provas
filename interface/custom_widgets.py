# interface/custom_widgets.py

from PyQt5.QtWidgets import (
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, 
    QPushButton, QLabel, QGroupBox, QSlider, QCheckBox, 
    QTextEdit, QTableWidget, QToolButton, QCompleter,
    QMessageBox
)
from PyQt5.QtCore import Qt, QTimer

class NoScrollComboBox(QComboBox):
    """
    Uma subclasse de QComboBox que ignora o evento de rolagem do mouse.
    """
    def wheelEvent(self, event):
        event.ignore()

class NoScrollSpinBox(QSpinBox):
    """
    Uma subclasse de QSpinBox que ignora o evento de rolagem do mouse.
    """
    def wheelEvent(self, event):
        event.ignore()

class NoScrollDoubleSpinBox(QDoubleSpinBox):
    """
    Uma subclasse de QDoubleSpinBox que ignora o evento de rolagem do mouse.
    """
    def wheelEvent(self, event):
        event.ignore()

class NoScrollSlider(QSlider):
    """
    Uma subclasse de QSlider que ignora o evento de rolagem do mouse.
    """
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, event):
        event.ignore()

class EstilosApp:
    """
    Classe central de estilos para todo o aplicativo.
    Fornece estilo base para botões e método para sobrescrever tamanho.
    """

    # --- Estilo base de todos os botões ---
    @staticmethod
    def estilo_botao_base():
        return """
            QPushButton {
                background-color: #3498db; /* azul padrão */
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1a5276;
            }
        """

    # --- Botão verde padrão (ex.: Salvar / Confirmar) ---
    @staticmethod
    def estilo_botao_verde():
        return """
            QPushButton {
                background-color: #2ecc71; /* verde */
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """

    # --- Botão cinza (ex.: Voltar / Cancelar) ---
    @staticmethod
    def estilo_botao_cinza():
        return """
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
            QPushButton:pressed {
                background-color: #707b7c;
            }
        """

    # --- Botão vermelho (ex.: Excluir) ---
    @staticmethod
    def estilo_botao_vermelho():
        return """
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #922b21;
            }
        """

    # --- Aplicar tamanho e padding customizado sem alterar cor/borda ---
    @staticmethod
    def aplicar_tamanho(botao, font_size=22, padding="10px 15px", min_height=35, min_width=None):
        """
        Aplica tamanho e padding a um QPushButton.
        Mantém o estilo base definido para cores e bordas.
        """
        tamanho_qss = f"""
            QPushButton {{
                font-size: {font_size}px;
                padding: {padding};
                min-height: {min_height}px;
        """
        if min_width:
            tamanho_qss += f"min-width: {min_width}px;"
        tamanho_qss += "}"
        # Junta com o estilo atual do botão (presumindo que já tenha aplicado base)
        botao.setStyleSheet(botao.styleSheet() + tamanho_qss)

    # --- Método helper para aplicar estilo e tamanho juntos ---
    @staticmethod
    def aplicar(botao, estilo="azul", font_size=22, padding="10px 15px", min_height=35, min_width=None):
        """
        Aplica um estilo base + tamanho customizado ao botão.
        estilos possíveis: 'azul', 'verde', 'cinza', 'vermelho'
        """
        if estilo == "azul":
            botao.setStyleSheet(EstilosApp.estilo_botao_base())
        elif estilo == "verde":
            botao.setStyleSheet(EstilosApp.estilo_botao_verde())
        elif estilo == "cinza":
            botao.setStyleSheet(EstilosApp.estilo_botao_cinza())
        elif estilo == "vermelho":
            botao.setStyleSheet(EstilosApp.estilo_botao_vermelho())
        else:
            botao.setStyleSheet(EstilosApp.estilo_botao_base())

        # Aplica o tamanho
        EstilosApp.aplicar_tamanho(botao, font_size, padding, min_height, min_width)

    @staticmethod
    def aplicar_estilo_janela_principal(janela):
        """Aplica o estilo global da QMainWindow, incluindo a barra superior."""
        style = """
            QMainWindow { background-color: #f7f7ff; }
            
            /* A barra superior unificada */
            #TopBar { 
                background-color: #001f3f; 
                color: white; 
                border: none;
                padding: 2px;
                spacing: 5px;
            }

            /* Botão de VOLTAR (seta) com fonte maior */
            #VoltarToolButton {
                color: white;
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 22px;
                font-weight: bold;
            }
            #VoltarToolButton:hover, #VoltarToolButton:pressed {
                background-color: #001a33;
            }

            /* Botões de MENU (Dados, etc.) com fonte normal */
            #MenuToolButton {
                color: white;
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 14px;
                font-weight: bold;
            }
            #MenuToolButton::menu-indicator { image: none; }
            #MenuToolButton:hover, #MenuToolButton:pressed {
                background-color: #001a33;
            }

            /* O menu suspenso que aparece */
            QMenu { 
                background-color: #001f3f; 
                color: white; 
                border: 1px solid #001a33; 
            }
            QMenu::item:selected { 
                background-color: #4169E1; 
            }
        """
        janela.setStyleSheet(style)

class MeuLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            border: 1px solid #bdc3c7;
            border-radius: 5px;
            padding: 5px;
            background-color: white;
            selection-background-color: #3498db;
        """)

class MeuSpinBox(NoScrollSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            border: 1px solid #bdc3c7;
            border-radius: 5px;
            padding: 5px;
            background-color: white;
            selection-background-color: #3498db;
        """)

class MeuDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            border: 1px solid #bdc3c7;
            border-radius: 5px;
            padding: 5px;
            background-color: white;
            selection-background-color: #3498db;
        """)

class MeuComboBox(NoScrollComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            border: 1px solid #bdc3c7;
            border-radius: 5px;
            padding: 5px;
            background-color: white;
        """)

'''class MeuComboEditavel(NoScrollComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            border: 1px solid #bdc3c7;
            border-radius: 5px;
            padding: 5px;
            background-color: white;
        """)
        
        # ✅ Inicia como NÃO editável - comportamento normal
        self.setEditable(False)
        
    def mouseDoubleClickEvent(self, event):
        """Clique duplo: torna editável e habilita edição"""
        if event.button() == Qt.LeftButton:
            self.setEditable(True)
            self.lineEdit().selectAll()
            self.lineEdit().setFocus()
            
            # ✅ Alternativa: observar perda de foco em vez de editingFinished
            self.lineEdit().focusOutEvent = self._handle_focus_out
            
        super().mouseDoubleClickEvent(event)

    def _handle_focus_out(self, event):
        """Quando perde foco, volta a ser não-editável"""
        self.setEditable(False)
        # Restaura o focusOutEvent original
        self.lineEdit().focusOutEvent = super().lineEdit().focusOutEvent
        super().lineEdit().focusOutEvent(event)'''

class MeuCheckBox(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("spacing: 5px;")

class MeuLabel(QLabel):
    def __init__(self, parent=None, cor="#2c3e50", tamanho=12):
        super().__init__(parent)
        self.setStyleSheet(f"color: {cor}; font-size: {tamanho}px;")

class MeuGroupBox(QGroupBox):
    """GroupBox padronizado para todas as telas."""
    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.setStyleSheet("""
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
        """)

class MeuBotao(QPushButton):
    """Botão padronizado para a aplicação, com cores e tamanhos customizáveis."""
    def __init__(self, text="", tipo="principal", parent=None):
        super().__init__(text, parent)
        self.tipo = tipo
        self._aplicar_estilo()

    def _aplicar_estilo(self):
        if self.tipo == "principal":
            # Verde, para ação principal (ex: Gerar Prova)
            style = """
                QPushButton {
                    background-color: #2ecc71;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 30px;
                    font-weight: bold;
                    min-width: 300px;
                    min-height: 60px;
                }
                QPushButton:hover {
                    background-color: #27ae60;
                }
            """
        elif self.tipo == "navegacao":
            # Cinza sutil para navegação na barra superior
            style = """
                QPushButton {
                    background-color: #7f8c8d;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-weight: bold;
                    
                    /* Tamanho menor e mais apropriado */
                    font-size: 14px;
                    padding: 5px 15px;
                    min-height: 30px;
                }
                QPushButton:hover {
                    background-color: #95a5a6;
                }
            """
        elif self.tipo == "voltar":
            # Cinza, botão voltar
            style = """
                QPushButton {
                    background-color: #7f8c8d;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 30px;
                    font-weight: bold;
                    min-width: 300px;
                    min-height: 60px;
                }
                QPushButton:hover {
                    background-color: #95a5a6;
                }
            """
        elif self.tipo == "editar" or self.tipo == "testar":
            # Azul, para editar (tamanho grande)
            style = """
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 30px;
                    font-weight: bold;
                    min-width: 300px;
                    min-height: 60px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """
            
        # --- ADICIONE ESTE NOVO BLOCO PARA O BOTÃO EXCLUIR ---
        elif self.tipo == "excluir":
            # Vermelho, para excluir (tamanho grande)
            style = """
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 30px;
                    font-weight: bold;
                    min-width: 300px;
                    min-height: 60px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """
        elif self.tipo == "acao":
            # Azul, para adicionar tema
            style = """
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 5px 12px;
                    font-size: 22px;
                    min-height: 25px;
                    min-width: 200px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """
        elif self.tipo == "remover":
            # Vermelho, para remover tema
            style = """
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 5px 10px;
                    font-size: 18px;
                    min-height: 25px;
                    min-width: 40px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """
        else:
            style = ""  # default
        self.setStyleSheet(style)

class MeuTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            border: 1px solid #bdc3c7;
            border-radius: 5px;
            padding: 5px;
            background-color: white;
            selection-background-color: #3498db;
        """)

class MeuTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QTableWidget {
                gridline-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                selection-background-color: #95a5a6;
            }
        """)

class MeuToolButton(QToolButton):
    # Substitua o __init__ inteiro por este:
    def __init__(self, text="", parent=None):
        # 1. Chama o construtor do pai da forma correta (sem o texto)
        super().__init__(parent)
        
        # 2. Define o texto usando o método apropriado
        self.setText(text)
        
        # 3. Aplica o estilo
        self.setStyleSheet("""
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
        """)

class MeuImagemPreviewLabel(QLabel):
    def __init__(self, text="Nenhuma imagem selecionada.", parent=None):
        super().__init__(text, parent)
        
        # Define as propriedades padrão do widget
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(200)
        
        # Aplica o estilo que estava faltando
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #95a5a6;
                border-radius: 5px;
                color: #7f8c8d;
                background-color: #f0f0f0; /* Um fundo sutil para destacar a área */
                font-size: 14px;
            }
        """)