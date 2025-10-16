"""
Sistema avançado de cache para otimização de performance
"""

import time
import random


class CalculationCache:
    """Cache inteligente para cálculos de questões com controle por geração"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.cache = {}
        self.access_count = {}
        self.max_size = max_size
        self.ttl = ttl
        self.hits = 0
        self.misses = 0
        self.geracao_atual = "default"
        print(f"💾 Cache inicializado: {max_size} entradas, TTL: {ttl}s")
    
    def nova_geracao(self, nome_geracao=None):
        """
        Inicia uma nova geração de cache para uma prova específica
        """
        cache_size_antes = len(self.cache)
        
        if nome_geracao is None:
            nome_geracao = f"geracao_{random.randint(1000, 9999)}"
        
        self.geracao_atual = nome_geracao
        self.cache.clear()
        self.access_count.clear()
        print(f"🔄 Nova geração de cache: '{self.geracao_atual}' (limpadas {cache_size_antes} entradas)")
    
    def _generate_key_with_generation(self, key: str) -> str:
        """Gera chave única incluindo a geração atual"""
        return f"{self.geracao_atual}_{key}"
    
    def get(self, key: str):
        """Obtém resultado do cache com validação de TTL e geração"""
        key_com_geracao = self._generate_key_with_generation(key)
        
        if key_com_geracao in self.cache:
            value, timestamp = self.cache[key_com_geracao]
            if time.time() - timestamp < self.ttl:
                self.hits += 1
                self.access_count[key_com_geracao] = self.access_count.get(key_com_geracao, 0) + 1
                return value
            else:
                # Expirou - remove do cache
                del self.cache[key_com_geracao]
                if key_com_geracao in self.access_count:
                    del self.access_count[key_com_geracao]
        self.misses += 1
        return None
    
    def set(self, key: str, value):
        """Adiciona resultado ao cache com política LRU e geração"""
        key_com_geracao = self._generate_key_with_generation(key)
        
        if len(self.cache) >= self.max_size:
            # Remove menos usado (LRU)
            if self.access_count:
                least_used = min(self.access_count.items(), key=lambda x: x[1])[0]
                del self.cache[least_used]
                del self.access_count[least_used]
                print(f"   🗑️  Cache cheio - removida entrada: {least_used[:20]}...")
        
        self.cache[key_com_geracao] = (value, time.time())
        self.access_count[key_com_geracao] = 1
    
    def clear(self):
        """Limpa todo o cache"""
        cache_size = len(self.cache)
        self.cache.clear()
        self.access_count.clear()
        self.hits = 0
        self.misses = 0
        print(f"💾 Cache limpo completamente ({cache_size} entradas removidas)")
    
    def stats(self):
        """Retorna estatísticas de performance"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.1f}%",
            'size': len(self.cache),
            'max_size': self.max_size,
            'efficiency': f"{self.hits}/{total}" if total > 0 else "0/0",
            'geracao_atual': self.geracao_atual
        }
    
    def print_stats(self):
        """Exibe estatísticas formatadas"""
        stats = self.stats()
        print(f"\n📊 ESTATÍSTICAS DO CACHE:")
        print(f"   Geração atual: {stats['geracao_atual']}")
        print(f"   Acertos: {stats['hits']}")
        print(f"   Perdas: {stats['misses']}")
        print(f"   Taxa de acerto: {stats['hit_rate']}")
        print(f"   Eficiência: {stats['efficiency']}")
        print(f"   Uso: {stats['size']}/{stats['max_size']} entradas")


# Instância global do cache
calculation_cache = CalculationCache(max_size=800)


def get_cache_stats():
    """Retorna estatísticas do cache para a interface"""
    try:
        return calculation_cache.stats()
    except:
        return None


def clear_cache():
    """Limpa o cache - pode ser chamado pela interface"""
    calculation_cache.clear()


def print_cache_stats():
    """Exibe estatísticas do cache no console"""
    calculation_cache.print_stats()


def finalizar_geracao_com_statistics():
    """Função para chamar após gerar provas/cardápio"""
    print_cache_stats()


def print_cache_stats_to_log(log_dialog=None):
    """Exibe estatísticas do cache no log dialog"""
    stats = get_cache_stats()
    if stats and log_dialog:
        stats_text = f"""
📊 ESTATÍSTICAS DO CACHE:
   • Geração: {stats['geracao_atual']}
   • Acertos: {stats['hits']}
   • Perdas: {stats['misses']}
   • Taxa de acerto: {stats['hit_rate']}
   • Eficiência: {stats['efficiency']}
   • Uso: {stats['size']}/{stats['max_size']} entradas
   • Economia: {stats['hits']} cálculos poupados
"""
        log_dialog.append_log(stats_text)


def iniciar_nova_geracao_cache(nome_geracao=None):
    """
    Inicia uma nova geração de cache para uma prova específica
    """
    calculation_cache.nova_geracao(nome_geracao)


def get_geracao_atual():
    """Retorna a geração atual do cache"""
    return calculation_cache.geracao_atual


def get_cache_stats_formatted():
    """Retorna estatísticas do cache formatadas para a interface"""
    stats = get_cache_stats()
    if stats:
        return f"""
📊 ESTATÍSTICAS DO CACHE:
   • Geração: {stats['geracao_atual']}
   • Acertos: {stats['hits']}
   • Perdas: {stats['misses']}
   • Taxa de acerto: {stats['hit_rate']}
   • Eficiência: {stats['efficiency']}
   • Uso: {stats['size']}/{stats['max_size']} entradas
   • Economia: {stats['hits']} cálculos poupados
"""
    else:
        return "📊 ESTATÍSTICAS DO CACHE: Indisponíveis"