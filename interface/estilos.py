# interface/estilos.py

def carregar_estilo_global():
    """
    Retorna uma string contendo todo o QSS (folha de estilos)
    para a aplicação, garantindo uma aparência consistente.
    """
    return """
        /* ===============================================================
           ESTILOS GERAIS PARA APLICAÇÃO
           =============================================================== */
        
        QWidget, QDialog {
            background-color: #f7f7f7;
            font-family: Arial;
            color: #2c3e50;
        }

        /* ===============================================================
           TÍTULOS
           =============================================================== */

        #TituloPrincipal, #TituloMenu, #TituloDialogo {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 2px solid #3498db;
        }

        #TituloDialogo {
            font-size: 18px;
        }

        /* ===============================================================
           BOTÕES
           =============================================================== */

        /* Estilo base para botões */
        QPushButton {
            border: none;
            border-radius: 8px;
            padding: 10px;
            font-size: 16px; 
            font-weight: bold;
            color: white;
            min-height: 30px;
        }
        
        /* Botões Padrão (Azuis) - Ex: Menu Principal */
        QPushButton {
            background-color: #3498db;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }

        /* Botão Principal de Ação (Verde) */
        #BotaoPrincipal {
            background-color: #27ae60;
            font-size: 24px;
        }
        #BotaoPrincipal:hover {
            background-color: #2ecc71;
        }

        /* Botão Secundário / Voltar (Cinza) */
        #BotaoVoltar {
            background-color: #7f8c8d;
        }
        #BotaoVoltar:hover {
            background-color: #95a5a6;
        }
        
        /* Botão de Ação Menor (Adicionar Critério) */
        #BotaoAcao {
            background-color: #3498db;
            padding: 5px 10px;
            font-size: 16px;
        }
        #BotaoAcao:hover {
            background-color: #2980b9;
        }

        /* Botão de Remoção (Vermelho) */
        QPushButton[text^="➖"] {
            background-color: #e74c3c;
            max-width: 40px;
        }
        QPushButton[text^="➖"]:hover {
            background-color: #c0392b;
        }


        /* ===============================================================
           OUTROS WIDGETS
           =============================================================== */

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

        QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QListWidget {
            border: 1px solid #bdc3c7;
            border-radius: 5px;
            padding: 5px;
            background-color: white;
        }
    """