# interface/gerador_provas.py

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFileDialog, QScrollArea, QMessageBox, QCheckBox,
    QGroupBox, QGridLayout, QDesktopWidget, QApplication, QSizePolicy
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QThread

from database import (
    obter_temas, buscar_questoes_para_prova, contar_questoes_por_criterio,
    obter_disciplinas, obter_disciplina_id_por_nome, carregar_configuracoes
)
from motor_gerador.core import gerar_versoes_prova
from gerador_pdf import criar_pdf_provas
from .custom_widgets import (
    MeuLineEdit, MeuSpinBox, MeuDoubleSpinBox, MeuComboBox, MeuLabel, MeuGroupBox, EstilosApp,
    NoScrollComboBox, NoScrollSpinBox, MeuCheckBox, MeuBotao
)
from .log_dialog import LogDialog
from .worker_gerador import GeradorWorker

class GeradorProvasScreen(QWidget):
    voltar_pressed = pyqtSignal()
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gerar Prova por Critérios")

        # Layout principal da tela
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Scroll principal
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("ScrollPrincipal")
        main_layout.addWidget(scroll_area)

        # Conteúdo do scroll
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)
        content_layout = QVBoxLayout(scroll_content)

        # Título principal
        titulo_label = QLabel("Gerador Automático de Provas")
        titulo_label.setObjectName("TituloPrincipal")
        content_layout.addWidget(titulo_label)

        # --- Configurações da Avaliação ---
        config_group = QGroupBox("Configurações da Avaliação")
        config_layout = QVBoxLayout(config_group)
        content_layout.addWidget(config_group)

        config_layout.addWidget(QLabel("Nome da Avaliação:"))
        self.nome_input = MeuLineEdit()
        self.nome_input.setPlaceholderText("Ex: Eletricidade Básica - 1º Bimestre")
        config_layout.addWidget(self.nome_input)

        campos_capa_layout = QHBoxLayout()
        campos_capa_layout.addWidget(QLabel("Bimestre:"))
        self.bimestre_input = MeuLineEdit()
        self.bimestre_input.setText("1")
        campos_capa_layout.addWidget(self.bimestre_input)
        campos_capa_layout.addSpacing(20)
        campos_capa_layout.addStretch()
        config_layout.addLayout(campos_capa_layout)

        h_layout_1 = QHBoxLayout()
        h_layout_1.addWidget(QLabel("Número de Versões:"))
        self.versoes_spinbox = MeuSpinBox()
        self.versoes_spinbox.setMinimum(1)
        self.versoes_spinbox.setValue(1)
        self.versoes_spinbox.setFixedWidth(150)
        h_layout_1.addWidget(self.versoes_spinbox)

        self.check_embaralhar = MeuCheckBox("Embaralhar Ordem das Questões")
        self.check_embaralhar.setChecked(False)
        h_layout_1.addWidget(self.check_embaralhar)
        h_layout_1.addStretch()
        config_layout.addLayout(h_layout_1)

        h_layout_2 = QHBoxLayout()
        h_layout_2.addWidget(QLabel("Valor Total da Prova:"))
        self.valor_total_spinbox = MeuDoubleSpinBox()
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
        config_layout.addLayout(h_layout_2)

        # --- Seleção de Questões ---
        questoes_group = QGroupBox("Seleção de Questões")
        self.layout_questoes = QVBoxLayout(questoes_group)
        content_layout.addWidget(questoes_group)

        disciplina_layout = QHBoxLayout()
        disciplina_layout.addWidget(QLabel("<b>Selecione a Disciplina para a Prova:</b>"))
        self.disciplina_combo = MeuComboBox()
        disciplina_layout.addWidget(self.disciplina_combo, 1)
        self.layout_questoes.addLayout(disciplina_layout)

        # Scroll interno para linhas de tema
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("ScrollCriterios")
        scroll.setMinimumHeight(350)
        scroll_content = QWidget()
        self.layout_scroll = QVBoxLayout(scroll_content)
        scroll.setWidget(scroll_content)

        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout_questoes.addWidget(scroll, 1)

        # Botão adicionar tema
        self.btn_add_tema = MeuBotao("➕ Adicionar Tema/Critério", tipo="acao")
        self.btn_add_tema.clicked.connect(self._add_linha_tema)
        self.layout_questoes.addWidget(self.btn_add_tema)

        self.linhas_tema = []

        # --- Opções de Geração ---
        gabarito_group = QGroupBox("Opções de Geração e Gabarito")
        gabarito_layout = QVBoxLayout(gabarito_group)
        content_layout.addWidget(gabarito_group)

        checkboxes_layout = QHBoxLayout()
        self.check_distribuir = MeuCheckBox("Distribuir Gabarito (A, B, C...)")
        self.check_distribuir.setChecked(True)
        checkboxes_layout.addWidget(self.check_distribuir)
        checkboxes_layout.addStretch()
        gabarito_layout.addLayout(checkboxes_layout)

        rotacao_layout = QHBoxLayout()
        rotacao_layout.addWidget(QLabel("Rotação do Gabarito entre versões (n+):"))
        self.rotacao_spinbox = MeuSpinBox()
        self.rotacao_spinbox.setMinimum(0)
        self.rotacao_spinbox.setValue(1)
        rotacao_layout.addWidget(self.rotacao_spinbox)
        rotacao_layout.addStretch()
        gabarito_layout.addLayout(rotacao_layout)

        # --- Botões finais ---
        botoes_layout = QHBoxLayout()
        self.btn_gerar = MeuBotao("🚀 Gerar Prova", tipo="principal")
        self.btn_gerar.clicked.connect(self._gerar_prova)
        
        botoes_layout.addStretch()
        botoes_layout.addWidget(self.btn_gerar)
        content_layout.addLayout(botoes_layout)

        # Inicializa com a primeira linha de tema
        self._carregar_disciplinas()
        self.disciplina_combo.activated.connect(self._disciplina_selecionada)
        self._add_linha_tema()
    
    def sizeHint(self):
        """Informa à MainWindow qual o tamanho ideal para esta tela."""
        return QSize(1100, 850)
    
    def _limpar_campos(self):
        """Limpa todos os campos e reseta a tela para o estado inicial."""
        self.nome_input.clear()
        self.bimestre_input.setText("1")
        self.versoes_spinbox.setValue(1)
        self.valor_total_spinbox.setValue(10.0)
        self.disciplina_combo.setCurrentIndex(0)

        # Remove todas as linhas de critério, exceto a primeira
        while len(self.linhas_tema) > 1:
            linha_ref = self.linhas_tema.pop()
            linha_ref["widget"].deleteLater()
        
        # Limpa os campos da primeira linha
        if self.linhas_tema:
            primeira_linha = self.linhas_tema[0]
            primeira_linha["combo"].clear()
            for formato in primeira_linha["spins"]:
                for dificuldade in primeira_linha["spins"][formato]:
                    primeira_linha["spins"][formato][dificuldade]["spin"].setValue(0)
        
        self._disciplina_selecionada()

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

    def _add_linha_tema(self):
        tema_group = MeuGroupBox("Critério por Tema")
        tema_layout = QVBoxLayout(tema_group)
        
        header_layout = QHBoxLayout()
        combo_tema = NoScrollComboBox()
        
        # Popula com os temas já filtrados pela disciplina selecionada
        disciplina_nome = self.disciplina_combo.currentText()
        if disciplina_nome and disciplina_nome != "-- Selecione --":
            disciplina_id = obter_disciplina_id_por_nome(disciplina_nome)
            temas_filtrados = obter_temas(disciplina_id=disciplina_id)
            combo_tema.addItems(temas_filtrados)
        
        btn_remover = MeuBotao("➖", tipo="remover")
        btn_remover.setFixedWidth(40)
        btn_remover.clicked.connect(lambda: self._remover_linha_tema(tema_group))
        
        header_layout.addWidget(QLabel("Tema:"))
        header_layout.addWidget(combo_tema, 1)
        header_layout.addWidget(btn_remover)
        tema_layout.addLayout(header_layout)

        grid_layout = QGridLayout()
        formatos = ["Múltipla Escolha", "Verdadeiro ou Falso", "Discursiva"]
        dificuldades = ["Fácil", "Média", "Difícil"]
        spins = {}
        for i, formato in enumerate(formatos):
            grid_layout.addWidget(QLabel(f"<b>{formato}</b>"), i + 1, 0)
            spins[formato] = {}
            for j, dificuldade in enumerate(dificuldades):
                spin = NoScrollSpinBox(); lbl_count = QLabel("(0 disp.)"); lbl_count.setStyleSheet("color: gray;")
                cell_layout = QVBoxLayout(); cell_layout.addWidget(spin); cell_layout.addWidget(lbl_count, 0, Qt.AlignCenter)
                grid_layout.addLayout(cell_layout, i + 1, j + 1)
                spins[formato][dificuldade] = {"spin": spin, "label": lbl_count}
        grid_layout.addWidget(QLabel("<b>Fácil</b>"), 0, 1, Qt.AlignCenter)
        grid_layout.addWidget(QLabel("<b>Média</b>"), 0, 2, Qt.AlignCenter)
        grid_layout.addWidget(QLabel("<b>Difícil</b>"), 0, 3, Qt.AlignCenter)
        
        tema_layout.addLayout(grid_layout)
        self.layout_scroll.addWidget(tema_group)

        nova_linha_ref = {"widget": tema_group, "combo": combo_tema, "spins": spins}
        self.linhas_tema.append(nova_linha_ref)
        
        combo_tema.currentIndexChanged.connect(self._atualizar_contadores)
        self._atualizar_contadores_linha(nova_linha_ref)

    def _atualizar_contadores_linha(self, linha_ref):
        tema = linha_ref["combo"].currentText()
        disciplina_id = obter_disciplina_id_por_nome(self.disciplina_combo.currentText())

        # Não faz a busca se a disciplina ou tema não estiverem selecionados
        if not tema or not disciplina_id:
            for formato, dificuldades in linha_ref["spins"].items():
                for dificuldade, widgets in dificuldades.items():
                    widgets["label"].setText("(0 disp.)")
                    widgets["spin"].setMaximum(0)
            return

        for formato, dificuldades in linha_ref["spins"].items():
            for dificuldade, widgets in dificuldades.items():
                count = contar_questoes_por_criterio(tema, formato, dificuldade, disciplina_id=disciplina_id)
                widgets["label"].setText(f"({count} disp.)")
                widgets["spin"].setMaximum(count)

    def _gerar_prova(self):
        # --- ETAPA 1: Coleta de Dados e Validação (Executa na Thread Principal) ---
        from motor_gerador.cache_manager import iniciar_nova_geracao_cache
        
        nome_prova = self.nome_input.text().strip() or "Prova_Sem_Nome"
        iniciar_nova_geracao_cache(f"prova_{nome_prova}")
        
        disciplina_id = obter_disciplina_id_por_nome(self.disciplina_combo.currentText())
        if not disciplina_id:
            QMessageBox.warning(self, "Erro", "Por favor, selecione uma disciplina.")
            return

        criterios_granulares = {}
        num_total_questoes = 0
        for linha in self.linhas_tema:
            tema = linha["combo"].currentText()
            if not tema: continue
            chave_criterio = (disciplina_id, tema)
            if chave_criterio not in criterios_granulares:
                criterios_granulares[chave_criterio] = {}
            for formato, dificuldades in linha["spins"].items():
                if formato not in criterios_granulares[chave_criterio]:
                    criterios_granulares[chave_criterio][formato] = {}
                for dificuldade, widgets in dificuldades.items():
                    qtd = widgets["spin"].value()
                    if qtd > 0:
                        criterios_granulares[chave_criterio][formato][dificuldade] = qtd
                        num_total_questoes += qtd
        
        if num_total_questoes == 0:
            QMessageBox.warning(self, "Erro", "Nenhuma questão foi selecionada.")
            return

        # Busca as questões na thread principal (geralmente rápido)
        num_versoes = self.versoes_spinbox.value()
        questoes_base, avisos = buscar_questoes_para_prova(criterios_granulares, num_versoes)

        if not questoes_base:
            QMessageBox.critical(self, "Erro", "Nenhuma questão foi encontrada com os critérios selecionados.")
            return

        # Prepara o log e desabilita o botão para evitar cliques duplos
        self.log_dialog = LogDialog(self)
        self.log_dialog.show()
        self.btn_gerar.setEnabled(False)
        self.log_dialog.append_log("Buscando questões no banco de dados...")
        if avisos:
            self.log_dialog.append_log("\n--- AVISOS ---")
            for aviso in avisos:
                self.log_dialog.append_log(aviso)
            self.log_dialog.append_log("---------------\n")
        self.log_dialog.append_log(f"{len(questoes_base)} questões de base encontradas.")
        self.log_dialog.append_log("Gerando variações... Este processo pode levar um momento.")
        QApplication.processEvents() # Força a UI a atualizar antes de iniciar a thread

        # --- ETAPA 2: Prepara os dados para a Thread ---
        # Coleta todas as informações necessárias ANTES de iniciar a thread.
        config = carregar_configuracoes()
        valor_total = self.valor_total_spinbox.value()
        valor_por_questao = 0.0
        valor_por_questao_display = "Vide a Questão"
        if self.check_distribuir_valor.isChecked():
            valor_por_questao = valor_total / num_total_questoes if num_total_questoes > 0 else 0
            valor_por_questao_display = f"{valor_por_questao:.2f}".replace('.', ',')

        opcoes_geracao = {
            "nome_prova": nome_prova,  # ← ADICIONADO para o cache
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

        # Salva os dados que serão necessários DEPOIS que a thread terminar
        self.temp_dados_pdf = { 
            "nomeDisciplina": self.disciplina_combo.currentText(), 
            "tipoExame": "AVALIAÇÃO",
            "bimestre": self.bimestre_input.text(),
            "nomeProfessor": config.get("nome_professor", ""),
            "siglaCurso": config.get("sigla_curso", "CURSO"),
            "nomeCursoCompleto": config.get("nome_curso", ""),
            "nomeEscola": config.get("nome_escola", ""),
            "emailContato": config.get("email_contato", ""),
            "numeroQuestoes": num_total_questoes, 
            "valorPorQuestao": valor_por_questao_display, 
            "valorTotalProva": f"{valor_total:.2f}".replace('.', ',') 
        }
        self.temp_nome_arquivo_base = self.nome_input.text()

        # --- ETAPA 3: Cria e Inicia a Thread ---
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
        Este método é chamado quando a thread termina com sucesso.
        Ele recebe os resultados e continua o processo na thread principal.
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
        """Este método é chamado se a thread encontrar um erro."""
        error_message = f"Ocorreu um erro durante a geração das versões:\n{mensagem_erro}"
        self.log_dialog.append_log(f"\n❌ ERRO: {error_message}")
        self.log_dialog.finish(success=False)
        QMessageBox.critical(self, "Erro na Geração", error_message)
        self.btn_gerar.setEnabled(True)

    def _remover_linha_tema(self, linha_widget):
        if len(self.linhas_tema) <= 1:
            QMessageBox.warning(self, "Aviso", "Pelo menos um critério de tema é necessário.")
            return
        for linha in self.linhas_tema:
            if linha["widget"] == linha_widget:
                linha_widget.deleteLater()
                self.linhas_tema.remove(linha)
                break
        self._atualizar_contadores()

    def _atualizar_contadores(self):
        """Dispara a atualização de contagem para todas as linhas de critério."""
        for linha in self.linhas_tema:
            self._atualizar_contadores_linha(linha)