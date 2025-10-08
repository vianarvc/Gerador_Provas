# interface/gerador_por_id.py

import os, re
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFileDialog, QScrollArea, QMessageBox, QCheckBox,
    QGroupBox, QGridLayout, QDesktopWidget, QTextEdit, QListWidget
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from database import buscar_questoes_por_ids, carregar_configuracoes
from motor_gerador import gerar_versoes_prova
from gerador_pdf import criar_pdf_provas
from .custom_widgets import NoScrollSpinBox, NoScrollDoubleSpinBox
from .log_dialog import LogDialog

class GeradorPorIdWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerador de Provas por IDs")
        self.resize(800, 700)
        
        # --- MUDANÇA 1: Nome da variável para mais clareza ---
        self.questoes_ativas_verificadas = [] # Armazena apenas as questões ATIVAS

        main_layout = QVBoxLayout(self)
        self._aplicar_estilos()
        
        # --- Configurações da Avaliação ---
        config_group = QGroupBox("Configurações da Avaliação")
        config_layout = QVBoxLayout(config_group)
        config_layout.addWidget(QLabel("Nome da Avaliação:"))
        self.nome_input = QLineEdit()
        self.nome_input.setPlaceholderText("Ex: Eletricidade Básica - Lista Pré-definida")
        config_layout.addWidget(self.nome_input)
        
        campos_capa_layout = QHBoxLayout()
        campos_capa_layout.addWidget(QLabel("Bimestre:"))
        self.bimestre_input = QLineEdit("1")
        campos_capa_layout.addWidget(self.bimestre_input)
        campos_capa_layout.addSpacing(20)
        campos_capa_layout.addStretch()
        config_layout.addLayout(campos_capa_layout)
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Número de Versões:"))
        self.versoes_spinbox = NoScrollSpinBox()
        self.versoes_spinbox.setMinimum(1)
        self.versoes_spinbox.setFixedWidth(150)
        h_layout.addWidget(self.versoes_spinbox)
        h_layout.addStretch()
        config_layout.addLayout(h_layout)
        main_layout.addWidget(config_group)

        # --- Seleção de Questões por ID ---
        id_group = QGroupBox("Seleção de Questões")
        id_layout = QVBoxLayout(id_group)
        id_layout.addWidget(QLabel("Insira os IDs das questões, separados por vírgula, espaço ou quebra de linha:"))
        self.ids_input = QTextEdit()
        self.ids_input.setPlaceholderText("Ex: 1, 5, 23, 42, 18")
        self.ids_input.setFixedHeight(100)
        id_layout.addWidget(self.ids_input)
        self.btn_verificar = QPushButton("Verificar IDs e Carregar Questões")
        self.btn_verificar.clicked.connect(self._verificar_ids)
        id_layout.addWidget(self.btn_verificar, 0, Qt.AlignLeft)
        id_layout.addWidget(QLabel("Status das Questões Carregadas:"))
        self.lista_questoes_carregadas = QListWidget()
        self.lista_questoes_carregadas.setFixedHeight(150)
        id_layout.addWidget(self.lista_questoes_carregadas)
        main_layout.addWidget(id_group)

        # --- Opções de Geração ---
        gabarito_group = QGroupBox("Opções de Geração e Gabarito")
        gabarito_group.setObjectName("GabaritoGroup")
        gabarito_main_layout = QVBoxLayout(gabarito_group)
        checkboxes_layout = QHBoxLayout()
        
        self.check_distribuir = QCheckBox("Distribuir Gabarito (A, B, C...)")
        self.check_distribuir.setChecked(True)
        self.check_embaralhar = QCheckBox("Embaralhar Ordem das Questões")
        self.check_embaralhar.setChecked(False)
        checkboxes_layout.addWidget(self.check_distribuir)
        checkboxes_layout.addWidget(self.check_embaralhar)
        checkboxes_layout.addStretch()
        gabarito_main_layout.addLayout(checkboxes_layout)
        
        rotacao_layout = QHBoxLayout()
        label_rotacao = QLabel("Rotação do Gabarito entre versões (n+):")
        self.rotacao_spinbox = NoScrollSpinBox()
        self.rotacao_spinbox.setMinimum(0)
        self.rotacao_spinbox.setValue(1)
        rotacao_layout.addWidget(label_rotacao)
        rotacao_layout.addWidget(self.rotacao_spinbox)
        rotacao_layout.addStretch()
        gabarito_main_layout.addLayout(rotacao_layout)
        main_layout.addWidget(gabarito_group)

        # --- Bloco 4: Botão Gerar (sem alteração) ---
        self.btn_gerar = QPushButton("🚀 Gerar Prova")
        self.btn_gerar.setObjectName("BotaoPrincipal")
        self.btn_gerar.setMinimumHeight(60)
        self.btn_gerar.clicked.connect(self._gerar_prova)
        main_layout.addWidget(self.btn_gerar, 0, Qt.AlignCenter)
        
        #self._center()

    # Lógica de verificação para checar status 'ativa' ---
    def _verificar_ids(self):
        self.questoes_ativas_verificadas.clear() # Limpa a lista de questões válidas
        self.lista_questoes_carregadas.clear()

        texto_ids = self.ids_input.toPlainText()
        if not texto_ids.strip():
            QMessageBox.warning(self, "Aviso", "Nenhum ID foi inserido.")
            return

        ids_str = re.findall(r'\d+', texto_ids)
        lista_ids = [int(id_str) for id_str in ids_str]

        if not lista_ids:
            QMessageBox.warning(self, "Aviso", "Nenhum número de ID válido foi encontrado no texto.")
            return

        todas_questoes_encontradas = buscar_questoes_por_ids(lista_ids)
        mapa_questoes = {q['id']: q for q in todas_questoes_encontradas}

        if not todas_questoes_encontradas:
            self.lista_questoes_carregadas.addItem(f"❌ ID {q_id}: NÃO ENCONTRADO OU INATIVO")
            return

        for q_id in lista_ids:
            resumo = "..."
            questao = mapa_questoes.get(q_id)

            if questao and questao.get("ativa", 1):
                resumo_txt = questao['enunciado'].replace('\n', ' ')
                if len(resumo_txt) > 80: resumo_txt = resumo_txt[:80] + "..."
                
                self.lista_questoes_carregadas.addItem(f"✅ ID {q_id}: {resumo_txt}")
                self.questoes_ativas_verificadas.append(questao) # Adiciona à lista de geração
            else:
                # Se a questão não foi encontrada OU foi encontrada mas está inativa,
                # o tratamento é o mesmo: NÃO ENCONTRADO.
                self.lista_questoes_carregadas.addItem(f"❌ ID {q_id}: NÃO ENCONTRADO OU INATIVO")


    # --- MUDANÇA 3: `_gerar_prova` agora usa a lista de questões ativas ---
    def _gerar_prova(self):
        if not self.questoes_ativas_verificadas:
            QMessageBox.warning(self, "Erro", "Nenhuma questão ATIVA foi verificada e carregada. Verifique os IDs.")
            return

        log_dialog = LogDialog(self)
        log_dialog.show()
        self.btn_gerar.setEnabled(False)
        
        try:
            config = carregar_configuracoes()
            num_versoes = self.versoes_spinbox.value()
            log_dialog.append_log(f"Iniciando geração de {num_versoes} versão(ões) com {len(self.questoes_ativas_verificadas)} questões pré-definidas.")
            
            opcoes_geracao = { "gabarito": {"embaralhar_questoes": self.check_embaralhar.isChecked()}, "pontuacao": {} }
            
            versoes_geradas = gerar_versoes_prova(self.questoes_ativas_verificadas, num_versoes, opcoes_geracao)
            if not versoes_geradas:
                raise Exception("Não foi possível gerar as versões da prova (motor retornou vazio).")

            log_dialog.append_log("Variações geradas. Solicitando pasta de destino...")
            pasta_destino = QFileDialog.getExistingDirectory(self, "Selecione a pasta para salvar as provas")
            
            if not pasta_destino:
                raise Exception("Nenhuma pasta de destino selecionada. Operação cancelada.")

            dados_pdf = {
                "nomeDisciplina": self.nome_input.text(), 
                "tipoExame": "AVALIAÇÃO", 
                "bimestre": self.bimestre_input.text(), # Pega o bimestre da tela
                "nomeProfessor": config.get("nome_professor", ""), # Pega o professor das configs
                # ... o resto dos seus campos continua igual
                "siglaCurso": config.get("sigla_curso", "CURSO"),
                "nomeCursoCompleto": config.get("nome_curso", ""),
                "nomeEscola": config.get("nome_escola", ""),
                "emailContato": config.get("email_contato", ""),
                "numeroQuestoes": len(self.questoes_ativas_verificadas),
                "valorTotalProva": " "
            }
            
            criar_pdf_provas(self.nome_input.text(), versoes_geradas, pasta_destino, dados_pdf, log_dialog)
            
            log_dialog.finish(success=True)
            QMessageBox.information(self, "Sucesso", f"Provas e gabarito gerados com sucesso em:\n{pasta_destino}")

        except Exception as e:
            QMessageBox.critical(self, "Erro na Geração", f"Ocorreu um erro: {e}")
        
        finally:
            self.btn_gerar.setEnabled(True)
    
    # --- Demais funções (estilo, centralizar) ---
    def _aplicar_estilos(self):
        # (Seu código de QSS que adicionamos na última vez)
        style = """
        QGroupBox{
            font-weight:bold;
            color:#34495e;
            margin-top:10px;
            padding-top:20px;
            border:1px solid #bdc3c7;
            border-radius:5px;
        }
        QGroupBox::title{
            subcontrol-origin:margin;
            subcontrol-position:top left;
            padding:0 10px;
            background-color:#ecf0f1;
            border-radius:3px;
        }

        QLineEdit,QTextEdit,QComboBox,QSpinBox,QDoubleSpinBox,QListWidget{
            border:1px solid #bdc3c7;
            border-radius:5px;
            padding:5px;
            background-color:white;
        }

        QPushButton{
            border:none;
            border-radius:5px;
            padding:8px 15px;
            font-size:18px;
            font-weight:bold;
            min-height:30px;
            background-color:#3498db;
            color:white;
        }

        QPushButton:hover{
            background-color:#2980b9;
        }

        #BotaoPrincipal{
            background-color:#2ecc71;
            font-size:30px;
        }
        
        #BotaoPrincipal:hover{
            background-color:#27ae60;}
        """
        self.setStyleSheet(style)

    def _center(self): 
        """ Centraliza a janela na tela. """
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        # Coloque este novo método na sua classe
    def showEvent(self, event):
        """Este método é chamado automaticamente pelo Qt antes de a janela ser exibida."""
        self._center()
        super().showEvent(event)