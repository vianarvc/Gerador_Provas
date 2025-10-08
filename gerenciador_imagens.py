# gerenciador_imagens.py

import os
import shutil
import time
from PyQt5.QtWidgets import QFileDialog, QApplication

# Define o nome da pasta de imagens
PASTA_IMAGENS = "img"

def inicializar_pasta_imagens():
    """Garante que a pasta de imagens exista."""
    if not os.path.exists(PASTA_IMAGENS):
        os.makedirs(PASTA_IMAGENS)

def _gerar_novo_nome(caminho_original):
    """Gera um novo nome de arquivo único baseado no timestamp."""
    _, extensao = os.path.splitext(caminho_original)
    timestamp = int(time.time() * 100)
    novo_nome = f"{timestamp}{extensao}"
    return os.path.join(PASTA_IMAGENS, novo_nome)

def copiar_arquivo_imagem_para_pasta_local(caminho_origem):
    """
    Copia um arquivo de imagem de um caminho de origem externo para a pasta local 'img'.
    Renomeia o arquivo para evitar conflitos e retorna o novo caminho relativo.
    """
    if not os.path.exists(caminho_origem):
        return ""
    
    inicializar_pasta_imagens()
    novo_caminho_relativo = _gerar_novo_nome(caminho_origem)
    
    try:
        shutil.copy(caminho_origem, novo_caminho_relativo)
        return novo_caminho_relativo.replace('\\', '/')
    except Exception as e:
        print(f"Erro ao copiar a imagem {caminho_origem}: {e}")
        return ""

def selecionar_e_copiar_imagem():
    """
    Abre um diálogo para o usuário selecionar uma imagem, copia para a pasta local
    e retorna o novo caminho relativo.
    """
    inicializar_pasta_imagens()
    # Abre o diálogo de arquivo
    caminho_origem, _ = QFileDialog.getOpenFileName(
        None, 
        "Selecionar Imagem", 
        "", 
        "Imagens (*.png *.jpg *.jpeg *.bmp *.gif)"
    )

    if caminho_origem:
        return copiar_arquivo_imagem_para_pasta_local(caminho_origem)
    return None

def salvar_pixmap(pixmap):
    """
    Salva um QPixmap da área de transferência na pasta local 'img' e retorna o caminho.
    """
    inicializar_pasta_imagens()
    # Gera um nome de arquivo temporário para salvar o pixmap
    caminho_temp = os.path.join(PASTA_IMAGENS, f"clip_{int(time.time()*100)}.png")
    
    if pixmap.save(caminho_temp, "PNG"):
        return caminho_temp.replace('\\', '/')
    return None

def remover_imagem(caminho_relativo):
    """
    Remove um arquivo de imagem da pasta 'img' se ele não estiver sendo usado por outra questão.
    (NOTA: A verificação de uso por outras questões não está implementada, apenas remove o arquivo).
    """
    if caminho_relativo and os.path.exists(caminho_relativo):
        try:
            os.remove(caminho_relativo)
            print(f"Imagem {caminho_relativo} removida.")
        except OSError as e:
            print(f"Erro ao remover a imagem {caminho_relativo}: {e}")