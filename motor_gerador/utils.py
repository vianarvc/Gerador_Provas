"""
Funções utilitárias e helpers para o sistema de geração
"""

import random
import math
import json
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
    """Executa a lógica de tabela de parâmetros"""
    params = json.loads(params_json)
    for var in params.get("variaveis", []):
        nome, tipo, vals = var.get("nome"), var.get("tipo"), var.get("valores")
        if not all([nome, tipo, vals]): 
            continue
            
        if tipo == "Intervalo Inteiro": 
            min_v, max_v = map(int, [v.strip() for v in vals.split('-')])
            contexto[nome] = random.randint(min_v, max_v)
            
        elif tipo == "Intervalo Decimal": 
            min_v, max_v = map(float, [v.strip() for v in vals.split('-')])
            contexto[nome] = random.uniform(min_v, max_v)
            
        elif tipo == "Lista de Valores":
            lista = [v.strip() for v in vals.split(',')]
            try: 
                lista = [float(v) if '.' in v else int(v) for v in lista]
            except ValueError: 
                pass
            contexto[nome] = random.choice(lista)
            
    formula = params.get("formula_resposta", "")
    if formula: 
        contexto['resposta_valor'] = eval(formula, {"__builtins__": None}, contexto)


def _calcular_apenas_resposta(questao_base, seed):
    """Calcula apenas a resposta sem gerar variante completa"""
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


# Exportar constantes para uso externo
__all__ = [
    '_get_math_context',
    'formatar_unidade', 
    '_executar_logica_tabela',
    '_calcular_apenas_resposta',
    'PREFIX_DIVISORS',
    'VALID_BASE_UNITS'
]