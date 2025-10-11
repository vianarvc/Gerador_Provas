# interface/gerador_provas.py

# interface/gerador_provas.py

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFileDialog, QScrollArea, QMessageBox, QCheckBox,
    QGroupBox, QGridLayout, QDesktopWidget, QApplication
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt
from database import (
    obter_temas, buscar_questoes_para_prova, contar_questoes_por_criterio,
    obter_disciplinas, obter_disciplina_id_por_nome, carregar_configuracoes
)
from motor_gerador import gerar_versoes_prova
from gerador_pdf import criar_pdf_provas
from .custom_widgets import NoScrollComboBox, NoScrollSpinBox, NoScrollDoubleSpinBox
from .log_dialog import LogDialog

class GeradorProvasWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gerador de Provas por Critérios")
        self.resize(800, 900)
        self._aplicar_estilos() 
        
        main_layout = QVBoxLayout(self)
        
        titulo_label = QLabel("Gerador Automático de Provas")
        titulo_label.setObjectName("TituloPrincipal")
        main_layout.addWidget(titulo_label)

        # --- Bloco 1: Configurações da Avaliação (VERSÃO CORRIGIDA) ---
        config_group = QGroupBox("Configurações da Avaliação")
        config_layout = QVBoxLayout(config_group)
        main_layout.addWidget(config_group)

        config_layout.addWidget(QLabel("Nome da Avaliação:"))
        self.nome_input = QLineEdit()
        self.nome_input.setPlaceholderText("Ex: Eletricidade Básica - 1º Bimestre")
        config_layout.addWidget(self.nome_input)

        campos_capa_layout = QHBoxLayout()
        campos_capa_layout.addWidget(QLabel("Bimestre:"))
        self.bimestre_input = QLineEdit("1") # Valor padrão "1"
        campos_capa_layout.addWidget(self.bimestre_input)
        campos_capa_layout.addSpacing(20)
        campos_capa_layout.addStretch()
        config_layout.addLayout(campos_capa_layout)

        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Número de Versões:"))
        self.versoes_spinbox = NoScrollSpinBox()
        self.versoes_spinbox.setMinimum(1)
        self.versoes_spinbox.setValue(1)
        self.versoes_spinbox.setFixedWidth(150)
        h_layout.addWidget(self.versoes_spinbox)

        h_layout.addSpacing(20)
        h_layout.addWidget(QLabel("Valor Total da Prova:"))
        self.valor_total_spinbox = NoScrollDoubleSpinBox() 
        self.valor_total_spinbox.setDecimals(2)
        self.valor_total_spinbox.setMinimum(0.0)
        self.valor_total_spinbox.setMaximum(1000.0)
        self.valor_total_spinbox.setValue(10.0)
        h_layout.addWidget(self.valor_total_spinbox)

        h_layout.addSpacing(20)
        self.check_distribuir_valor = QCheckBox("Distribuir valor igualmente") 
        self.check_distribuir_valor.setChecked(True)
        h_layout.addWidget(self.check_distribuir_valor)

        h_layout.addStretch()
        config_layout.addLayout(h_layout)
        
        # --- MUDANÇA 2: Adiciona o seletor de Disciplina ---
        questoes_group = QGroupBox("Seleção de Questões")
        self.layout_questoes = QVBoxLayout(questoes_group)
        
        disciplina_layout = QHBoxLayout()
        disciplina_layout.addWidget(QLabel("<b>Selecione a Disciplina para a Prova:</b>"))
        self.disciplina_combo = NoScrollComboBox()
        disciplina_layout.addWidget(self.disciplina_combo, 1)
        self.layout_questoes.addLayout(disciplina_layout)
        
        main_layout.addWidget(questoes_group)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("ScrollCriterios")
        scroll_content = QWidget()
        self.layout_scroll = QVBoxLayout(scroll_content)
        scroll.setWidget(scroll_content)
        self.layout_questoes.addWidget(scroll, 1)

        self.btn_add_tema = QPushButton("➕ Adicionar Tema/Critério")
        self.btn_add_tema.setObjectName("BotaoAcao")
        self.btn_add_tema.clicked.connect(self._add_linha_tema)
        self.layout_questoes.addWidget(self.btn_add_tema)
        
        self.linhas_tema = []
        
        # Carrega disciplinas e conecta o sinal ---
        self._carregar_disciplinas()
        self.disciplina_combo.activated.connect(self._disciplina_selecionada)
        
        # Inicia com a primeira linha de critério
        self._add_linha_tema()

        # --- Bloco 3: Opções de Geração (sem alteração) ---
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

    # --- MUDANÇA 4: Novas funções para carregar e selecionar disciplina ---
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

    # --- _add_linha_tema` agora usa temas filtrados ---
    def _add_linha_tema(self):
        tema_group = QGroupBox("Critério por Tema")
        tema_layout = QVBoxLayout(tema_group)
        
        header_layout = QHBoxLayout()
        combo_tema = NoScrollComboBox()
        
        # Popula com os temas já filtrados pela disciplina selecionada
        disciplina_nome = self.disciplina_combo.currentText()
        if disciplina_nome and disciplina_nome != "-- Selecione --":
            disciplina_id = obter_disciplina_id_por_nome(disciplina_nome)
            temas_filtrados = obter_temas(disciplina_id=disciplina_id)
            combo_tema.addItems(temas_filtrados)
        
        btn_remover = QPushButton("➖")
        btn_remover.setFixedWidth(40)
        btn_remover.clicked.connect(lambda: self._remover_linha_tema(tema_group))
        
        header_layout.addWidget(QLabel("Tema:"))
        header_layout.addWidget(combo_tema, 1)
        header_layout.addWidget(btn_remover)
        tema_layout.addLayout(header_layout)

        grid_layout = QGridLayout()
        # ... (Restante do seu código para criar a grade de spinboxes)
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
        # ... (Fim da criação da grade)
        
        tema_layout.addLayout(grid_layout)
        self.layout_scroll.addWidget(tema_group)

        nova_linha_ref = {"widget": tema_group, "combo": combo_tema, "spins": spins}
        self.linhas_tema.append(nova_linha_ref)
        
        combo_tema.currentIndexChanged.connect(self._atualizar_contadores)
        self._atualizar_contadores_linha(nova_linha_ref)

    # --- MUDANÇA 6: `_atualizar_contadores_linha` agora passa o disciplina_id ---
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

    # --- MUDANÇA 7: `_gerar_prova` agora passa o disciplina_id ---
    def _gerar_prova(self):
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

        log_dialog = LogDialog(self)
        log_dialog.show()
        self.btn_gerar.setEnabled(False)
        
        try:
            config = carregar_configuracoes()
            num_versoes = self.versoes_spinbox.value()
            log_dialog.append_log("Buscando questões no banco de dados...")
            
            questoes_base, avisos = buscar_questoes_para_prova(criterios_granulares, num_versoes)
            
            if avisos:
                log_dialog.append_log("\n--- AVISOS ---")
                for aviso in avisos:
                    log_dialog.append_log(aviso)
                log_dialog.append_log("---------------\n")

            if not questoes_base:
                raise Exception("Nenhuma questão foi encontrada com os critérios selecionados.")

            log_dialog.append_log(f"{len(questoes_base)} questões de base encontradas.")
            log_dialog.append_log("Gerando variações das questões para cada versão...")

            # --- LÓGICA DE VALOR ADICIONADA DE VOLTA ---
            valor_total = self.valor_total_spinbox.value()
            valor_por_questao = 0.0
            valor_por_questao_display = "Vide a Questão"
            if self.check_distribuir_valor.isChecked():
                valor_por_questao = valor_total / num_total_questoes if num_total_questoes > 0 else 0
                valor_por_questao_display = f"{valor_por_questao:.2f}".replace('.', ',')
            
            opcoes_geracao = {
                "gabarito": {
                    "distribuir": self.check_distribuir.isChecked(),
                    "rotacao": self.rotacao_spinbox.value(),
                    "embaralhar_questoes": self.check_embaralhar.isChecked()
                },
                "pontuacao": {
                    "valor_total": valor_total, 
                    "valor_por_questao": valor_por_questao
                }
            }
            
            versoes_geradas = gerar_versoes_prova(questoes_base, num_versoes, opcoes_geracao)
            if not versoes_geradas:
                raise Exception("Não foi possível gerar as versões da prova (motor retornou vazio).")

            log_dialog.append_log("Variações geradas. Solicitando pasta de destino...")
            pasta_destino = QFileDialog.getExistingDirectory(self, "Selecione a pasta para salvar as provas")
            
            if not pasta_destino:
                raise Exception("Nenhuma pasta de destino selecionada. Operação cancelada.")
            
            disciplina_selecionada = self.disciplina_combo.currentText()

            # Validação para garantir que uma disciplina foi selecionada
            if disciplina_selecionada == "-- Selecione --":
                QMessageBox.warning(self, "Erro", "Por favor, selecione uma disciplina para a prova.")
                return

            dados_pdf = { 
                "nomeDisciplina": disciplina_selecionada, 
                "tipoExame": "AVALIAÇÃO",
                "bimestre": self.bimestre_input.text(), # Pega o bimestre da tela
                "nomeProfessor": config.get("nome_professor", ""), # Pega o professor das configs
                # ... o resto dos seus campos (siglaCurso, etc.) continua igual
                "siglaCurso": config.get("sigla_curso", "CURSO"),
                "nomeCursoCompleto": config.get("nome_curso", ""),
                "nomeEscola": config.get("nome_escola", ""),
                "emailContato": config.get("email_contato", ""),
                "nomeescola": config.get("nome_escola", ""),
                "numeroQuestoes": num_total_questoes, 
                "valorPorQuestao": valor_por_questao_display, 
                "valorTotalProva": f"{valor_total:.2f}".replace('.', ',') 
            }

            nome_arquivo_base = self.nome_input.text()
            criar_pdf_provas(nome_arquivo_base, versoes_geradas, pasta_destino, dados_pdf, log_dialog)
            
            log_dialog.finish(success=True)
            QMessageBox.information(self, "Sucesso", f"Provas e gabarito gerados com sucesso em:\n{pasta_destino}")

        except Exception as e:
            error_message = f"Ocorreu um erro: {e}"
            log_dialog.append_log(f"\n❌ ERRO: {error_message}")
            self.og_dialog.finish(success=False)
            QMessageBox.critical(self, "Erro na Geração", error_message)
        
        finally:
            self.btn_gerar.setEnabled(True)

    def _aplicar_estilos(self):
        """Define e aplica o Qt Style Sheet (QSS) para a janela de geração."""
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

        /* CAMPOS DE INPUT E COMBOBOX */
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
            border: 1px solid #bdc3c7;
            border-radius: 5px;
            padding: 5px;
            background-color: white;
            selection-background-color: #3498db;
        }
        
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
            border: 1px solid #3498db;
        }

        /* LABEL DE CONTADOR */
        QLabel {
             color: #2c3e50;
        }
        QLabel[style*="gray"] { /* Label de contagem de questões */
            font-size: 11px;
            color: #7f8c8d;
        }
        
        /* SCROLL AREA DOS CRITÉRIOS */
        #ScrollCriterios {
             border: 1px solid #bdc3c7;
             border-radius: 5px;
             background-color: #ecf0f1;
        }
        
        /* BOTÃO PRINCIPAL (Gerar Prova) */
        #BotaoPrincipal {
            background-color: #2ecc71; /* Verde */
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 30px;
            font-weight: bold;
            margin-top: 15px;
            min-width: 300px
        }
        #BotaoPrincipal:hover {
            background-color: #27ae60;
        }
        
        /* BOTÃO DE AÇÃO (Adicionar/Remover Tema) */
        #BotaoAcao {
            background-color: #3498db; /* Azul */
            color: white;
            border: none;
            border-radius: 5px;
            padding: 5px 10px;
            font-size: 18px;
            min-height: 25px;
            min-width: 200px
        }
        #BotaoAcao:hover {
            background-color: #2980b9;
        }
        
        QPushButton[text^="➖"] { /* Botão remover */
            background-color: #e74c3c; /* Vermelho */
        }
        QPushButton[text^="➖"]:hover {
            background-color: #c0392b;
        }
        """
        self.setStyleSheet(style)

    def _center(self): 
        """ Centraliza a janela na tela. """
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

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

    def showEvent(self, event):
        """Este método é chamado automaticamente pelo Qt antes de a janela ser exibida."""
        self._center()
        super().showEvent(event)