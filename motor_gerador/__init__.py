"""
Motor Gerador - Sistema avançado para geração de questões e provas
"""

from .cache_manager import (
    CalculationCache,
    calculation_cache,
    get_cache_stats,
    clear_cache,
    iniciar_nova_geracao_cache,
    get_cache_stats_formatted,
    print_cache_stats_to_log
)

from .utils import (
    _get_math_context,
    formatar_unidade,
    _executar_logica_tabela,
    _calcular_apenas_resposta
)

# Exportações para acesso direto
__all__ = [
    # Core
    'gerar_versoes_prova',
    'gerar_cardapio_questoes',
    '_gerar_variante_questao',
    
    # Cache
    'CalculationCache',
    'calculation_cache',
    'get_cache_stats',
    'clear_cache',
    
    # Utilitários
    'formatar_unidade',
    '_get_math_context'
]

# Versão
__version__ = "2.0.0"
__author__ = "Sistema de Geração de Provas"

# Importações adiadas para evitar circularidade
def get_core_functions():
    from .core import (
        gerar_versoes_prova,
        gerar_cardapio_questoes,
        _gerar_variante_questao,
        _gerar_gabarito_distribuido,
        _rotacionar_letra
    )
    return gerar_versoes_prova, gerar_cardapio_questoes, _gerar_variante_questao, _gerar_gabarito_distribuido, _rotacionar_letra

def get_parallel_functions():
    from .parallel_engine import (
        _detectar_melhor_estrategia_paralelismo,
        _deve_usar_paralelismo,
        gerar_versoes_prova_paralelo,
        gerar_versoes_prova_serial
    )
    return _detectar_melhor_estrategia_paralelismo, _deve_usar_paralelismo, gerar_versoes_prova_paralelo, gerar_versoes_prova_serial

def get_optimizer_functions():
    from .memory_optimizer import (
        CombinatorialEngine,
        _gerar_pool_combinatorio,
        optimize_memory_usage
    )
    return CombinatorialEngine, _gerar_pool_combinatorio, optimize_memory_usage