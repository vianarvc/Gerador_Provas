# migracao.py

import sqlite3

# Nomes dos arquivos de banco de dados
DB_ANTIGO = 'banco_antigo.db'
DB_NOVO = 'banco_questoes.db'

def migrar_dados():
    """
    Script para migrar dados de um banco de dados antigo (com 'disciplina' como TEXT)
    para um novo (com tabela 'disciplinas' e 'disciplina_id' como FOREIGN KEY).
    """
    try:
        # Conecta aos dois bancos de dados
        conn_antigo = sqlite3.connect(DB_ANTIGO)
        conn_antigo.row_factory = sqlite3.Row
        cursor_antigo = conn_antigo.cursor()

        conn_novo = sqlite3.connect(DB_NOVO)
        cursor_novo = conn_novo.cursor()

        print("Iniciando a migração...")

        # --- ETAPA 1: Migrar as Disciplinas ---
        print("1. Lendo disciplinas do banco antigo...")
        cursor_antigo.execute("SELECT DISTINCT disciplina FROM questoes WHERE disciplina IS NOT NULL AND disciplina != ''")
        disciplinas_unicas = [row['disciplina'] for row in cursor_antigo.fetchall()]
        
        # Insere as disciplinas na nova tabela e guarda seus IDs
        mapa_disciplina_id = {}
        print(f"   Encontradas {len(disciplinas_unicas)} disciplinas únicas. Inserindo no novo banco...")
        for nome_disciplina in disciplinas_unicas:
            try:
                cursor_novo.execute("INSERT INTO disciplinas (nome) VALUES (?)", (nome_disciplina,))
                mapa_disciplina_id[nome_disciplina] = cursor_novo.lastrowid
            except sqlite3.IntegrityError:
                # Se a disciplina já existe, busca o ID dela
                cursor_novo.execute("SELECT id FROM disciplinas WHERE nome = ?", (nome_disciplina,))
                mapa_disciplina_id[nome_disciplina] = cursor_novo.fetchone()[0]
        
        conn_novo.commit()
        print("   Disciplinas migradas com sucesso.")

        # --- ETAPA 2: Migrar as Questões ---
        print("\n2. Lendo questões do banco antigo...")
        # Pega todas as colunas, exceto 'id' e a antiga 'disciplina' de texto
        cursor_antigo.execute("PRAGMA table_info(questoes)")
        colunas_antigas = [info[1] for info in cursor_antigo.fetchall()]
        
        # Filtra colunas que não existem mais ou foram substituídas
        colunas_para_copiar = [col for col in colunas_antigas if col not in ('id', 'disciplina')]
        
        # Adiciona a nova coluna de ID no final
        colunas_novas = colunas_para_copiar + ['disciplina_id']
        
        # Monta a query
        colunas_str_select = ', '.join(colunas_para_copiar)
        cursor_antigo.execute(f"SELECT id, disciplina, {colunas_str_select} FROM questoes")
        questoes_antigas = cursor_antigo.fetchall()
        
        print(f"   Encontradas {len(questoes_antigas)} questões. Inserindo no novo banco...")
        
        questoes_migradas = 0
        for questao in questoes_antigas:
            dados_para_inserir = dict(questao)
            
            # Pega o nome da disciplina da questão antiga
            nome_disciplina_antiga = dados_para_inserir.pop('disciplina', None)
            
            # Pega o ID da questão antiga (não será usado na inserção)
            dados_para_inserir.pop('id', None)

            # Busca o novo ID correspondente
            novo_id_disciplina = mapa_disciplina_id.get(nome_disciplina_antiga)
            
            # Adiciona o novo ID aos dados
            dados_para_inserir['disciplina_id'] = novo_id_disciplina
            
            # Garante que a ordem das colunas e valores está correta
            nomes_colunas = ', '.join(dados_para_inserir.keys())
            placeholders = ', '.join('?' * len(dados_para_inserir))
            valores = list(dados_para_inserir.values())
            
            cursor_novo.execute(f"INSERT INTO questoes ({nomes_colunas}) VALUES ({placeholders})", valores)
            questoes_migradas += 1

        conn_novo.commit()
        print(f"   {questoes_migradas} questões migradas com sucesso.")
        
        print("\n--- MIGRAÇÃO CONCLUÍDA! ---")

    except sqlite3.Error as e:
        print(f"\n--- ERRO DURANTE A MIGRAÇÃO ---")
        print(f"Ocorreu um erro: {e}")
        if conn_novo:
            conn_novo.rollback()
    finally:
        if conn_antigo:
            conn_antigo.close()
        if conn_novo:
            conn_novo.close()

if __name__ == '__main__':
    migrar_dados()