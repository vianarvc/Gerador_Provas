# motor_gerador.py 20h54 04/10/25

import random, math, json, traceback, re
from collections import Counter, defaultdict
from itertools import groupby
from database import obter_todas_questoes_para_cardapio, obter_disciplina_nome_por_id
import gerador_pdf
from PyQt5.QtWidgets import QApplication
from constants import PREFIX_DIVISORS, VALID_BASE_UNITS

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

import random, math, json, traceback, re
from collections import Counter, defaultdict
from itertools import groupby, product
import ast
from typing import Dict, List, Set, Any, Tuple
import os

class CombinatorialEngine:
    """Motor otimizado para questões com alto número de combinações - FOCADO EM ELETROTÉCNICA"""
    
    def __init__(self, max_combinations: int = 20000, max_sample: int = 1000):
        self.max_combinations = max_combinations
        self.max_sample = max_sample
        
    def generate_smart_pool(self, questao_base: Dict, params_code: str, base_context: Dict) -> Set:
        """
        Gera pool inteligente com amostragem estratégica para questões de eletrotécnica
        """
        q_id = questao_base.get('id', 'N/A')
        
        try:
            # Análise AST do código para identificar variáveis
            choice_vars, calculation_source = self._analyze_parameters(params_code, base_context)
            if not choice_vars:
                return None
                
            print(f"🔍 Engine Combinatória - Questão ID {q_id}")
            print(f"   Variáveis encontradas: {list(choice_vars.keys())}")
            print(f"   Tamanhos dos domínios: {[len(v) for v in choice_vars.values()]}")
            
            # Calcula total de combinações possíveis
            total_possible = 1
            for values in choice_vars.values():
                total_possible *= len(values)
            print(f"   Combinações totais possíveis: {total_possible:,}")
            
            # Seleciona estratégia baseada nas características
            sampling_strategy = self._select_sampling_strategy(choice_vars, total_possible)
            print(f"   Estratégia selecionada: {sampling_strategy.__name__}")
            
            # Gera combinações usando a estratégia selecionada
            combinations = sampling_strategy(choice_vars, base_context, total_possible)
            print(f"   Combinações a processar: {len(combinations):,}")
            
            # Processa as combinações e coleta resultados únicos
            results = self._process_combinations(
                combinations, choice_vars, calculation_source, base_context, questao_base
            )
            
            print(f"   ✅ Resultados únicos gerados: {len(results)}")
            return results
            
        except Exception as e:
            print(f"   ❌ Erro no motor combinatório: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _analyze_parameters(self, params_code: str, base_context: Dict) -> Tuple[Dict, str]:
        """Analisa o código Python e extrai variáveis de random.choice"""
        try:
            tree = ast.parse(params_code)
            choice_assignments = []
            other_nodes = []
            
            for node in tree.body:
                if (isinstance(node, ast.Assign) and 
                    isinstance(node.value, ast.Call) and
                    isinstance(node.value.func, ast.Attribute) and 
                    isinstance(node.value.func.value, ast.Name) and
                    node.value.func.value.id == 'random' and 
                    node.value.func.attr == 'choice'):
                    choice_assignments.append(node)
                else:
                    other_nodes.append(node)
            
            if not choice_assignments:
                return None, ""
            
            # Executa o código original para obter os valores reais
            temp_context = base_context.copy()
            temp_context['random'] = random
            exec(params_code, temp_context)
            
            # Extrai as listas de valores para cada variável
            choice_vars = {}
            for assign_node in choice_assignments:
                var_name = assign_node.targets[0].id
                arg_as_string = ast.unparse(assign_node.value.args[0])
                values = eval(arg_as_string, temp_context)
                choice_vars[var_name] = values
            
            # Prepara o código de cálculo (parte sem random.choice)
            calculation_tree = ast.Module(body=other_nodes, type_ignores=[])
            calculation_source = ast.unparse(calculation_tree)
            
            return choice_vars, calculation_source
            
        except Exception as e:
            print(f"   ❌ Erro na análise AST: {e}")
            return None, ""
    
    def _select_sampling_strategy(self, choice_vars: Dict, total_possible: int) -> callable:
        """Seleciona a melhor estratégia de amostragem baseada nas variáveis"""
        if total_possible <= self.max_combinations:
            return self._exhaustive_sampling
        
        # Analisa tipos de variáveis
        has_continuous = False
        has_large_domains = False
        
        for values in choice_vars.values():
            if any(isinstance(v, (int, float)) for v in values):
                has_continuous = True
            if len(values) > 10:  # Domínio grande
                has_large_domains = True
        
        if has_continuous:
            return self._continuous_sampling
        elif has_large_domains:
            return self._discrete_large_sampling
        else:
            return self._discrete_sampling
    
    def _exhaustive_sampling(self, choice_vars: Dict, base_context: Dict, total_possible: int) -> List[Tuple]:
        """Processamento completo (para combinações pequenas)"""
        var_names = list(choice_vars.keys())
        value_lists = list(choice_vars.values())
        return list(product(*value_lists))
    
    def _continuous_sampling(self, choice_vars: Dict, base_context: Dict, total_possible: int) -> List[Tuple]:
        """
        Amostragem REOTIMIZADA: Gera menos combinações para evitar pool excessivo
        """
        var_names = list(choice_vars.keys())
        
        # 1. Combinação correta garantida
        correct_combination = tuple(base_context.get(v) for v in var_names)
        samples = set([correct_combination])
        
        # 2. Estratégia MAIS CONSERVADORA para variáveis contínuas
        max_samples = min(200, total_possible)  # REDUZIDO drasticamente
        
        # 3. Para eletrotécnica: foca nos valores mais representativos
        for i, (var_name, values) in enumerate(choice_vars.items()):
            if all(isinstance(v, (int, float)) for v in values) and len(samples) < max_samples:
                sorted_vals = sorted(values)
                n = len(sorted_vals)
                
                # Valores CRÍTICOS apenas: mínimo, máximo, mediana
                critical_values = [
                    sorted_vals[0],      # Mínimo
                    sorted_vals[-1],     # Máximo
                    sorted_vals[n//2],   # Mediana
                ]
                
                # Para cada valor crítico, cria uma combinação
                for critical_val in critical_values:
                    if len(samples) >= max_samples:
                        break
                    new_comb = list(correct_combination)
                    new_comb[i] = critical_val
                    samples.add(tuple(new_comb))
        
        # 4. Amostra aleatória MUITO limitada
        attempts = 0
        max_attempts = 500
        
        while len(samples) < max_samples and attempts < max_attempts:
            new_sample = tuple(random.choice(values) for values in choice_vars.values())
            samples.add(new_sample)
            attempts += 1
        
        print(f"   🎯 Amostras geradas: {len(samples)} (limite: {max_samples})")
        return list(samples)
    
    def _discrete_large_sampling(self, choice_vars: Dict, base_context: Dict, total_possible: int) -> List[Tuple]:
        """Amostragem para variáveis discretas com domínios grandes"""
        var_names = list(choice_vars.keys())
        correct_combination = tuple(base_context.get(v) for v in var_names)
        samples = set([correct_combination])
        
        # Estratégia: amostra proporcional ao tamanho do domínio
        max_samples = min(self.max_sample, total_possible)
        
        while len(samples) < max_samples:
            new_sample = []
            for var_name, values in choice_vars.items():
                # Amostra mais diversa para domínios maiores
                if len(values) > 5:
                    # Pega valores espaçados para domínios grandes
                    idx = random.randint(0, len(values) - 1)
                    new_sample.append(values[idx])
                else:
                    new_sample.append(random.choice(values))
            
            samples.add(tuple(new_sample))
        
        return list(samples)
    
    def _discrete_sampling(self, choice_vars: Dict, base_context: Dict, total_possible: int) -> List[Tuple]:
        """Amostragem padrão para variáveis discretas"""
        var_names = list(choice_vars.keys())
        correct_combination = tuple(base_context.get(v) for v in var_names)
        samples = set([correct_combination])
        
        max_samples = min(self.max_sample, total_possible)
        attempts = 0
        max_attempts = max_samples * 2
        
        while len(samples) < max_samples and attempts < max_attempts:
            new_sample = tuple(random.choice(values) for values in choice_vars.values())
            samples.add(new_sample)
            attempts += 1
        
        return list(samples)
    
    def _process_combinations(self, combinations: List[Tuple], choice_vars: Dict, 
                            calculation_source: str, base_context: Dict, questao_base: Dict) -> Set:
        """Executa o cálculo para cada combinação e filtra resultados válidos"""
        var_names = list(choice_vars.keys())
        possible_outcomes = set()
        permitir_negativos = questao_base.get("permitir_negativos", False)
        
        print(f"   🔄 Processando {len(combinations)} combinações...")
        
        for i, combination in enumerate(combinations):
            try:
                # Monta o script de atribuição
                assignment_script = ""
                current_combination_dict = dict(zip(var_names, combination))
                
                for var_name, value in current_combination_dict.items():
                    assignment_script += f"{var_name} = {repr(value)}\n"
                
                full_script = assignment_script + calculation_source
                
                # Executa em contexto isolado
                exec_context = base_context.copy()
                exec_context.update(current_combination_dict)
                exec(full_script, exec_context)
                
                # Obtém o resultado
                result = exec_context.get('resposta_valor') or exec_context.get('resposta')
                
                # Aplica filtros
                if self._is_valid_result(result, permitir_negativos):
                    if isinstance(result, dict) and 'valores' in result:
                        # Modo 1: Múltiplos valores
                        vals_dict = result['valores']
                        hashable_result = tuple(sorted(vals_dict.items()))
                        possible_outcomes.add(hashable_result)
                    elif isinstance(result, (int, float)):
                        # Modo 2: Valor único
                        possible_outcomes.add(result)
                        
            except Exception as e:
                # Ignora erros em combinações individuais
                continue
        
        return possible_outcomes
    
    def _is_valid_result(self, result, permitir_negativos: bool) -> bool:
        """Verifica se o resultado é válido baseado nos filtros"""
        if result is None:
            return False
        
        # Filtro anti-zero
        if isinstance(result, (int, float)) and abs(result) < 1e-15:
            return False
        
        if isinstance(result, dict) and 'valores' in result:
            for v in result['valores'].values():
                if isinstance(v, (int, float)) and abs(v) < 1e-15:
                    return False
                if not permitir_negativos and isinstance(v, (int, float)) and v < 0:
                    return False
        
        # Filtro de negativos
        if not permitir_negativos and isinstance(result, (int, float)) and result < 0:
            return False
            
        return True
#-------------------------------------------------------------------------------------------------------

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
    Formata um número usando notação de engenharia, mas APENAS para unidades permitidas.
    - unidade: A unidade base (ex: 'A', 'V', 'Ω').
    - incluir_unidade: Se False, retorna apenas o número com prefixo.
    """
    if not isinstance(valor, (int, float)):
        return str(valor)

    # Verifica se a unidade PODE receber um prefixo usando a lista de permissão
    if unidade in VALID_BASE_UNITS:
        # --- BLOCO DE LÓGICA DE PREFIXO (só para 'V', 'A', 'F', etc.) ---

        # Usa uma tolerância para tratar números de ponto flutuante quase nulos como zero.
        if abs(valor) < 1e-15:
            if incluir_unidade and unidade:
                return f"0 {unidade}"
            return "0"

        prefixos = [(1e12, 'T'), (1e9, 'G'), (1e6, 'M'), (1e3, 'k'), (1, ''),
                    (1e-3, 'm'), (1e-6, 'µ'), (1e-9, 'n'), (1e-12, 'p')]

        for mult, prefixo in prefixos:
            if abs(valor) >= mult:
                v_ajustado = valor / mult
                
                if round(v_ajustado, 2) == int(v_ajustado):
                    valor_str = f"{int(v_ajustado)}"
                else:
                    valor_str = f"{v_ajustado:.2f}".replace('.', ',')
                
                if incluir_unidade:
                    return f"{valor_str} {prefixo}{unidade}".strip()
                else:
                    return f"{valor_str} {prefixo}".strip()
        
        # Fallback para números menores que 'pico' (ex: femto), usa notação científica.
        valor_str = f"{valor:.2e}".replace('.', ',')

    else:
        # --- BLOCO SEM PREFIXO (para 'e', 'N/C', 'kWh', etc.) ---
        # Apenas formata o número.
        if isinstance(valor, int):
             valor_str = str(valor)
        elif round(valor, 2) == int(valor):
            valor_str = f"{int(round(valor, 2))}"
        else:
            valor_str = f"{valor:.2f}".replace('.', ',')

    # Monta a string final para ambos os casos (com ou sem prefixo)
    if incluir_unidade and unidade:
        return f"{valor_str} {unidade}"
    else:
        return valor_str

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
    SUBSTITUIÇÃO OTIMIZADA: Usa o CombinatorialEngine para gerar pools inteligentes
    """
    engine = CombinatorialEngine(
        max_combinations=20000,
        max_sample=1000
    )
    
    return engine.generate_smart_pool(questao_base, params_code, base_context)

def _gerar_variante_questao(questao_base, seed):
    is_multi_valor = False
    try:
        if seed is not None:
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

        placeholders = re.findall(r'\{(\w+)\}(?:\s*)(\S+)\b', enunciado_template)
        for var_name, potential_unit_text in placeholders:
            if var_name in contexto_formatado and isinstance(contexto_formatado[var_name], (int, float)) and len(potential_unit_text) > 1:
                
                prefix = potential_unit_text[0]
                base_unit = potential_unit_text[1:]
                
                # A validação agora usa as constantes importadas do arquivo central
                if prefix in PREFIX_DIVISORS and base_unit in VALID_BASE_UNITS:
                    original_value = float(contexto_formatado[var_name])
                    divisor = PREFIX_DIVISORS[prefix]
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
                        #print(f"AVISO: A questão ID {questao_base.get('id', 'N/A')} não gerou resultados combinatórios. Questão descartada.")
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
                            #print(f"FALHA: A variável '{chave}' da ID {questao_base.get('id', 'N/A')} não teve valores válidos. Questão descartada.")
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
                        #print(f"FALHA: Resposta correta da ID {questao_base.get('id', 'N/A')} contém negativo. Descartada.")
                        return None
                    if any(abs(v) < 1e-9 for v in resposta_correta_dict_numerico.values() if isinstance(v, (int, float))):
                        #print(f"FALHA: Resposta correta da ID {questao_base.get('id', 'N/A')} contém zero. Descartada.")
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
                    
                    #print(f"DEBUG (ID {questao_base.get('id', 'N/A')} MODO 1): Pool de textos final: {sorted(alternativas_valores)}")

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
                        #if texto_formatado.strip().startswith('0'):
                        if abs(valor_num) < 1e-15:
                            continue

                            print(f"\n--- DEBUG DETALHADO PARA QUESTÃO ID {questao_base.get('id')} ---")

                        pool_de_textos.add(texto_formatado)
                
                    # --- INÍCIO DO BLOCO DE DEBUG DETALHADO ---
                    # 1. Qual é a resposta correta numérica exata?
                    resposta_correta_num = resposta_valor_calculado
                    print(f"DEBUG: Resposta correta NUMÉRICA: {repr(resposta_correta_num)}")

                    # 2. Como ela fica depois de formatada?
                    resposta_correta_texto = formatar_unidade(resposta_correta_num, unidade)
                    print(f"DEBUG: Resposta correta FORMATADA: '{resposta_correta_texto}'")

                    # 3. Quantos itens o pool de textos tem?
                    print(f"DEBUG: Tamanho do pool de textos: {len(pool_de_textos)}")

                    # 4. A resposta correta formatada está no pool? (ESTA É A VERIFICAÇÃO CRÍTICA)
                    esta_no_pool = resposta_correta_texto in pool_de_textos
                    print(f"DEBUG: A resposta formatada ESTÁ no pool de textos? {esta_no_pool}")

                    if not esta_no_pool:
                        # Se não estiver, vamos procurar por um valor numericamente próximo
                        valor_proximo = None
                        min_diff = float('inf')
                        for num in pool_numerico:
                            diff = abs(resposta_correta_num - num)
                            if diff < min_diff:
                                min_diff = diff
                                valor_proximo = num
                        if valor_proximo is not None:
                            print(f"DEBUG: Valor NUMÉRICO mais próximo no pool: {repr(valor_proximo)}")
                            print(f"DEBUG: Valor mais próximo FORMATADO: '{formatar_unidade(valor_proximo, unidade)}'")
                            print(f"DEBUG: Diferença numérica mínima: {min_diff}")
                    
                    print(f"--- FIM DO DEBUG ---\n")
                    # --- FIM DO BLOCO DE DEBUG ---

                        
                    
                    print(f"DEBUG (ID {questao_base.get('id', 'N/A')}): Pool de textos final (após filtros): {sorted(list(pool_de_textos))}")

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
                    
                    max_pool_size = 30  # Número máximo de alternativas no pool final

                    if len(pool_de_textos) > max_pool_size:
                        print(f"DEBUG: Pool reduzido de {len(pool_de_textos)} para {max_pool_size} alternativas")
                        # Converte para lista, remove a resposta correta, limita, e adiciona a resposta de volta
                        pool_list = list(pool_de_textos)
                        if resposta_correta_texto in pool_list:
                            pool_list.remove(resposta_correta_texto)
                        # Seleciona aleatoriamente um subconjunto
                        pool_list_limited = random.sample(pool_list, max_pool_size - 1)
                        pool_de_textos = set(pool_list_limited) | {resposta_correta_texto}

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

    '''imagem_path = questao_base.get("imagem", "")
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
        "is_multi_valor": is_multi_valor }'''
    
    imagem_path = questao_base.get("imagem", "")
    if imagem_path:
        imagem_path = imagem_path.replace('\\', '/')
        # Verifica se o arquivo de imagem realmente existe
        if not os.path.exists(imagem_path):
            print(f"⚠️ AVISO: Imagem não encontrada - {imagem_path}")
            imagem_path = ""  # Remove a imagem se não existir
    
    largura_imagem = questao_base.get("imagem_largura_percentual") or 50
    
    return { 
        "id_base": questao_base.get("id"), 
        "tema": questao_base.get("tema"), 
        "formato_questao": formato_questao, 
        "num_alternativas": num_alternativas, 
        "enunciado": enunciado_final, 
        "imagem": imagem_path,  # ← Já validada
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
    random.seed(None) 
    opcoes_gabarito = opcoes_geracao.get("gabarito", {})
    opcoes_pontuacao = opcoes_geracao.get("pontuacao", {})
    valor_por_questao = opcoes_pontuacao.get("valor_por_questao", 0.0)
    mostrar_valor_individual = opcoes_pontuacao.get("mostrar_valor_individual", False)

    # --- LÓGICA DE PRÉ-GERAÇÃO REMOVIDA: Não precisamos mais do 'banco_de_variantes' ---

    # 1. PREPARAÇÃO DOS 'SLOTS' (lógica original, sem alterações)
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

    # 2. PREPARAÇÃO DOS GABARITOS (lógica original, sem alterações)
    versoes_finais = []
    num_questoes_me = sum(1 for slot in slots if slot[0]['formato_questao'] == 'Múltipla Escolha')
    
    if num_questoes_me == 1:
        gabarito_me_v1 = [random.choice(["A", "B", "C", "D", "E"])]
    elif opcoes_gabarito.get("distribuir", True):
        gabarito_me_v1 = _gerar_gabarito_distribuido(num_questoes_me)
        random.shuffle(gabarito_me_v1)
    else:
        gabarito_me_v1 = [random.choice(["A", "B", "C", "D", "E"]) for _ in range(num_questoes_me)]

    # 3. MONTAGEM DAS VERSÕES (LÓGICA OTIMIZADA)
    for i in range(num_versoes):
        # Prepara a estrutura para a nova versão (usando a que já funciona com o gerador_pdf)
        letra_versao = chr(65 + i)
        versao_data = {
            'letra': letra_versao,
            'questoes': []
        }
        
        gabarito_me_atual = [_rotacionar_letra(letra, i * opcoes_gabarito.get("rotacao", 0)) for letra in gabarito_me_v1]
        contador_me = 0

        for slot in slots:
            questao_base_para_versao = slot[i % len(slot)]
            
            # --- PONTO CENTRAL DA MUDANÇA ---
            # Geramos uma nova variante AQUI, sob demanda, para cada versão da prova.
            # O 'None' no seed garante que seja aleatória a cada chamada.
            variante = _gerar_variante_questao(questao_base_para_versao, None)
            
            # Se a geração da variante falhar por algum motivo, pulamos para a próxima questão.
            if not variante:
                print(f"AVISO: A geração da variante para a questão ID {questao_base_para_versao['id']} falhou. A questão não será incluída nesta versão da prova.")
                continue

            # --- O resto do código é o mesmo de antes, processando a 'variante' ---
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
                
                # Salvaguarda: Se por algum motivo as alternativas estiverem vazias, não continuamos
                if not alternativas or resposta_valor is None:
                    continue

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
            else: # Discursiva
                questao_final["gabarito"] = "D"
            
            versao_data['questoes'].append(questao_final)
        
        versoes_finais.append(versao_data)
        
    return versoes_finais

def gerar_cardapio_questoes(caminho_salvar_pdf, disciplina_id=None, tema=None, log_dialog=None):
    """
    Orquestra a criação do PDF do cardápio, usando um LogDialog e
    uma lógica resiliente de múltiplas tentativas para gerar cada questão.
    """
    def log_message(message):
        """ Helper local para log. """
        if log_dialog:
            log_dialog.append_log(message)
            QApplication.processEvents()
        else:
            print(message)
            
    try:
        log_message("Iniciando a geração do cardápio de questões com filtros...")
        
        questoes_base = obter_todas_questoes_para_cardapio(disciplina_id, tema)
        if not questoes_base:
            raise ValueError("Nenhuma questão encontrada para os filtros selecionados.")

        log_message(f"Encontradas {len(questoes_base)} questões para o cardápio.")
        
        questoes_geradas = []
        for questao_base in questoes_base:
            
            # --- INÍCIO DA LÓGICA DE TENTATIVAS ---
            variante = None
            numero_de_tentativas = 100  # Limite de segurança para não ficar em loop infinito

            for tentativa in range(numero_de_tentativas):
                # A cada tentativa, usamos uma semente diferente (ID da questão + número da tentativa)
                seed_da_tentativa = questao_base['id'] + tentativa
                
                variante_tentativa = _gerar_variante_questao(questao_base, seed=seed_da_tentativa)
                
                # Se a geração foi bem-sucedida, guardamos a variante e paramos de tentar
                if variante_tentativa:
                    variante = variante_tentativa
                    break  # Interrompe o loop de tentativas e vai para a próxima questão
            # --- FIM DA LÓGICA DE TENTATIVAS ---

            # Apenas se uma variante válida foi encontrada, nós a processamos e adicionamos à lista
            if variante:
                if variante.get("formato_questao") == "Múltipla Escolha":
                    letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    alternativas_dict = {}
                    # Apenas ordena a lista de valores, sem embaralhar
                    valores_ordenados = sorted(variante.get("alternativas_valores", []))
                    for i, valor in enumerate(valores_ordenados):
                        alternativas_dict[letras[i]] = valor
                    variante['alternativas'] = alternativas_dict

                variante['id_base'] = questao_base['id']
                variante['ativa'] = questao_base['ativa']
                variante['disciplina_id'] = questao_base['disciplina_id']
                questoes_geradas.append(variante)
            else:
                # Opcional: Loga a falha final apenas se todas as tentativas falharem
                log_message(f"AVISO: Questão ID {questao_base['id']} foi descartada do cardápio após {numero_de_tentativas} tentativas falharem.")


        log_message(f"Geradas {len(questoes_geradas)} variantes para o PDF.")

        contexto_extra = { "obter_disciplina_nome_por_id": obter_disciplina_nome_por_id }
        template_path = 'modelo_cardapio.tex'
        
        gerador_pdf.gerar_pdf_cardapio(
            questoes_geradas, caminho_salvar_pdf, template_path, contexto_extra, log_dialog
        )
        
        log_message("Cardápio de questões gerado com sucesso!")
        return True, "Cardápio gerado com sucesso!"

    except Exception as e:
        log_message(f"ERRO ao gerar cardápio: {e}")
        return False, f"Ocorreu um erro: {e}"