"""
Sistema inteligente de paralelismo para geração de múltiplas versões
"""

import multiprocessing
import random
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from itertools import groupby
from collections import Counter

def _gerar_versao_unica_wrapper(args):
    """
    Wrapper para gerar uma única versão em processo separado
    """
    slots, opcoes_geracao, seed_offset, num_questoes_me, gabarito_me_v1 = args
    return _gerar_versao_unica(slots, opcoes_geracao, seed_offset, num_questoes_me, gabarito_me_v1)


def _gerar_versao_unica(slots, opcoes_geracao, seed_offset, num_questoes_me, gabarito_me_v1):
    """
    Gera uma única versão de prova - função interna para paralelismo
    """
    # Importação local para evitar circularidade
    from .core import _gerar_variante_questao, _rotacionar_letra
    
    # Configura seed única para esta versão
    import random
    random.seed(seed_offset)
    
    opcoes_gabarito = opcoes_geracao.get("gabarito", {})
    opcoes_pontuacao = opcoes_geracao.get("pontuacao", {})
    valor_por_questao = opcoes_pontuacao.get("valor_por_questao", 0.0)
    mostrar_valor_individual = opcoes_pontuacao.get("mostrar_valor_individual", False)
    
    versao_data = {
        'letra': chr(65 + seed_offset),  # A, B, C, D...
        'questoes': []
    }
    
    gabarito_me_atual = [_rotacionar_letra(letra, seed_offset * opcoes_gabarito.get("rotacao", 0)) for letra in gabarito_me_v1]
    contador_me = 0

    for slot in slots:
        questao_base_para_versao = slot[seed_offset % len(slot)]
        
        variante = _gerar_variante_questao(questao_base_para_versao, None)
        
        if not variante:
            continue

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
    
    return versao_data


def _detectar_melhor_estrategia_paralelismo():
    """
    Detecta a melhor estratégia baseada no hardware
    """
    num_cores = multiprocessing.cpu_count()
    
    # Estimativa simples de memória
    try:
        import psutil
        memoria_gb = psutil.virtual_memory().total / (1024.**3)
    except:
        memoria_gb = 4  # Fallback
    
    print(f"🔍 Detectado: {num_cores} cores, ~{memoria_gb:.1f}GB RAM")
    
    if num_cores >= 4 and memoria_gb >= 8:
        return "processos"  # PCs bons
    elif num_cores >= 2 and memoria_gb >= 4:
        return "threads"    # PCs médios
    else:
        return "serial"     # PCs fracos


def _deve_usar_paralelismo(questoes_base, num_versoes):
    """
    Decide se vale a pena usar paralelismo
    """
    if num_versoes == 1:
        return False
    
    # Conta questões complexas (combinatórias)
    questao_complexas = sum(1 for q in questoes_base 
                          if q.get("gerar_alternativas_auto") and q.get("parametros"))
    
    return questao_complexas >= max(1, len(questoes_base) * 0.25)


def gerar_versoes_prova_paralelo(questoes_base, num_versoes, opcoes_geracao):
    """
    Versão paralelizada inteligente
    """
    # Importação local para evitar circularidade
    from .core import _gerar_gabarito_distribuido
    
    # Prepara slots e gabarito (mesma lógica da versão serial)
    questoes_base.sort(key=lambda q: q.get("grupo") or f"__individual_{q['id']}__")
    slots = []
    for key, group in groupby(questoes_base, key=lambda q: q.get("grupo")):
        questoes_do_grupo = list(group)
        if key and key.strip():
            slots.append(questoes_do_grupo)
        else:
            slots.extend([[q] for q in questoes_do_grupo])
    
    if opcoes_geracao.get("gabarito", {}).get("embaralhar_questoes", True):
        random.shuffle(slots)

    num_questoes_me = sum(1 for slot in slots if slot[0]['formato_questao'] == 'Múltipla Escolha')
    
    if num_questoes_me == 1:
        gabarito_me_v1 = [random.choice(["A", "B", "C", "D", "E"])]
    elif opcoes_geracao.get("gabarito", {}).get("distribuir", True):
        gabarito_me_v1 = _gerar_gabarito_distribuido(num_questoes_me)
        random.shuffle(gabarito_me_v1)
    else:
        gabarito_me_v1 = [random.choice(["A", "B", "C", "D", "E"]) for _ in range(num_questoes_me)]

    estrategia = _detectar_melhor_estrategia_paralelismo()
    print(f"🔄 Usando estratégia: {estrategia}")
    
    # Prepara argumentos para cada versão
    args_list = [(slots, opcoes_geracao, i, num_questoes_me, gabarito_me_v1) for i in range(num_versoes)]
    
    try:
        if estrategia == "processos":
            # Máximo desempenho - ProcessPoolExecutor
            num_workers = min(multiprocessing.cpu_count(), num_versoes, 4)
            with ProcessPoolExecutor(max_workers=num_workers) as executor:
                versoes_geradas = list(executor.map(_gerar_versao_unica_wrapper, args_list))
                
        else:  # estrategia == "threads"
            # Balanceado - ThreadPoolExecutor
            num_workers = min(multiprocessing.cpu_count() * 2, num_versoes, 8)
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                versoes_geradas = list(executor.map(_gerar_versao_unica_wrapper, args_list))
        
        print(f"✅ Paralelismo ({estrategia}): {num_versoes} versões com {num_workers} workers")
        return versoes_geradas
        
    except Exception as e:
        print(f"⚠️  Paralelismo falhou: {e}")
        return None


def gerar_versoes_prova_serial(questoes_base, num_versoes, opcoes_geracao):
    """
    Versão serial de fallback
    """
    # Importação local para evitar circularidade
    from .core import _gerar_gabarito_distribuido
    
    print("🔄 Usando processamento serial...")
    
    # Prepara slots e gabarito
    questoes_base.sort(key=lambda q: q.get("grupo") or f"__individual_{q['id']}__")
    slots = []
    for key, group in groupby(questoes_base, key=lambda q: q.get("grupo")):
        questoes_do_grupo = list(group)
        if key and key.strip():
            slots.append(questoes_do_grupo)
        else:
            slots.extend([[q] for q in questoes_do_grupo])
    
    if opcoes_geracao.get("gabarito", {}).get("embaralhar_questoes", True):
        random.shuffle(slots)

    num_questoes_me = sum(1 for slot in slots if slot[0]['formato_questao'] == 'Múltipla Escolha')
    
    if num_questoes_me == 1:
        gabarito_me_v1 = [random.choice(["A", "B", "C", "D", "E"])]
    elif opcoes_geracao.get("gabarito", {}).get("distribuir", True):
        gabarito_me_v1 = _gerar_gabarito_distribuido(num_questoes_me)
        random.shuffle(gabarito_me_v1)
    else:
        gabarito_me_v1 = [random.choice(["A", "B", "C", "D", "E"]) for _ in range(num_questoes_me)]

    versoes_geradas = []
    
    for i in range(num_versoes):
        versao_data = _gerar_versao_unica(slots, opcoes_geracao, i, num_questoes_me, gabarito_me_v1)
        versoes_geradas.append(versao_data)
    
    return versoes_geradas