"""
Motor Gerador - Sistema avançado para geração de questões e provas
"""

from .utils import (
    _get_math_context,
    formatar_unidade,
    _executar_logica_tabela
)

# ✅ ADICIONAR A NOVA FUNÇÃO DIRETAMENTE NAS EXPORTAÇÕES
__all__ = [
    # Utilitários
    'formatar_unidade',
    '_get_math_context',
    '_executar_logica_tabela',
    'gerar_prova_por_ids'  # ✅ ADICIONAR AQUI
]

# Versão
__version__ = "2.0.0"
__author__ = "Sistema de Geração de Provas"

# ✅ ADICIONAR IMPORT DIRETO (se não causar circularidade)
try:
    from .core import gerar_prova_por_ids
except ImportError:
    # Fallback para importação tardia se houver circularidade
    def gerar_prova_por_ids(*args, **kwargs):
        from .core import gerar_prova_por_ids as func
        return func(*args, **kwargs)

# Importações adiadas para evitar circularidade
def get_core_functions():
    from .core import (
        gerar_versoes_prova,
        gerar_cardapio_questoes,
        _gerar_variante_questao,
        gerar_prova_por_ids
    )
    return gerar_versoes_prova, gerar_cardapio_questoes, _gerar_variante_questao, gerar_prova_por_ids

def get_optimizer_functions():
    from .memory_optimizer import (
        CombinatorialEngine,
        _gerar_pool_combinatorio,
        optimize_memory_usage
    )
    return CombinatorialEngine, _gerar_pool_combinatorio, optimize_memory_usage