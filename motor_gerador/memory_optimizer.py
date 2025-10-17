"""
Otimização de memória e processamento combinatorial para questões complexas
"""

import random
import ast
from itertools import product
from typing import Dict, List, Set, Any, Tuple
import hashlib

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


def _gerar_pool_combinatorio(questao_base, params_code, base_context):
    """
    ✅ VERSÃO SEM CACHE: Usa o CombinatorialEngine diretamente
    """
    questao_id = questao_base.get('id', 'N/A')
    print(f"   🔄 Processando - Questão {questao_id}")
    
    # Processa normalmente sem cache
    engine = CombinatorialEngine(
        max_combinations=20000,
        max_sample=200
    )
    
    result = engine.generate_smart_pool(questao_base, params_code, base_context)
    
    return result


def optimize_memory_usage():
    """
    Funções para otimização de uso de memória
    """
    import gc
    collected = gc.collect()
    print(f"🧹 Coleta de lixo: {collected} objetos liberados")
    
    # Limpa caches internos do Python
    import sys
    for module in list(sys.modules.values()):
        if hasattr(module, '__dict__') and hasattr(module.__dict__, 'clear'):
            try:
                module.__dict__.clear()
            except:
                pass
    
    return collected