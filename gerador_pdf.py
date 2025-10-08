# gerador_pdf.py

import os
import subprocess
from jinja2 import Environment, FileSystemLoader
from PyQt5.QtWidgets import QApplication

def criar_pdf_provas(nome_avaliacao, versoes_geradas, pasta_destino, dados_gerais_pdf, log_dialog=None):
    
    def log_message(message):
        """ Helper para enviar mensagens para o log ou para o console """
        if log_dialog:
            log_dialog.append_log(message)
        else:
            print(message)

    template_env = Environment(
        loader=FileSystemLoader(searchpath="."),
        block_start_string='<<%',
        block_end_string='%>>',
        variable_start_string='<<',
        variable_end_string='>>',
        comment_start_string='(*',
        comment_end_string='*)',
        autoescape=False
    )
    
    delete_temp_files = True
    
    try:
        template_prova = template_env.get_template('modelo_prova.tex')
        template_gabarito = template_env.get_template('modelo_gabarito.tex')
    except Exception as e:
        raise FileNotFoundError(f"Não foi possível encontrar um arquivo de template (.tex). Erro: {e}")

    todos_gabaritos = []

    log_message(f"Iniciando compilação de {len(versoes_geradas)} versão(ões)...")
    for i, versao in enumerate(versoes_geradas):
        log_message(f"\nGerando arquivos para a Versão {i+1}...")
        nome_base_arquivo = f"{nome_avaliacao.replace(' ', '_')}_v{i+1}"
        caminho_tex = os.path.join(pasta_destino, f"{nome_base_arquivo}.tex")
        
        itens_gabarito_versao = []
        for q in versao:
            itens_gabarito_versao.append({
                "resposta": str(q.get("gabarito", "?")),
                "id": q.get("id_base", "N/A"),
                "tema": q.get("tema", "N/A")
            })
        todos_gabaritos.append({ "versao": f"Versão {i+1}", "itens": itens_gabarito_versao })
        
        dados_template = dados_gerais_pdf.copy()
        dados_template['questoes'] = versao

        with open(caminho_tex, 'w', encoding='utf-8') as f:
            f.write(template_prova.render(dados_template))
        log_message(f"Arquivo .tex da Versão {i+1} criado.")
        log_message(f"Compilando PDF da Versão {i+1} (isso pode levar um momento)...")

        comando = ['xelatex', '-interaction=nonstopmode', '-output-directory', pasta_destino, caminho_tex]
        """nome_base_arquivo_tex = os.path.basename(caminho_tex)
        comando = ['xelatex', '-interaction=nonstopmode', nome_base_arquivo_tex]"""
        
        process = None
        try:
            for run_count in range(2):
                process = subprocess.run(comando, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                if process.returncode != 0:
                    process.check_returncode()
            log_message(f"✅ PDF da Versão {i+1} gerado com sucesso.")

        except subprocess.CalledProcessError:
            log_message(f"❌ Erro ao compilar o PDF da Versão {i+1}.")
            if process:
                log_message("--- Saída do Compilador LaTeX (stdout) ---")
                log_message(process.stdout)
                log_message("------------------------------------------")
            raise Exception(f"Erro na compilação do LaTeX. Verifique a janela de log.")

    if todos_gabaritos:
        log_message("\nGerando PDF do Gabarito...")
        caminho_tex_gabarito = os.path.join(pasta_destino, f"{nome_avaliacao.replace(' ', '_')}_GABARITO.tex")
        with open(caminho_tex_gabarito, 'w', encoding='utf-8') as f:
            f.write(template_gabarito.render({"versoes": todos_gabaritos}))
        
        comando_gabarito = ['xelatex', '-interaction=nonstopmode', '-output-directory', pasta_destino, caminho_tex_gabarito]
        try:
            for _ in range(2):
                subprocess.run(comando_gabarito, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            log_message("✅ PDF do Gabarito gerado com sucesso.")
        except subprocess.CalledProcessError as e:
            log_message("❌ Erro ao compilar o PDF do Gabarito.")
            log_message("--- Saída do Compilador LaTeX (stdout) ---")
            log_message(e.stdout)
            log_message("------------------------------------------")
            raise Exception("Erro na compilação do gabarito. Verifique a janela de log.")

    if delete_temp_files:
        log_message("\nLimpando arquivos temporários...")
        extensoes_para_limpar = ['.tex', '.aux', '.log', '.out']
        for i in range(len(versoes_geradas)):
            nome_base_arquivo = f"{nome_avaliacao.replace(' ', '_')}_v{i+1}"
            for ext in extensoes_para_limpar:
                arquivo_para_deletar = os.path.join(pasta_destino, nome_base_arquivo + ext)
                if os.path.exists(arquivo_para_deletar):
                    try: os.remove(arquivo_para_deletar)
                    except OSError: pass
        
        nome_gabarito = f"{nome_avaliacao.replace(' ', '_')}_GABARITO"
        for ext in extensoes_para_limpar:
            arquivo_gabarito_para_deletar = os.path.join(pasta_destino, nome_gabarito + ext)
            if os.path.exists(arquivo_gabarito_para_deletar):
                try: os.remove(arquivo_gabarito_para_deletar)
                except OSError: pass
        log_message("Limpeza concluída.")