# database.py

import sqlite3
import json
import zipfile
import os
import shutil
import uuid  
from datetime import datetime

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
    check_and_add_column('parametros_tabela_json', 'TEXT') 
    check_and_add_column('grupo_importacao', 'TEXT')

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
def salvar_ordem_temas(lista_de_temas, disciplina_id):
    """Salva a ordem customizada dos temas para uma disciplina específica."""
    if not disciplina_id: return # Não salva ordem para "Todas as Disciplinas"

    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        settings = {}
    
    if 'ordem_temas_por_disciplina' not in settings:
        settings['ordem_temas_por_disciplina'] = {}

    # Usa o ID da disciplina como chave (convertido para string)
    settings['ordem_temas_por_disciplina'][str(disciplina_id)] = lista_de_temas
    
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4)

def obter_temas(disciplina_id=None):
    """Retorna uma lista de temas, respeitando a ordem salva para a disciplina, filtrada por disciplina."""
    ordem_salva = []
    if disciplina_id:
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # Carrega a ordem específica da disciplina
                ordem_salva = settings.get('ordem_temas_por_disciplina', {}).get(str(disciplina_id), [])
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

    # A lógica de ordenação agora usa a ordem específica da disciplina
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
    questao_id = cursor.lastrowid  # ← CAPTURA O ID
    conn.commit()
    conn.close()
    return questao_id

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
        quantidade_necessaria = criterio['quantidade']
        
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
    Descompacta o backup e mescla as questões e imagens no DB atual,
    evitando duplicatas e conflitos de imagem.
    """
    # ... (código de descompactação inicial, sem alterações) ...
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
        
        # Cria uma tag de importação única para esta operação
        import_tag = f"Importado em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        # 1. Copia Disciplinas (sua lógica original, que está correta)
        cursor_temp.execute("SELECT nome FROM disciplinas")
        for row in cursor_temp.fetchall():
            # A função salvar_disciplina/obter_disciplina_id_por_nome já lida com duplicatas
            obter_disciplina_id_por_nome(row[0], criar_se_nao_existir=True)

        # 2. Prepara a inserção de Questões de forma segura
        
        # Pega as colunas do DB de backup
        cursor_temp.execute("PRAGMA table_info(questoes)")
        colunas_temp = {info[1]: i for i, info in enumerate(cursor_temp.fetchall())}
        
        # Pega as colunas do DB atual
        cursor_atual.execute("PRAGMA table_info(questoes)")
        colunas_atuais = {info[1] for info in cursor_atual.fetchall()}
        
        # Interseção: usa apenas colunas que existem em AMBOS os bancos
        colunas_comuns = [col for col in colunas_temp if col in colunas_atuais and col != 'id']

        # Garante que a nova coluna de tag esteja presente
        if 'grupo_importacao' not in colunas_comuns and 'grupo_importacao' in colunas_atuais:
            colunas_comuns.append('grupo_importacao')

        cursor_temp.execute(f"SELECT * FROM questoes")
        questoes_importar = cursor_temp.fetchall()
        
        questoes_adicionadas = 0
        questoes_ignoradas = 0
        
        for questao_row in questoes_importar:
            dados_questao = {col: questao_row[idx] for col, idx in colunas_temp.items()}

            # --- VERIFICAÇÃO DE DUPLICATAS ---
            enunciado = dados_questao.get('enunciado', '')
            cursor_atual.execute("SELECT id FROM questoes WHERE enunciado = ?", (enunciado,))
            if cursor_atual.fetchone():
                questoes_ignoradas += 1
                continue # Pula para a próxima questão se já existir

            # --- CORREÇÃO DE CONFLITO DE IMAGEM ---
            if 'imagem' in dados_questao and dados_questao['imagem']:
                caminho_imagem_antigo = dados_questao['imagem']
                nome_arquivo_antigo = os.path.basename(caminho_imagem_antigo)
                extensao = os.path.splitext(nome_arquivo_antigo)[1]
                
                # Gera um novo nome de arquivo único
                novo_nome_arquivo = f"{uuid.uuid4()}{extensao}"
                
                caminho_origem_img = os.path.join(temp_img_dir, nome_arquivo_antigo)
                caminho_destino_img = os.path.join(IMAGE_DIR, novo_nome_arquivo)
                
                if os.path.exists(caminho_origem_img):
                    if not os.path.exists(IMAGE_DIR): os.makedirs(IMAGE_DIR)
                    shutil.copy2(caminho_origem_img, caminho_destino_img)
                    # Atualiza o caminho da imagem para o novo nome
                    dados_questao['imagem'] = os.path.join(os.path.basename(IMAGE_DIR), novo_nome_arquivo).replace('\\', '/')
            
            # Mapeia o ID da disciplina (sua lógica original adaptada)
            if 'disciplina_id' in dados_questao and dados_questao['disciplina_id']:
                cursor_temp.execute("SELECT nome FROM disciplinas WHERE id = ?", (dados_questao['disciplina_id'],))
                nome_disciplina = cursor_temp.fetchone()[0]
                dados_questao['disciplina_id'] = obter_disciplina_id_por_nome(nome_disciplina)

            # --- ADICIONA A TAG DE IMPORTAÇÃO ---
            dados_questao['grupo_importacao'] = import_tag

            # Monta a query de inserção apenas com as colunas comuns
            colunas_para_inserir = [col for col in colunas_comuns if col in dados_questao]
            valores_para_inserir = [dados_questao[col] for col in colunas_para_inserir]
            
            placeholders = ', '.join(['?'] * len(colunas_para_inserir))
            query_insert = f"INSERT INTO questoes ({', '.join(colunas_para_inserir)}) VALUES ({placeholders})"
            
            cursor_atual.execute(query_insert, tuple(valores_para_inserir))
            questoes_adicionadas += 1

        conn_atual.commit()
        
        mensagem_final = f"{questoes_adicionadas} novas questões importadas com sucesso."
        if questoes_ignoradas > 0:
            mensagem_final += f" {questoes_ignoradas} questões foram ignoradas por já existirem."
            
        return True, mensagem_final

    except Exception as e:
        if conn_atual: conn_atual.rollback()
        return False, f"Erro durante a mesclagem dos dados: {e}"
        
    finally:
        if conn_atual: conn_atual.close()
        if conn_temp: conn_temp.close()
        if os.path.exists(caminho_temp):
            shutil.rmtree(caminho_temp)


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
    
def obter_todas_questoes_para_cardapio(disciplina_id=None, tema=None):
    """
    Busca TODAS as questões (ativas e inativas), com filtros opcionais
    de disciplina e tema, e ordena usando a ordem customizada de temas.
    """
    
    # 1. Obter a ordem customizada dos temas
    # Reutilizamos a lógica de obter_temas, mas queremos a lista ordenada, sem o 'Todos'
    temas_ordenados = obter_temas(disciplina_id=disciplina_id)
    if temas_ordenados and temas_ordenados[0] == "Todos":
        temas_ordenados = temas_ordenados[1:]
    
    # Cria um dicionário para mapear tema para sua posição customizada (ex: {'Tema A': 0, 'Tema B': 1})
    tema_para_posicao = {t: i for i, t in enumerate(temas_ordenados)}

    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    conditions = []
    params = []

    if disciplina_id:
        conditions.append("disciplina_id = ?")
        params.append(disciplina_id)
    
    if tema and tema != "Todos":
        conditions.append("tema = ?")
        params.append(tema)

    query = "SELECT * FROM questoes"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    # 2. ALtera a Query SQL: Ordena apenas por disciplina e ID (a ordenação por tema será em Python)
    query += " ORDER BY disciplina_id, id" 
    
    cursor.execute(query, params)
    questoes = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # 3. Ordenação Final em Python usando a ordem customizada
    # A ordenação será: 
    # 1º Disciplina (o SQL já cuidou disso, mas é bom manter)
    # 2º Posição do Tema (Customizada)
    # 3º ID (para ordem estável)
    
    def key_sort(questao):
        # A posição do tema é obtida do dicionário tema_para_posicao.
        # Usamos float('inf') para temas que não estão na lista salva, colocando-os no final.
        posicao_tema = tema_para_posicao.get(questao['tema'], float('inf'))
        return (questao['disciplina_id'], posicao_tema, questao['id'])

    questoes_ordenadas = sorted(questoes, key=key_sort)
    
    return questoes_ordenadas

def renomear_tema(nome_antigo, nome_novo):
    """
    Renomeia um tema em todas as questões onde ele aparece.
    
    Args:
        nome_antigo (str): O nome atual do tema a ser substituído.
        nome_novo (str): O novo nome para o tema.
        
    Returns:
        bool: True se a operação foi bem-sucedida, False caso contrário.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # A query é um simples UPDATE que busca pelo nome antigo do tema
        cursor.execute("UPDATE questoes SET tema = ? WHERE tema = ?", (nome_novo, nome_antigo))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Erro ao renomear tema no banco de dados: {e}")
        return False
    finally:
        if conn:
            conn.close()

def obter_grupos_por_tema(disciplina_id, tema):
    """
    Busca no banco de dados todos os nomes de grupos únicos
    associados a uma disciplina e um tema específicos.
    """
    if not disciplina_id or not tema:
        return []
        
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT DISTINCT grupo FROM questoes 
            WHERE disciplina_id = ? AND tema = ? AND grupo IS NOT NULL AND grupo != ''
            ORDER BY grupo
        """, (disciplina_id, tema))
        grupos = [row[0] for row in cursor.fetchall()]
        return grupos
    except sqlite3.Error as e:
        print(f"Erro ao buscar grupos por tema: {e}")
        return []
    finally:
        conn.close()

def verificar_configuracoes_essenciais():
    """
    Verifica se os campos essenciais para a geração de PDF estão preenchidos.
    Retorna True se tudo estiver OK, False caso contrário.
    """
    config = carregar_configuracoes()
    
    # Defina aqui quais chaves são OBRIGATÓRIAS no seu template LaTeX
    campos_obrigatorios = [
        "nome_professor",
        "nome_escola",
        "sigla_curso",
        "nome_curso"
    ]
    
    for campo in campos_obrigatorios:
        # Verifica se o campo não existe, ou se existe mas está vazio ou só com espaços
        if not config.get(campo, "").strip():
            return False # Encontrou um campo essencial faltando
            
    return True # Todos os campos essenciais estão preenchidos

def atualizar_imagem_questao(questao_id, caminho_imagem):
    """
    Atualiza apenas o campo imagem de uma questão específica
    """
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE questoes SET imagem = ? WHERE id = ?", (caminho_imagem, questao_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao atualizar imagem da questão {questao_id}: {e}")
        return False
    finally:
        conn.close()

def obter_questoes_do_grupo(grupo, disciplina_id=None):
    """
    Busca todas as questões ATIVAS de um grupo específico
    """
    if not grupo:
        return []
        
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    conditions = ["grupo = ?", "ativa = 1"]
    params = [grupo]
    
    if disciplina_id is not None:
        conditions.append("disciplina_id = ?")
        params.append(disciplina_id)
        
    query = "SELECT * FROM questoes WHERE " + " AND ".join(conditions) + " ORDER BY id"
    cursor.execute(query, params)
    questoes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return questoes