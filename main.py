# main.py

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from interface.MenuInicial import MenuInicialWindow
from database import init_db

if __name__ == '__main__':
    # Garante que o banco de dados e as tabelas existam
    init_db()
    
    # Inicia o aplicativo
    app = QApplication(sys.argv)

    # Define a fonte padrão para toda a aplicação.
    default_font = QFont("Arial", 12)
    app.setFont(default_font)
    
    window = MenuInicialWindow()
    window.show()
    sys.exit(app.exec_())