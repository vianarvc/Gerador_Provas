# motor_gerador.py 20h54 04/10/25

import random, math, json, traceback, re
from collections import Counter, defaultdict
from itertools import groupby

try:
    import numpy as np
except ImportError:
    np = None
try:
    import cmath
except ImportError:
    cmath = None
try:
    import sympy as sp
except ImportError:
    sp = None

def _get_math_context():
    """Cria o dicionário de contexto com as bibliotecas disponíveis."""
    context = {
        'random': random,
        'math': math,
    }
    if np: context['np'] = np
    if cmath: context['cmath'] = cmath
    if sp: context['sp'] = sp
    return context

# Substitua a função inteira por esta:

def formatar_unidade(valor, unidade="", incluir_unidade=True):
    """
    Formata um número usando notação de engenharia (prefixos k, M, m, µ, etc.).
    - unidade: A unidade base (ex: 'A', 'V', 'Ω').
    - incluir_unidade: Se False, retorna apenas o número com prefixo e um espaço (ex: "5 m ").
    """
    if not isinstance(valor, (int, float)):
        return str(valor)

    # Usa uma pequena tolerância para tratar números de ponto flutuante quase nulos como zero.
    if abs(valor) < 1e-9:
        if incluir_unidade and unidade:
            return f"0 {unidade}"
        return "0"

    prefixos = [(1e12, 'T'), (1e9, 'G'), (1e6, 'M'), (1e3, 'k'), (1, ''),
                (1e-3, 'm'), (1e-6, 'µ'), (1e-9, 'n'), (1e-12, 'p')]

    for mult, prefixo in prefixos:
        if abs(valor) >= mult:
            v_ajustado = valor / mult
            
            # Lógica final para formatar inteiros corretamente
            if round(v_ajustado, 2) == int(round(v_ajustado, 2)):
                valor_str = str(int(round(v_ajustado, 2)))
            else:
                valor_str = f'{v_ajustado:.2f}'.replace('.', ',')
            
            if incluir_unidade:
                return f"{valor_str} {prefixo}{unidade}".strip()
            else:
                # Lógica corrigida:
                if prefixo:
                    return f"{valor_str} {prefixo}" # Retorna "19 m" (sem espaço no final)
                else:
                    return f"{valor_str} " # Retorna "10 " (com espaço no final)

    # Fallback para números muito pequenos
    valor_str = f'{valor:.2f}'.replace('.', ',')
    if incluir_unidade:
        return f"{valor_str} {unidade}".strip()
    else:
        return f"{valor_str} "

def _executar_logica_tabela(params_json, contexto):
    params = json.loads(params_json)
    for var in params.get("variaveis", []):
        nome, tipo, vals = var.get("nome"), var.get("tipo"), var.get("valores")
        if not all([nome, tipo, vals]): continue
        if tipo == "Intervalo Inteiro": min_v, max_v = map(int, [v.strip() for v in vals.split('-')]); contexto[nome] = random.randint(min_v, max_v)
        elif tipo == "Intervalo Decimal": min_v, max_v = map(float, [v.strip() for v in vals.split('-')]); contexto[nome] = random.uniform(min_v, max_v)
        elif tipo == "Lista de Valores":
            lista = [v.strip() for v in vals.split(',')];
            try: lista = [float(v) if '.' in v else int(v) for v in lista]
            except ValueError: pass
            contexto[nome] = random.choice(lista)
    formula = params.get("formula_resposta", "")
    if formula: contexto['resposta_valor'] = eval(formula, {"__builtins__": None}, contexto)

def _calcular_apenas_resposta(questao_base, seed):
    random.seed(seed)
    try:
        contexto = _get_math_context()
        if questao_base.get("parametros"):
            params = questao_base.get("parametros", "")
            if questao_base.get("tipo_questao", "Código (Python)") == "Código (Python)":
                exec(params, contexto)
            else:
                _executar_logica_tabela(params, contexto)
        return contexto.get('resposta_valor') or contexto.get('resposta')
    except Exception:
        return None

def _gerar_pool_combinatorio(questao_base, params_code, base_context):
    """
    Analisa o código Python, extrai variáveis de random.choice,
    e executa todas as combinações para gerar um pool determinístico de resultados.
    (Versão 3.0 - Robusta, reconstrói o script para cada combinação)
    """
    import ast
    import itertools
    import random

    # Garante que o 'random' está no contexto, não importa como ele foi chamado
    if 'random' not in base_context:
        base_context['random'] = random # <-- 2. ADICIONE ESTA LINHA

    q_id = questao_base.get('id', 'N/A')
    #print(f"\n--- Análise Combinatória para Questão ID: {q_id} ---")

    try:
        tree = ast.parse(params_code)
        
        choice_assignments = []
        other_nodes = []
        
        # 1. Separa as linhas de `... = random.choice(...)` do resto do código.
        for node in tree.body:
            if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and
                    isinstance(node.value.func, ast.Attribute) and isinstance(node.value.func.value, ast.Name) and
                    node.value.func.value.id == 'random' and node.value.func.attr == 'choice'):
                choice_assignments.append(node)
            else:
                other_nodes.append(node)

        if not choice_assignments:
            print("  - AVISO: Não é uma questão do tipo combinatório (sem random.choice). Análise ignorada.")
            print(f"--- Fim da Análise para Questão ID: {q_id} ---")
            return None

        # 2. Extrai as listas de valores de forma segura
        # Executa o código uma vez para que as listas (ex: minha_lista) sejam definidas
        temp_context = base_context.copy()
        exec(params_code, temp_context)
        choice_vars = {}
        for assign_node in choice_assignments:
            var_name = assign_node.targets[0].id
            arg_as_string = ast.unparse(assign_node.value.args[0])
            values = eval(arg_as_string, temp_context)
            choice_vars[var_name] = values
        
        # 3. Pega o código de cálculo (tudo que não é random.choice)
        calculation_tree = ast.Module(body=other_nodes, type_ignores=[])
        calculation_source = ast.unparse(calculation_tree)
        #print(f"  - Fórmulas de Cálculo Extraídas:\n---\n{calculation_source.strip()}\n---")
        
        # 4. Gera todas as combinações
        var_names = list(choice_vars.keys())
        value_lists = list(choice_vars.values())
        all_combinations = list(itertools.product(*value_lists))
        #print(f"  - Variáveis e Valores: {choice_vars}")
        #print(f"  - Total de Combinações a testar: {len(all_combinations)}")

        possible_outcomes = set()

        # 5. Loop, monta o "mini-script" para cada combinação e executa
        for combination in all_combinations:
            # ... (código que monta o script e o contexto)
            assignment_script = ""
            current_combination_dict = dict(zip(var_names, combination))
            for var_name, value in current_combination_dict.items():
                assignment_script += f"{var_name} = {repr(value)}\n"

            full_script_for_run = assignment_script + calculation_source
            
            exec_context = base_context.copy()
            exec(full_script_for_run, exec_context)
            
            result = exec_context.get('resposta_valor') or exec_context.get('resposta')

            # --- FILTRO ANTI-ZERO ADICIONADO ---
            is_zero_present = False
            if isinstance(result, dict) and 'valores' in result:
                # Para MODO 1, verifica se algum dos valores no dicionário é zero
                for v in result['valores'].values():
                    if isinstance(v, (int, float)) and abs(v) < 1e-9: # 1e-9 é uma tolerância para zero em ponto flutuante
                        is_zero_present = True
                        break
            elif isinstance(result, (int, float)):
                # Para MODO 2, verifica se o próprio valor é zero
                if abs(result) < 1e-9:
                    is_zero_present = True
            
            # Só adiciona ao pool se não houver zero na resposta
            if not is_zero_present:
                if isinstance(result, dict) and 'valores' in result:
                    vals_dict = result['valores']
                    hashable_result = tuple(sorted(vals_dict.items()))
                    possible_outcomes.add(hashable_result)
                elif isinstance(result, (int, float)):
                    possible_outcomes.add(result)
        
        #print(f"  - Pool de Resultados Únicos Encontrados: {possible_outcomes}")
        #print(f"--- Fim da Análise para Questão ID: {q_id} ---")

        return possible_outcomes

    except Exception as e:
        print(f"ERRO CRÍTICO no motor combinatório ao analisar a questão ID {q_id}: {e}")
        import traceback
        traceback.print_exc()
        return None

def _gerar_variante_questao(questao_base, seed):
    is_multi_valor = False
    try:
        random.seed(seed)
        
        formato_questao = questao_base.get("formato_questao", "Múltipla Escolha")
        num_alternativas = questao_base.get("num_alternativas", 5)
        unidade = questao_base.get("unidade_resposta", "")
        permitir_negativos = questao_base.get("permitir_negativos", False)

        contexto = _get_math_context()
        contexto['avisos'] = []
        
        if questao_base.get("parametros"):
            params = questao_base.get("parametros", "")

            if questao_base.get("tipo_questao", "Código (Python)") == "Código (Python)":
                try:
                    exec(params, contexto)
                except Exception as e:
                    id_questao = questao_base.get('id', 'N/A')
                    aviso = f"AVISO: Erro no código da questão ID {id_questao}: '{e}'. A questão não será gerada."
                    print(aviso)
                    return None
            else:
                _executar_logica_tabela(params, contexto)
        
        resposta_valor_calculado = contexto.get('resposta_valor') or contexto.get('resposta')
        
        for key in ['random', 'math', 'np', 'cmath', 'sp', '__builtins__']:
            if key in contexto: del contexto[key]

        enunciado_template = questao_base.get("enunciado", "")
        contexto_formatado = contexto.copy()

        import re
        prefix_divisors = { 'T': 1e12, 'G': 1e9, 'M': 1e6, 'k': 1e3, 'K': 1e3, 'c': 1e-2, 'm': 1e-3, 'u': 1e-6, 'µ': 1e-6, 'n': 1e-9, 'p': 1e-12 }
        placeholders = re.findall(r'\{(\w+)\}(?:\s*)((?:T|G|M|k|K|c|m|u|µ|n|p)\w{0,2})\b', enunciado_template)
        for var_name, unit_with_prefix in placeholders:
            if var_name in contexto_formatado and isinstance(contexto_formatado[var_name], (int, float)):
                prefix = unit_with_prefix[0]
                if prefix in prefix_divisors:
                    original_value = float(contexto_formatado[var_name])
                    divisor = prefix_divisors[prefix]
                    converted_value = original_value / divisor
                    contexto_formatado[var_name] = int(converted_value) if converted_value == int(converted_value) else converted_value

        # --- INÍCIO DA CORREÇÃO DE ARREDONDAMENTO ---
        # Adicione este bloco para arredondar todos os floats antes de formatar o enunciado.
        for key, value in contexto_formatado.items():
            if isinstance(value, float):
                # Arredonda para 2 casas decimais para uma exibição limpa.
                rounded_value = round(value, 2)
                # Se o número arredondado for um inteiro (ex: 50.0), converte para inteiro.
                if rounded_value == int(rounded_value):
                    contexto_formatado[key] = int(rounded_value)
                else:
                    contexto_formatado[key] = rounded_value
        # --- FIM DA CORREÇÃO DE ARREDONDAMENTO ---

        enunciado_final = enunciado_template.format(**contexto_formatado)
        enunciado_final = re.sub(r'(\d+)\.(\d+)', r'\1,\2', enunciado_final)
        
        alternativas_valores = []
        resposta_valor = None

        if formato_questao == "Múltipla Escolha":
            if questao_base.get("gerar_alternativas_auto"):
                # --- MODO 1 - RESPOSTAS MÚLTIPLAS ---
                if isinstance(resposta_valor_calculado, dict) and "valores" in resposta_valor_calculado and "formato_texto" in resposta_valor_calculado:                   
                    is_multi_valor = True
                    
                    pool_de_tuplas = _gerar_pool_combinatorio(questao_base, params, contexto)

                    if not pool_de_tuplas:
                        print(f"AVISO: A questão ID {questao_base.get('id', 'N/A')} não gerou resultados combinatórios. Questão descartada.")
                        return None

                    pools_por_variavel = {chave: set() for chave in resposta_valor_calculado["valores"].keys()}
                    for resultado_tupla in pool_de_tuplas:
                        for chave, valor in resultado_tupla:
                            if chave in pools_por_variavel:
                                pools_por_variavel[chave].add(valor)

                    pools_filtrados = {}
                    for chave, valores_set in pools_por_variavel.items():
                        valores_filtrados = {v for v in valores_set if abs(v) > 1e-9}
                        if not permitir_negativos:
                            valores_filtrados = {v for v in valores_filtrados if v >= 0}
                        
                        if not valores_filtrados:
                            print(f"FALHA: A variável '{chave}' da ID {questao_base.get('id', 'N/A')} não teve valores válidos. Questão descartada.")
                            return None
                            
                        pools_filtrados[chave] = list(valores_filtrados)

                    def formatar_dict_inteligentemente(valores_dict, formato_template, unidade_base):
                        valores_formatados = {}
                        for chave, valor_num in valores_dict.items():
                            valores_formatados[chave] = formatar_unidade(valor_num, unidade_base, incluir_unidade=False)
                        return formato_template.format(**valores_formatados).replace('.', ',')

                    formato_texto = resposta_valor_calculado.get("formato_texto", "")
                    resposta_correta_dict_numerico = resposta_valor_calculado["valores"]
                    
                    if not permitir_negativos and any(v < 0 for v in resposta_correta_dict_numerico.values() if isinstance(v, (int, float))):
                        print(f"FALHA: Resposta correta da ID {questao_base.get('id', 'N/A')} contém negativo. Descartada.")
                        return None
                    if any(abs(v) < 1e-9 for v in resposta_correta_dict_numerico.values() if isinstance(v, (int, float))):
                        print(f"FALHA: Resposta correta da ID {questao_base.get('id', 'N/A')} contém zero. Descartada.")
                        return None
                    
                    resposta_valor = formatar_dict_inteligentemente(resposta_correta_dict_numerico, formato_texto, unidade)
                    alternativas_valores = [resposta_valor]

                    tentativas, limite_tentativas = 0, 500
                    while len(alternativas_valores) < num_alternativas:
                        if tentativas > limite_tentativas:
                            print(f"AVISO: ID {questao_base.get('id', 'N/A')}: Limite de tentativas atingido. Questão descartada.")
                            return None
                        
                        distrator_dict_numerico = {chave: random.choice(pool) for chave, pool in pools_filtrados.items()}
                        distrator_texto = formatar_dict_inteligentemente(distrator_dict_numerico, formato_texto, unidade)
                        
                        if distrator_texto not in alternativas_valores:
                            alternativas_valores.append(distrator_texto)
                        
                        tentativas += 1

                elif isinstance(resposta_valor_calculado, (int, float)):
                    # --- MODO 2 - RESPOSTA ÚNICA ---              
                    pool_numerico = _gerar_pool_combinatorio(questao_base, params, contexto)
                    
                    if pool_numerico is None:
                        print(f"AVISO: A questão ID {questao_base.get('id', 'N/A')} não é do tipo combinatório. Questão descartada.")
                        return None

                    pool_de_textos = set()
                    for valor_num in pool_numerico:
                        # --- FILTRO DE NEGATIVOS REINSERIDO AQUI ---
                        if not permitir_negativos and valor_num < 0:
                            continue # Pula este número se ele for negativo e a questão não permitir

                        # Sua função inteligente formata o número (escala e arredonda)
                        texto_formatado = formatar_unidade(valor_num, unidade)
                        
                        # Filtro anti-zero, que agora funciona corretamente
                        if texto_formatado.strip().startswith('0'):
                            continue

                        pool_de_textos.add(texto_formatado)
                    
                    #print(f"DEBUG (ID {questao_base.get('id', 'N/A')}): Pool de textos gerado: {pool_de_textos}")

                    # Valida se o pool final tem alternativas suficientes
                    if len(pool_de_textos) < num_alternativas:
                        print(f"FALHA: A questão ID {questao_base.get('id', 'N/A')} não gerou alternativas de texto válidas suficientes ({len(pool_de_textos)} encontradas). Questão descartada.")
                        return None

                    # Formata a RESPOSTA CORRETA e aplica os mesmos filtros
                    resposta_correta_num = resposta_valor_calculado
                    
                    if not permitir_negativos and resposta_correta_num < 0:
                        # Se a própria resposta correta for negativa e não for permitido, a questão é inválida.
                        print(f"FALHA: A resposta correta para a ID {questao_base.get('id', 'N/A')} é negativa, o que não é permitido. Questão descartada.")
                        return None

                    resposta_correta_texto = formatar_unidade(resposta_correta_num, unidade)

                    if resposta_correta_texto.strip().startswith('0'):
                        print(f"FALHA: A resposta correta para a ID {questao_base.get('id', 'N/A')} é zero, o que não é permitido. Questão descartada.")
                        return None
                    
                    # Garante que a resposta correta está no pool e seleciona os distratores
                    pool_de_textos.add(resposta_correta_texto)
                    if len(pool_de_textos) < num_alternativas:
                        # Adiciona uma salvaguarda para o caso de a resposta correta ser a única opção válida
                        print(f"FALHA: Pool de textos insuficiente para ID {questao_base.get('id', 'N/A')} mesmo após adicionar a resposta correta. Descartada.")
                        return None
                    
                    pool_sem_resposta = set(pool_de_textos)
                    pool_sem_resposta.discard(resposta_correta_texto)
                    
                    distratores = random.sample(list(pool_sem_resposta), num_alternativas - 1)
                    
                    # Monta a lista final
                    resposta_valor = resposta_correta_texto
                    alternativas_valores = [resposta_valor] + distratores
                
            else:
                # --- MODO 3: Alternativas Manuais (Lógica Moderna e Isolada) ---
                contexto_formatacao = {}
                # Se a questão tiver parâmetros, executa-os em um contexto temporário e seguro.
                if questao_base.get("parametros"):
                    params = questao_base.get("parametros", "")
                    temp_context = _get_math_context()
                    try:
                        exec(params, temp_context)
                        contexto_formatacao = temp_context
                    except Exception as e:
                        print(f"AVISO: Erro ao executar parâmetros para formatação do MODO 3 na ID {questao_base.get('id')}: {e}")
                
                # Garante que as listas estejam limpas antes de começar.
                alternativas_valores = []
                resposta_valor = None
                
                letras_base = ["a", "b", "c", "d", "e"]
                
                # Monta a lista de alternativas, formatando cada uma com o contexto seguro.
                for letra in letras_base[:num_alternativas]:
                    alt_base = questao_base.get(f"alternativa_{letra}")
                    if alt_base:
                        try:
                            alternativas_valores.append(alt_base.format(**contexto_formatacao))
                        except KeyError as e:
                            # Se uma variável não for encontrada, avisa e adiciona o texto sem formatar.
                            print(f"AVISO: Erro de formatação na alternativa '{letra}' da ID {questao_base.get('id')}: Variável {e} não encontrada.")
                            alternativas_valores.append(alt_base)
                
                # Define a resposta correta, também formatada com o contexto seguro.
                resposta_letra = questao_base.get("resposta_correta", "?").lower()
                alt_correta_texto = questao_base.get(f"alternativa_{resposta_letra}")
                
                if alt_correta_texto:
                    try:
                        resposta_valor = alt_correta_texto.format(**contexto_formatacao)
                    except KeyError as e:
                        print(f"AVISO: Erro de formatação na resposta correta ('{resposta_letra}') da ID {questao_base.get('id')}: Variável {e} não encontrada.")
                        resposta_valor = alt_correta_texto
                else:
                    # Se a letra da resposta correta for inválida, avisa e a resposta pode ficar como None.
                    print(f"AVISO: 'resposta_correta' ('{resposta_letra}') é inválida para a ID {questao_base.get('id')}. Verifique o cadastro.")
        
        elif formato_questao == "Verdadeiro ou Falso":
             # (código original)
            resposta_valor = resposta_valor_calculado
            if resposta_valor not in ["Verdadeiro", "Falso"] and resposta_valor is not None:
                resposta_valor = resposta_valor.format(**contexto)

    except KeyError as e:
        # (código de tratamento de erro)
        id_questao = questao_base.get('id', 'N/A')
        variavel_faltante = str(e).strip("'")
        aviso = f"AVISO: Erro de formatação na questão ID {id_questao}: A variável {{{variavel_faltante}}} está no enunciado mas não foi definida nos parâmetros."
        print(aviso)
        return None
    except Exception as e:
        # (código de tratamento de erro)
        id_questao = questao_base.get('id', 'N/A')
        aviso = f"AVISO: Erro inesperado ao gerar a questão ID {id_questao}: {e}"
        print(aviso)
        import traceback
        traceback.print_exc()
        return None

    imagem_path = questao_base.get("imagem", "")
    if imagem_path: imagem_path = imagem_path.replace('\\', '/')
    largura_imagem = questao_base.get("imagem_largura_percentual") or 50
    
    return { 
        "id_base": questao_base.get("id"), 
        "tema": questao_base.get("tema"), 
        "formato_questao": formato_questao, 
        "num_alternativas": num_alternativas, 
        "enunciado": enunciado_final, 
        "imagem": imagem_path, 
        "imagemLarguraPercentual": largura_imagem, 
        "resposta_valor": resposta_valor, 
        "alternativas_valores": alternativas_valores,
        "is_multi_valor": is_multi_valor }

def _gerar_gabarito_distribuido(num_questoes):
    letras = ["A", "B", "C", "D", "E"]; gabarito = []; contagem = Counter()
    for _ in range(num_questoes):
        letras_ordenadas = sorted(letras, key=lambda l: contagem[l]); letra_escolhida = letras_ordenadas[0]
        gabarito.append(letra_escolhida); contagem[letra_escolhida] += 1
    random.shuffle(gabarito); return gabarito

def _rotacionar_letra(letra, rotacao):
    letras = ["A", "B", "C", "D", "E"]
    if letra not in letras: return letra
    idx_original = letras.index(letra); idx_novo = (idx_original + rotacao) % len(letras); return letras[idx_novo]

def gerar_versoes_prova(questoes_base, num_versoes, opcoes_geracao):
    opcoes_gabarito = opcoes_geracao.get("gabarito", {})
    opcoes_pontuacao = opcoes_geracao.get("pontuacao", {})
    valor_por_questao = opcoes_pontuacao.get("valor_por_questao", 0.0)
    mostrar_valor_individual = opcoes_pontuacao.get("mostrar_valor_individual", False)

    # --- INÍCIO DA NOVA LÓGICA DE GERAÇÃO GARANTIDA ---

    # 1. PRÉ-GERAÇÃO DAS VARIAÇÕES
    # Para cada questão de cálculo, vamos descobrir todas as suas variações únicas primeiro.
    banco_de_variantes = defaultdict(list)
    variantes_unicas_por_questao = defaultdict(set)

    for q_base in questoes_base:
        q_id = q_base['id']
        
        # Se a questão não tem parâmetros (ex: teórica), ela só tem uma "variação".
        if not q_base.get('parametros'):
            variante = _gerar_variante_questao(q_base, f"static-{q_id}")
            if variante:
                banco_de_variantes[q_id] = [variante]
            continue

        # Para questões de cálculo, tentamos encontrar todas as variações únicas.
        max_tentativas_pool = 75 # Um número alto de tentativas para garantir encontrar as variações
        for i in range(max_tentativas_pool):
            seed_pool = f"pool-{q_id}-{i}"
            variante = _gerar_variante_questao(q_base, seed_pool)
            if variante:
                # Usamos o enunciado como uma "assinatura" para detectar variações únicas
                assinatura = variante['enunciado']
                if assinatura not in variantes_unicas_por_questao[q_id]:
                    variantes_unicas_por_questao[q_id].add(assinatura)
                    banco_de_variantes[q_id].append(variante)
        
        # Embaralha as variações encontradas para que a distribuição seja aleatória
        random.shuffle(banco_de_variantes[q_id])

    # 2. PREPARAÇÃO DOS 'SLOTS' (para Grupos de questões, sem alteração na lógica)
    questoes_base.sort(key=lambda q: q.get("grupo") or f"__individual_{q['id']}__")
    slots = []
    for key, group in groupby(questoes_base, key=lambda q: q.get("grupo")):
        questoes_do_grupo = list(group)
        if key and key.strip():
            slots.append(questoes_do_grupo)
        else:
            slots.extend([[q] for q in questoes_do_grupo])
    
    if opcoes_gabarito.get("embaralhar_questoes", True):
        random.shuffle(slots)

    # 3. MONTAGEM DAS VERSÕES DA PROVA
    versoes_finais = []
    num_questoes_me = sum(1 for slot in slots if slot[0]['formato_questao'] == 'Múltipla Escolha')
    
    if opcoes_gabarito.get("distribuir", True):
        gabarito_me_v1 = _gerar_gabarito_distribuido(num_questoes_me)
    else:
        gabarito_me_v1 = [random.choice(["A", "B", "C", "D", "E"]) for _ in range(num_questoes_me)]

    for i in range(num_versoes):
        versao_final = []
        gabarito_me_atual = [_rotacionar_letra(letra, i * opcoes_gabarito.get("rotacao", 0)) for letra in gabarito_me_v1]
        contador_me = 0

        for slot in slots:
            questao_base_para_versao = slot[i % len(slot)]
            q_id = questao_base_para_versao['id']

            # --- PONTO CENTRAL DA MUDANÇA ---
            # Em vez de gerar uma nova variação, pegamos uma da nossa lista pré-gerada.
            lista_de_variantes = banco_de_variantes.get(q_id, [])
            if not lista_de_variantes:
                continue # Salvaguarda caso nenhuma variação tenha sido encontrada

            # Pega a próxima variação disponível da lista, de forma cíclica
            variante = lista_de_variantes[i % len(lista_de_variantes)]
            
            # A partir daqui, a lógica é a mesma de antes, mas aplicada à 'variante' que já pegamos pronta.
            questao_final = variante.copy()
            if mostrar_valor_individual and valor_por_questao > 0:
                questao_final["valor"] = f"{valor_por_questao:.2f}".replace('.', ',')
            else:
                questao_final["valor"] = ""

            if variante['formato_questao'] == 'Múltipla Escolha':
                num_alternativas = variante.get('num_alternativas', 5)
                letras_disponiveis = ["A", "B", "C", "D", "E"][:num_alternativas]
                letra_correta_sorteada = gabarito_me_atual[contador_me]
                contador_me += 1
                
                idx_sorteado = ["A", "B", "C", "D", "E"].index(letra_correta_sorteada)
                letra_correta_final = letras_disponiveis[idx_sorteado % num_alternativas]
                
                alternativas = list(variante["alternativas_valores"])
                resposta_valor = variante["resposta_valor"]
                
                if resposta_valor not in alternativas and len(alternativas) < num_alternativas:
                    alternativas.append(resposta_valor)
                
                random.shuffle(alternativas)
                try:
                    idx_correta_atual = alternativas.index(resposta_valor)
                    idx_alvo = letras_disponiveis.index(letra_correta_final)
                    alternativas[idx_correta_atual], alternativas[idx_alvo] = alternativas[idx_alvo], alternativas[idx_correta_atual]
                except (ValueError, IndexError):
                    print(f"Aviso: não foi possível posicionar a resposta para a questão ID {variante['id_base']}...")
                
                questao_final["gabarito"] = letra_correta_final
                questao_final["alternativas"] = {letra: texto for letra, texto in zip(letras_disponiveis, alternativas)}

            elif variante['formato_questao'] == 'Verdadeiro ou Falso':
                questao_final["gabarito"] = "V" if variante["resposta_valor"] == "Verdadeiro" else "F"
            else:
                questao_final["gabarito"] = "D"
            
            versao_final.append(questao_final)
        
        versoes_finais.append(versao_final)
        
    return versoes_finais