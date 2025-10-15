# interface/gerador_por_id.py

import os, re
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFileDialog, QScrollArea, QMessageBox, QCheckBox,
    QGroupBox, QGridLayout, QDesktopWidget, QTextEdit, QListWidget, QApplication
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QThread

from database import (
    obter_temas, obter_disciplinas, obter_disciplina_id_por_nome, 
    carregar_configuracoes, buscar_questoes_por_ids
)
from motor_gerador import gerar_versoes_prova
from gerador_pdf import criar_pdf_provas
from .custom_widgets import (
    MeuLineEdit, MeuSpinBox, MeuDoubleSpinBox, MeuComboBox, MeuLabel, MeuGroupBox, EstilosApp,
    NoScrollComboBox, NoScrollSpinBox, NoScrollDoubleSpinBox, MeuCheckBox, MeuBotao
)
from .log_dialog import LogDialog
from .worker_gerador import GeradorWorker

class GeradorPorIdScreen(QWidget):
    voltar_pressed = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Gerar Prova por IDs")
        
        self.questoes_ativas_verificadas = []

        # O layout principal da tela agora conterá apenas a área de rolagem
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10) # Margem para a janela toda

        # 1. Criar a QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("ScrollPrincipal")

        # 2. Criar um widget que servirá como "página" dentro da rolagem
        scroll_content_widget = QWidget()
        
        # 3. Criar o layout para esta "página"
        content_layout = QVBoxLayout(scroll_content_widget)

        # --- Configurações da Avaliação ---
        config_group = MeuGroupBox("Configurações da Avaliação")
        config_layout = QVBoxLayout(config_group)
        config_layout.addWidget(QLabel("Nome da Avaliação:"))
        self.nome_input = MeuLineEdit()
        self.nome_input.setPlaceholderText("Ex: Eletricidade Básica - Lista Pré-definida")
        config_layout.addWidget(self.nome_input)

        disciplina_layout = QHBoxLayout()
        disciplina_layout.addWidget(QLabel("<b>Selecione a Disciplina para a Prova:</b>"))
        self.disciplina_combo = NoScrollComboBox() # Mantido por causa da funcionalidade wheelEvent
        disciplina_layout.addWidget(self.disciplina_combo, 1)
        config_layout.addLayout(disciplina_layout)
        
        campos_capa_layout = QHBoxLayout()
        campos_capa_layout.addWidget(QLabel("Bimestre:"))
        self.bimestre_input = MeuLineEdit("1")
        campos_capa_layout.addWidget(self.bimestre_input)
        campos_capa_layout.addSpacing(20)
        campos_capa_layout.addStretch()
        config_layout.addLayout(campos_capa_layout)
        
        h_layout_1 = QHBoxLayout()
        h_layout_1.addWidget(QLabel("Número de Versões:"))
        self.versoes_spinbox = NoScrollSpinBox() # Mantido
        self.versoes_spinbox.setMinimum(1)
        self.versoes_spinbox.setFixedWidth(150)
        self.check_embaralhar = MeuCheckBox("Embaralhar Ordem das Questões")
        self.check_embaralhar.setChecked(False)
        h_layout_1.addWidget(self.versoes_spinbox)
        h_layout_1.addWidget(self.check_embaralhar)
        h_layout_1.addStretch()
        
        h_layout_2 = QHBoxLayout()
        h_layout_2.addWidget(QLabel("Valor Total da Prova:"))
        self.valor_total_spinbox = NoScrollDoubleSpinBox() # Mantido
        self.valor_total_spinbox.setDecimals(2)
        self.valor_total_spinbox.setMinimum(0.0)
        self.valor_total_spinbox.setMaximum(1000.0)
        self.valor_total_spinbox.setValue(10.0)
        h_layout_2.addWidget(self.valor_total_spinbox)
        h_layout_2.addSpacing(20)
        self.check_distribuir_valor = MeuCheckBox("Distribuir valor igualmente") 
        self.check_distribuir_valor.setChecked(True)
        h_layout_2.addWidget(self.check_distribuir_valor)
        h_layout_2.addStretch()
        
        config_layout.addLayout(h_layout_1)
        config_layout.addLayout(h_layout_2)
        
        content_layout.addWidget(config_group)

        # --- Seleção de Questões por ID ---
        id_group = MeuGroupBox("Seleção de Questões")
        id_layout = QVBoxLayout(id_group)
        id_layout.addWidget(QLabel("Insira os IDs das questões, separados por vírgula, espaço ou quebra de linha:"))
        self.ids_input = QTextEdit() # Mantido como QTextEdit
        self.ids_input.setPlaceholderText("Ex: 1, 5, 23, 42, 18")
        self.ids_input.setMinimumHeight(100)
        id_layout.addWidget(self.ids_input)
        self.btn_verificar = MeuBotao("Verificar IDs e Carregar Questões", tipo="acao")
        self.btn_verificar.clicked.connect(self._verificar_ids)
        id_layout.addWidget(self.btn_verificar, 0, Qt.AlignLeft)
        id_layout.addWidget(QLabel("Status das Questões Carregadas:"))
        self.lista_questoes_carregadas = QListWidget() # Mantido como QListWidget
        self.lista_questoes_carregadas.setMinimumHeight(150)
        id_layout.addWidget(self.lista_questoes_carregadas)
        content_layout.addWidget(id_group)

        # --- Opções de Geração ---
        gabarito_group = MeuGroupBox("Opções de Geração e Gabarito")
        gabarito_main_layout = QVBoxLayout(gabarito_group)
        checkboxes_layout = QHBoxLayout()
        self.check_distribuir = MeuCheckBox("Distribuir Gabarito (A, B, C...)")
        self.check_distribuir.setChecked(True)
        checkboxes_layout.addWidget(self.check_distribuir)
        
        checkboxes_layout.addStretch()
        gabarito_main_layout.addLayout(checkboxes_layout)
        rotacao_layout = QHBoxLayout()
        label_rotacao = QLabel("Rotação do Gabarito entre versões (n+):")
        self.rotacao_spinbox = NoScrollSpinBox() # Mantido
        self.rotacao_spinbox.setMinimum(0)
        self.rotacao_spinbox.setValue(1)
        rotacao_layout.addWidget(label_rotacao)
        rotacao_layout.addWidget(self.rotacao_spinbox)
        rotacao_layout.addStretch()
        gabarito_main_layout.addLayout(rotacao_layout)
        content_layout.addWidget(gabarito_group)

        # --- Botões Finais ---
        botoes_finais_layout = QHBoxLayout()
        '''self.btn_voltar = MeuBotao("↩️ Voltar ao Menu", tipo="voltar")
        self.btn_voltar.clicked.connect(self.voltar_pressed.emit)'''
        self.btn_gerar = MeuBotao("🚀 Gerar Prova", tipo="principal")
        self.btn_gerar.clicked.connect(self._gerar_prova)
        #botoes_finais_layout.addWidget(self.btn_voltar)
        botoes_finais_layout.addStretch()
        botoes_finais_layout.addWidget(self.btn_gerar)
        content_layout.addLayout(botoes_finais_layout)

        # 4. Conectar a "página" à área de rolagem
        scroll_area.setWidget(scroll_content_widget)

        # 5. Adicionar a área de rolagem ao layout principal da tela
        main_layout.addWidget(scroll_area)
        
        self._carregar_disciplinas()

    # Lógica de verificação para checar status 'ativa' ---
    def _verificar_ids(self):
        self.questoes_ativas_verificadas.clear()
        self.lista_questoes_carregadas.clear()

        texto_ids = self.ids_input.toPlainText()
        if not texto_ids.strip():
            QMessageBox.warning(self, "Aviso", "Nenhum ID foi inserido.")
            return

        ids_str = re.findall(r'\d+', texto_ids)
        lista_ids_usuario = [int(id_str) for id_str in ids_str]

        if not lista_ids_usuario:
            QMessageBox.warning(self, "Aviso", "Nenhum número de ID válido foi encontrado no texto.")
            return

        # Busca no banco de dados. A função deve ser capaz de encontrar questões
        # mesmo que estejam inativas para que possamos reportar o status corretamente.
        questoes_do_banco = buscar_questoes_por_ids(lista_ids_usuario)
        mapa_questoes_encontradas = {q['id']: q for q in questoes_do_banco}

        # Itera sobre a lista de IDs que o USUÁRIO digitou para dar feedback para cada um.
        for q_id in lista_ids_usuario:
            questao_encontrada = mapa_questoes_encontradas.get(q_id)

            # Verifica o status da questão encontrada
            if questao_encontrada:
                # A chave "ativa" pode ser 1 (ativa) ou 0 (inativa).
                if questao_encontrada.get("ativa", 1):
                    # Caso 1: Questão encontrada E ATIVA
                    resumo_txt = questao_encontrada['enunciado'].replace('\n', ' ')
                    if len(resumo_txt) > 80:
                        resumo_txt = resumo_txt[:80] + "..."
                    
                    self.lista_questoes_carregadas.addItem(f"✅ ID {q_id}: {resumo_txt}")
                    self.questoes_ativas_verificadas.append(questao_encontrada)
                else:
                    # Caso 2: Questão encontrada mas INATIVA
                    self.lista_questoes_carregadas.addItem(f"❌ ID {q_id}: INATIVA")
            else:
                # Caso 3: Questão NÃO ENCONTRADA no mapa (não retornou do banco)
                self.lista_questoes_carregadas.addItem(f"❌ ID {q_id}: NÃO ENCONTRADA")
    
    def _carregar_disciplinas(self):
        self.disciplina_combo.clear()
        disciplinas = obter_disciplinas()
        # Adiciona um placeholder para forçar a seleção inicial
        if "-- Selecione --" not in disciplinas:
            disciplinas.insert(0, "-- Selecione --")
        self.disciplina_combo.addItems(disciplinas)

    def _disciplina_selecionada(self):
        """Atualiza os temas disponíveis em todas as linhas de critério."""
        disciplina_nome = self.disciplina_combo.currentText()
        if disciplina_nome == "-- Selecione --":
            temas_filtrados = []
        else:
            disciplina_id = obter_disciplina_id_por_nome(disciplina_nome)
            temas_filtrados = obter_temas(disciplina_id=disciplina_id)
        
        # Atualiza cada combobox de tema já existente
        for linha in self.linhas_tema:
            combo_tema = linha["combo"]
            texto_atual = combo_tema.currentText()
            combo_tema.clear()
            combo_tema.addItems(temas_filtrados)
            
            # Tenta manter o tema que já estava selecionado
            index = combo_tema.findText(texto_atual)
            if index != -1:
                combo_tema.setCurrentIndex(index)

        self._atualizar_contadores()


    def _gerar_prova(self):
        # --- ETAPA 1: Coleta de Dados e Validação (Sem alterações) ---
        ids_texto = self.ids_input.toPlainText().strip()
        if not ids_texto:
            QMessageBox.warning(self, "Atenção", "Por favor, insira pelo menos um ID de questão.")
            return
        
        try:
            lista_ids = [int(id_str.strip()) for id_str in ids_texto.split(',')]
        except ValueError:
            QMessageBox.critical(self, "Erro de Formato", "IDs inválidos. Por favor, insira apenas números separados por vírgula.")
            return

        questoes_base = buscar_questoes_por_ids(lista_ids)
        if not questoes_base:
            QMessageBox.critical(self, "Erro", "Nenhuma das questões com os IDs fornecidos foi encontrada no banco de dados.")
            return

        self.log_dialog = LogDialog(self)
        self.log_dialog.show()
        self.btn_gerar.setEnabled(False)
        self.log_dialog.append_log(f"{len(questoes_base)} questões encontradas.")
        self.log_dialog.append_log("Gerando variações... Este processo pode levar um momento.")
        QApplication.processEvents()

        # --- ETAPA 2: Prepara TODOS os dados para a Geração (LÓGICA CORRIGIDA) ---
        config = carregar_configuracoes()
        num_versoes = self.versoes_spinbox.value()
        
        # 1. Define o número total de questões
        num_total_questoes = len(questoes_base)

        # 2. Lê os valores da interface e calcula os dados da prova
        valor_total = self.valor_total_spinbox.value()
        valor_por_questao = 0.0
        valor_por_questao_display = ""

        if self.check_distribuir_valor.isChecked():
            if num_total_questoes > 0:
                valor_por_questao = valor_total / num_total_questoes
                valor_por_questao_display = f"{valor_por_questao:.2f}".replace('.', ',')
        
        # 3. Cria o dicionário de opções para o MOTOR GERADOR com os dados corretos
        opcoes_geracao = {
            "gabarito": {
                "distribuir": self.check_distribuir.isChecked(),
                "rotacao": self.rotacao_spinbox.value(),
                "embaralhar_questoes": self.check_embaralhar.isChecked()
            },
            "pontuacao": {
                "valor_total": valor_total,
                "valor_por_questao": valor_por_questao,
                "mostrar_valor_individual": self.check_distribuir_valor.isChecked()
            }
        }
        
        # 4. Cria o dicionário de dados para o GERADOR DE PDF com os dados corretos
        self.temp_dados_pdf = {
            "nomeDisciplina": self.disciplina_combo.currentText() if self.disciplina_combo.currentIndex() > 0 else "Seleção por ID",
            "tipoExame": "AVALIAÇÃO",
            "bimestre": self.bimestre_input.text(),
            "nomeProfessor": config.get("nome_professor", ""),
            "siglaCurso": config.get("sigla_curso", ""),
            "nomeCursoCompleto": config.get("nome_curso", ""),
            "nomeEscola": config.get("nome_escola", ""),
            "emailContato": config.get("email_contato", ""),
            "numeroQuestoes": num_total_questoes,
            "valorPorQuestao": valor_por_questao_display,
            "valorTotalProva": f"{valor_total:.2f}".replace('.', ',')
        }
        self.temp_nome_arquivo_base = self.nome_input.text()

        # --- ETAPA 3: Cria e Inicia a Thread (Sem alterações) ---
        self.thread = QThread()
        self.worker = GeradorWorker(questoes_base, num_versoes, opcoes_geracao)
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._handle_geracao_concluida)
        self.worker.error.connect(self._handle_geracao_erro)
        
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        self.thread.start()

    def _handle_geracao_concluida(self, versoes_geradas):
        """
        Executa quando a geração em segundo plano termina com sucesso.
        """
        if not versoes_geradas:
            self._handle_geracao_erro("O motor gerador não retornou nenhuma versão.")
            return

        self.log_dialog.append_log("Variações geradas. Solicitando pasta de destino...")
        
        pasta_destino = QFileDialog.getExistingDirectory(self, "Selecione a pasta para salvar as provas")
        if not pasta_destino:
            self.log_dialog.append_log("Operação cancelada pelo usuário.")
            self.btn_gerar.setEnabled(True)
            self.log_dialog.close()
            return
        
        try:
            criar_pdf_provas(self.temp_nome_arquivo_base, versoes_geradas, pasta_destino, self.temp_dados_pdf, self.log_dialog)
            
            self.log_dialog.finish(success=True)
            QMessageBox.information(self, "Sucesso", f"Provas e gabarito gerados com sucesso em:\n{pasta_destino}")
        except Exception as e:
            error_message = f"Ocorreu um erro na criação do PDF: {e}"
            self.log_dialog.append_log(f"\n❌ ERRO: {error_message}")
            self.log_dialog.finish(success=False)
            QMessageBox.critical(self, "Erro na Geração do PDF", error_message)
        finally:
            self.btn_gerar.setEnabled(True)

    def _handle_geracao_erro(self, mensagem_erro):
        """
        Executa se a geração em segundo plano falhar.
        """
        error_message = f"Ocorreu um erro durante a geração das variações: {mensagem_erro}"
        self.log_dialog.append_log(f"\n❌ ERRO: {error_message}")
        self.log_dialog.finish(success=False)
        QMessageBox.critical(self, "Erro na Geração", error_message)
        self.btn_gerar.setEnabled(True)

    def sizeHint(self):
        """Informa à MainWindow qual o tamanho ideal para esta tela."""
        return QSize(900, 850) # Um pouco mais alto para o novo botão

    def _limpar_campos(self):
        """Limpa os campos da tela para uma nova geração."""
        self.nome_input.clear()
        self.disciplina_combo.setCurrentIndex(0)
        self.bimestre_input.setText("1")
        self.versoes_spinbox.setValue(1)
        self.valor_total_spinbox.setValue(10.0)
        self.ids_input.clear()
        self.lista_questoes_carregadas.clear()
        self.questoes_ativas_verificadas.clear()