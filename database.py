# database.py

import sqlite3
import json
import zipfile
import os
import shutil

DB_NAME = 'banco_questoes.db'
SETTINGS_FILE = 'settings.json'
IMAGE_DIR = 'imagens_questoes'

def connect_db():
    """Conecta ao banco de dados SQLite."""
    return sqlite3.connect(DB_NAME)

def init_db():
    """Cria as tabelas e adiciona as novas colunas se elas não existirem."""
    conn = connect_db()
    cursor = conn.cursor()
    
    # Cria a tabela de disciplinas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disciplinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    """)
    
    # Cria a tabela de questões com a estrutura base
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tema TEXT NOT NULL,
            enunciado TEXT NOT NULL,
            formato_questao TEXT,
            dificuldade TEXT,
            imagem TEXT,
            imagem_largura_percentual INTEGER,
            parametros TEXT,
            linguagem TEXT,
            resposta_correta TEXT,
            alternativa_a TEXT,
            alternativa_b TEXT,
            alternativa_c TEXT,
            alternativa_d TEXT,
            alternativa_e TEXT,
            tipo_questao TEXT,
            gerar_alternativas_auto BOOLEAN,
            unidade_resposta TEXT,
            permitir_negativos BOOLEAN,
            is_teorica BOOLEAN,
            grupo TEXT,
            ativa BOOLEAN DEFAULT 1
        )
    """)
    
    # Função auxiliar para adicionar colunas de forma segura
    def check_and_add_column(col_name, col_type):
        try:
            cursor.execute(f"ALTER TABLE questoes ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                print(f"Erro ao adicionar coluna {col_name}: {e}")

    # Adiciona as colunas novas via ALTER TABLE para compatibilidade
    check_and_add_column('disciplina_id', 'INTEGER REFERENCES disciplinas(id)')
    check_and_add_column('fonte', 'TEXT')
    check_and_add_column('tipo_resposta', 'TEXT') 

    conn.commit()
    conn.close()

# --- FUNÇÕES DE DISCIPLINAS ---

def salvar_disciplina(nome):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO disciplinas (nome) VALUES (?)", (nome,))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        cursor.execute("SELECT id FROM disciplinas WHERE nome = ?", (nome,))
        return cursor.fetchone()[0]
    finally:
        conn.close()

def obter_disciplinas():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM disciplinas ORDER BY nome")
    disciplinas = [row[0] for row in cursor.fetchall()]
    conn.close()
    if "Todas" not in disciplinas:
        disciplinas.insert(0, "Todas")
    return disciplinas
    
def obter_disciplina_id_por_nome(nome):
    if not nome or nome == "Todas": return None
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM disciplinas WHERE nome = ?", (nome,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else None

def obter_disciplina_nome_por_id(disciplina_id):
    if disciplina_id is None: 
        return ""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM disciplinas WHERE id = ?", (disciplina_id,))
    resultado = cursor.fetchone()
    conn.close()
    if resultado:
        return resultado[0]  
    else:
        ""

# --- FUNÇÕES DE TEMAS ---
def salvar_ordem_temas(lista_de_temas):
    """Salva a ordem customizada dos temas em um arquivo de configuração."""
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        settings = {}
    
    settings['ordem_temas'] = lista_de_temas
    
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4)

def obter_temas(disciplina_id=None):
    """Retorna uma lista de temas, respeitando a ordem salva pelo usuário, filtrada por disciplina."""
    ordem_salva = []
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            ordem_salva = settings.get('ordem_temas', [])
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    conn = connect_db()
    cursor = conn.cursor()
    
    query = "SELECT DISTINCT tema FROM questoes"
    params = ()
    if disciplina_id is not None:
        query += " WHERE disciplina_id = ?"
        params = (disciplina_id,)

    cursor.execute(query, params)
    temas_db_set = {row[0] for row in cursor.fetchall()}
    conn.close()

    temas_finais = [tema for tema in ordem_salva if tema in temas_db_set]
    temas_novos = sorted(list(temas_db_set - set(temas_finais)))
    temas_finais.extend(temas_novos)
    
    if temas_finais and "Todos" not in temas_finais:
        temas_finais.insert(0, "Todos")
    elif not temas_finais and temas_db_set:
        temas_finais = sorted(list(temas_db_set))
        temas_finais.insert(0, "Todos")
        
    return temas_finais

# --- FUNÇÕES DE QUESTÕES ---

def obter_questoes_por_tema(tema, disciplina_id=None):
    """Busca todas as questões de um tema/disciplina ou todas se o tema for 'Todos'."""
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    conditions = []
    params = []
    
    if tema != "Todos" and tema is not None:
        conditions.append("tema = ?")
        params.append(tema)

    if disciplina_id is not None:
        conditions.append("disciplina_id = ?")
        params.append(disciplina_id)
        
    query = "SELECT * FROM questoes"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC"

    cursor.execute(query, params)
    questoes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return questoes
    
def salvar_questao(dados_dict):
    conn = connect_db()
    cursor = conn.cursor()
    colunas = ', '.join(dados_dict.keys())
    placeholders = ', '.join(['?'] * len(dados_dict))
    valores = list(dados_dict.values())
    cursor.execute(f"INSERT INTO questoes ({colunas}) VALUES ({placeholders})", valores)
    conn.commit()
    conn.close()

def atualizar_questao(questao_id, dados_dict):
    conn = connect_db()
    cursor = conn.cursor()
    set_clause = ', '.join([f"{key} = ?" for key in dados_dict.keys()])
    valores = list(dados_dict.values())
    valores.append(questao_id)
    cursor.execute(f"UPDATE questoes SET {set_clause} WHERE id = ?", valores)
    conn.commit()
    conn.close()

def obter_questao_por_id(questao_id):
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questoes WHERE id = ?", (questao_id,))
    questao = cursor.fetchone()
    conn.close()
    return dict(questao) if questao else None

def excluir_questao(questao_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM questoes WHERE id = ?", (questao_id,))
    conn.commit()
    conn.close()
    return True
# ----------------------------------------------------
# FUNÇÕES PARA GERAÇÃO DE PROVAS (AJUSTADAS - D1)
# ----------------------------------------------------

def contar_questoes_por_criterio(tema, formato, dificuldade, disciplina_id=None):
    """Conta quantas questões ATIVAS existem para os critérios, com filtro de disciplina."""
    conn = connect_db()
    cursor = conn.cursor()
    
    # Construção dinâmica da query
    conditions = ["formato_questao = ?", "dificuldade = ?", "ativa = 1"]
    params = [formato, dificuldade]
    
    if tema != "Todos":
        conditions.append("tema = ?")
        params.append(tema) 
        
    if disciplina_id is not None:
        conditions.append("disciplina_id = ?")
        params.append(disciplina_id)
    
    query = "SELECT COUNT(*) FROM questoes WHERE " + " AND ".join(conditions)
    
    cursor.execute(query, params)
    count = cursor.fetchone()[0]
    conn.close()
    return count

def buscar_questoes_para_prova(criterios_granulares, num_versoes=1):
    """
    Busca questões no banco de dados com base em critérios granulares e tenta
    garantir que haja questões suficientes para as versões.
    
    Retorna uma lista de questões base e uma lista de avisos.
    """
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    questoes_base = []
    avisos = []
    
    criterios = []
    # --- INÍCIO DA CORREÇÃO ---
    # A 'chave_criterio' agora é uma tupla: (disciplina_id, tema)
    for chave_criterio, formatos in criterios_granulares.items():
        disciplina_id, tema = chave_criterio

        for formato, dificuldades in formatos.items():
            for dificuldade, quantidade in dificuldades.items():
                if quantidade > 0:
                    criterios.append({
                        'tema': tema, 
                        'disciplina_id': disciplina_id,
                        'formato': formato, 
                        'dificuldade': dificuldade, 
                        'quantidade': quantidade
                    })
    # --- FIM DA CORREÇÃO ---
    
    for criterio in criterios:
        tema = criterio['tema']
        disciplina_id = criterio['disciplina_id']
        formato = criterio['formato']
        dificuldade = criterio['dificuldade']
        quantidade_necessaria = criterio['quantidade'] * num_versoes 
        
        conditions = ["formato_questao = ?", "dificuldade = ?", "ativa = 1"]
        params = [formato, dificuldade]

        if tema != "Todos":
            conditions.append("tema = ?")
            params.append(tema)
        
        if disciplina_id is not None:
            conditions.append("disciplina_id = ?")
            params.append(disciplina_id)
            
        query = "SELECT * FROM questoes WHERE " + " AND ".join(conditions) + " ORDER BY RANDOM() LIMIT ?"
        params.append(quantidade_necessaria)
            
        cursor = conn.cursor()
        cursor.execute(query, params)
        questoes_encontradas = [dict(row) for row in cursor.fetchall()]
        
        if len(questoes_encontradas) < quantidade_necessaria:
            nome_disciplina_aviso = obter_disciplina_nome_por_id(disciplina_id) or "Geral"
            avisos.append(f"AVISO: Apenas {len(questoes_encontradas)} de {quantidade_necessaria} questões encontradas para [{nome_disciplina_aviso} / {tema} / {formato} / {dificuldade}].")
        
        questoes_base.extend(questoes_encontradas)
            
    conn.close()
    return questoes_base, avisos

def buscar_questoes_por_ids(lista_ids):
    """Busca questões específicas por uma lista de IDs."""
    if not lista_ids:
        return []
    
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    placeholders = ', '.join('?' for _ in lista_ids)
    query = f"SELECT * FROM questoes WHERE id IN ({placeholders}) AND ativa = 1"
    
    cursor.execute(query, lista_ids)
    questoes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return questoes


# ----------------------------------------------------
# FUNÇÕES DE IMPORTAÇÃO/EXPORTAÇÃO (AJUSTADAS)
# ----------------------------------------------------

def exportar_base_de_dados(caminho_destino):
    """Cria um arquivo ZIP contendo o DB e a pasta de imagens_questoes."""
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)
        
    try:
        with zipfile.ZipFile(caminho_destino, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(DB_NAME, os.path.basename(DB_NAME))
            
            for root, _, files in os.walk(IMAGE_DIR):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.join(os.path.basename(IMAGE_DIR), file))
        return True
    except Exception as e:
        print(f"Erro ao exportar dados: {e}")
        return False

def importar_base_de_dados(caminho_origem):
    """
    Descompacta o backup e insere as questões e imagens no DB atual como novos IDs.
    """
    caminho_temp = 'temp_import_data'
    temp_db_path = os.path.join(caminho_temp, os.path.basename(DB_NAME))
    temp_img_dir = os.path.join(caminho_temp, os.path.basename(IMAGE_DIR))

    if os.path.exists(caminho_temp):
        shutil.rmtree(caminho_temp)
    os.makedirs(caminho_temp)

    try:
        with zipfile.ZipFile(caminho_origem, 'r') as zipf:
            zipf.extractall(caminho_temp)
    except Exception as e:
        shutil.rmtree(caminho_temp)
        return False, f"Erro ao descompactar o arquivo: {e}"

    conn_atual = None
    conn_temp = None
    try:
        conn_atual = sqlite3.connect(DB_NAME)
        cursor_atual = conn_atual.cursor()
        
        conn_temp = sqlite3.connect(temp_db_path)
        cursor_temp = conn_temp.cursor()
        
        # 1. Copia Disciplinas (para garantir que IDs de FKs existam)
        cursor_temp.execute("SELECT nome FROM disciplinas")
        disciplinas_importar = cursor_temp.fetchall()
        for row in disciplinas_importar:
            salvar_disciplina(row[0]) # Usa a função que insere ou retorna o ID se já existir
        
        # 2. Insere as Questões
        # Obter a lista de colunas dinamicamente (para incluir as novas: disciplina_id, fonte, tipo_resposta)
        cursor_temp.execute("PRAGMA table_info(questoes)")
        colunas_temp = [info[1] for info in cursor_temp.fetchall()]
        colunas_sem_id = [col for col in colunas_temp if col != 'id']
        
        cursor_temp.execute(f"SELECT {', '.join(colunas_sem_id)} FROM questoes")
        questoes_importar = cursor_temp.fetchall()
        
        questoes_adicionadas = 0
        
        # Encontra os índices das colunas de interesse
        try:
            indice_imagem = colunas_sem_id.index('imagem')
            indice_disciplina_id = colunas_sem_id.index('disciplina_id')
        except ValueError:
            # Colunas novas podem não existir em DBs antigos, mas o código deve tratar
            indice_imagem = -1
            indice_disciplina_id = -1


        # Mapeamento do ID antigo para o novo (útil para questões que referenciam outras, se houver)
        id_map = {} 
        
        for idx, questao in enumerate(questoes_importar):
            dados_questao = list(questao)
            
            # --- Ajuste D1: Mapear Disciplina ---
            if indice_disciplina_id != -1 and dados_questao[indice_disciplina_id] is not None:
                # Busca o nome da disciplina no DB temporário
                cursor_temp.execute("SELECT nome FROM disciplinas WHERE id = ?", (dados_questao[indice_disciplina_id],))
                nome_disciplina_temp = cursor_temp.fetchone()
                if nome_disciplina_temp:
                    # Busca ou cria o novo ID no DB atual
                    novo_disciplina_id = obter_disciplina_id_por_nome(nome_disciplina_temp[0])
                    dados_questao[indice_disciplina_id] = novo_disciplina_id
            
            # --- Ajuste de Imagem ---
            if indice_imagem != -1:
                caminho_imagem_antigo = dados_questao[indice_imagem] 
                
                if caminho_imagem_antigo and caminho_imagem_antigo not in ("NULL", ""):
                    nome_arquivo = os.path.basename(caminho_imagem_antigo)
                    caminho_origem_img = os.path.join(temp_img_dir, nome_arquivo)
                    caminho_destino_img = os.path.join(IMAGE_DIR, nome_arquivo)
                    
                    if os.path.exists(caminho_origem_img):
                         if not os.path.exists(IMAGE_DIR): os.makedirs(IMAGE_DIR)
                         
                         shutil.copy2(caminho_origem_img, caminho_destino_img)
                         caminho_imagem_novo = os.path.join(os.path.basename(IMAGE_DIR), nome_arquivo)
                         dados_questao[indice_imagem] = caminho_imagem_novo
                # Se não tem imagem, garante que seja NULL (o valor padrão do DB)
                elif dados_questao[indice_imagem] in ("NULL", ""):
                     dados_questao[indice_imagem] = None 


            # Insere a nova questão (usando NULL para o ID para que o DB gere um novo)
            colunas_insercao = ', '.join(colunas_sem_id)
            placeholders = ', '.join(['?'] * len(dados_questao))
            
            # A inserção é feita com os nomes das colunas e os valores
            query_insert = f"INSERT INTO questoes ({colunas_insercao}) VALUES ({placeholders})"
            cursor_atual.execute(query_insert, tuple(dados_questao))
            
            questoes_adicionadas += 1

        conn_atual.commit()
        
        return True, f"{questoes_adicionadas} novas questões importadas com sucesso."

    except Exception as e:
        if conn_atual: conn_atual.rollback()
        return False, f"Erro na mesclagem SQL. O banco de dados de destino pode ter sido corrompido: {e}"
        
    finally:
        if conn_atual: conn_atual.close()
        if conn_temp: conn_temp.close()
        if os.path.exists(caminho_temp):
            shutil.rmtree(caminho_temp)

    # Adicione estas funções ao seu database.py

def salvar_configuracoes(dados):
    """Salva um dicionário de configurações no arquivo settings.json."""
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        settings = {}
    
    # Atualiza a chave 'identificacao' com os novos dados
    settings['identificacao'] = dados
    
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4)

def carregar_configuracoes():
    """Carrega as configurações de identificação do arquivo settings.json."""
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            return settings.get('identificacao', {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}