# gerador_pdf.py

import os
import subprocess
from jinja2 import Environment, FileSystemLoader
from PyQt5.QtWidgets import QApplication

def criar_pdf_provas(nome_avaliacao, versoes_geradas, pasta_destino, dados_gerais_pdf, log_dialog=None):
    
    def log_message(message):
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
    
    # --- INÍCIO DA CORREÇÃO PRINCIPAL ---
    
    # O loop agora itera sobre a nova estrutura de dados (lista de dicionários)
    for versao_data in versoes_geradas:
        
        # 1. Desempacota os dados corretamente, resolvendo o erro 'str' object has no attribute 'get'
        letra_versao = versao_data.get('letra', 'N/A')
        questoes_da_versao = versao_data.get('questoes', [])
        
        log_message(f"\nGerando arquivos para o Caderno {letra_versao}...")
        
        # 2. Usa a nomenclatura que você pediu
        nome_base_arquivo = f"{nome_avaliacao.replace(' ', '_')}_caderno_{letra_versao}"
        caminho_tex = os.path.join(pasta_destino, f"{nome_base_arquivo}.tex")
        
        # 3. A lógica do gabarito agora itera sobre a lista de questões correta
        itens_gabarito_versao = []
        for q in questoes_da_versao:
            itens_gabarito_versao.append({
                "resposta": str(q.get("gabarito", "?")),
                "id": q.get("id_base", "N/A"),
                "tema": q.get("tema", "N/A")
            })
        todos_gabaritos.append({ "versao": f"Caderno {letra_versao}", "itens": itens_gabarito_versao })
        
        # 4. Prepara os dados para o template da prova
        dados_template = dados_gerais_pdf.copy()
        dados_template['questoes'] = questoes_da_versao
        
        # <<< CORREÇÃO CRUCIAL: Adiciona a letra da versão para o cabeçalho >>>
        dados_template['versao'] = letra_versao

        # --- FIM DA CORREÇÃO PRINCIPAL ---

        with open(caminho_tex, 'w', encoding='utf-8') as f:
            f.write(template_prova.render(dados_template))
        log_message(f"Arquivo .tex do Caderno {letra_versao} criado.")
        log_message(f"Compilando PDF do Caderno {letra_versao} (isso pode levar um momento)...")

        comando = ['xelatex', '-interaction=nonstopmode', '-output-directory', pasta_destino, caminho_tex]
        
        process = None
        try:
            for run_count in range(2):
                process = subprocess.run(comando, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                if process.returncode != 0:
                    process.check_returncode()
            log_message(f"✅ PDF do Caderno {letra_versao} gerado com sucesso.")

        except subprocess.CalledProcessError:
            log_message(f"❌ Erro ao compilar o PDF do Caderno {letra_versao}.")
            if process:
                log_message("--- Saída do Compilador LaTeX (stdout) ---")
                log_message(process.stdout)
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
            log_message(f"--- Saída do Compilador LaTeX ---\n{e.stdout}\n--------------------")
            raise Exception("Erro na compilação do gabarito. Verifique a janela de log.")

    if delete_temp_files:
        log_message("\nLimpando arquivos temporários...")
        extensoes_para_limpar = ['.aux', '.log', '.out', '.tex']
        
        # --- CORREÇÃO DA LIMPEZA: Usa a mesma lógica de nomenclatura ---
        for versao_data in versoes_geradas:
            letra_versao = versao_data.get('letra', 'N/A')
            nome_base_arquivo = f"{nome_avaliacao.replace(' ', '_')}_caderno_{letra_versao}"
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
        
def gerar_pdf_cardapio(questoes, caminho_saida, template_file, contexto_extra, log_dialog=None):
    """
    Renderiza o template do cardápio, usando um LogDialog para manter a UI responsiva.
    """
    def log_message(message):
        """ Helper que envia mensagens para o log e atualiza a UI. """
        if log_dialog:
            log_dialog.append_log(message)
            QApplication.processEvents() # <<< A CHAVE PARA NÃO TRAVAR
        else:
            print(message)

    # ... (o resto da função continua exatamente igual à que eu te enviei antes)
    if not questoes:
        raise ValueError("A lista de questões para o cardápio está vazia.")

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
    
    if contexto_extra:
        template_env.globals.update(contexto_extra)

    try:
        template = template_env.get_template(template_file)
    except Exception as e:
        raise FileNotFoundError(f"Não foi possível encontrar o template do cardápio '{template_file}'. Erro: {e}")

    log_message("Iniciando a geração do PDF do cardápio...")
    
    output_tex = template.render(questoes=questoes)
    
    nome_base_arquivo = os.path.splitext(os.path.basename(caminho_saida))[0]
    pasta_destino = os.path.dirname(caminho_saida)
    caminho_tex = os.path.join(pasta_destino, f"{nome_base_arquivo}.tex")
    
    with open(caminho_tex, 'w', encoding='utf-8') as f:
        f.write(output_tex)
    log_message("Arquivo .tex do cardápio criado.")
    
    log_message("Compilando PDF do cardápio (isso pode levar um momento)...")
    comando = ['xelatex', '-interaction=nonstopmode', '-output-directory', pasta_destino, caminho_tex]
    
    process = None
    try:
        for run_count in range(2):
            process = subprocess.run(comando, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            if process.returncode != 0:
                process.check_returncode()
        log_message("✅ PDF do cardápio gerado com sucesso.")
    except subprocess.CalledProcessError:
        log_message(f"❌ Erro ao compilar o PDF do cardápio.")
        if process:
            log_message("--- Saída do Compilador LaTeX (stdout) ---")
            log_message(process.stdout)
        raise Exception(f"Erro na compilação do LaTeX. Verifique o log.")
    finally:
        log_message("Limpando arquivos temporários...")
        for ext in ['.tex', '.aux', '.log', '.out']:
            try:
                arquivo_para_deletar = os.path.join(pasta_destino, nome_base_arquivo + ext)
                if os.path.exists(arquivo_para_deletar):
                    os.remove(arquivo_para_deletar)
            except OSError: pass
        log_message("Limpeza concluída.")