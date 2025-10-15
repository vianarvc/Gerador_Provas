"""
Módulo principal com as funções centrais de geração de provas e cardápios
"""

import random
import re
import os
from collections import Counter
from itertools import groupby

from PyQt5.QtWidgets import QApplication

from .cache_manager import calculation_cache, iniciar_nova_geracao_cache, print_cache_stats_to_log
from .utils import _get_math_context, _executar_logica_tabela, formatar_unidade


def _gerar_variante_questao(questao_base, seed):
    """
    Gera uma variante única de uma questão base
    """
    is_multi_valor = False
    try:
        if seed is not None:
            random.seed(seed)
        
        # Gera chave única para cache
        questao_id = questao_base.get('id', 'N/A')
        cache_key = f"variante_{questao_id}_{seed}"
        
        # Tenta obter do cache
        cached_variante = calculation_cache.get(cache_key)
        if cached_variante is not None:
            print(f"   💾 Variante em cache - Questão {questao_id}")
            return cached_variante
        
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
        
        # Limpa contexto
        for key in ['random', 'math', 'np', 'cmath', 'sp', '__builtins__']:
            if key in contexto: del contexto[key]

        enunciado_template = questao_base.get("enunciado", "")
        contexto_formatado = contexto.copy()

        # Processa placeholders com unidades
        placeholders = re.findall(r'\{(\w+)\}(?:\s*)(\S+)\b', enunciado_template)
        for var_name, potential_unit_text in placeholders:
            if var_name in contexto_formatado and isinstance(contexto_formatado[var_name], (int, float)) and len(potential_unit_text) > 1:
                from .utils import PREFIX_DIVISORS, VALID_BASE_UNITS
                prefix = potential_unit_text[0]
                base_unit = potential_unit_text[1:]
                
                if prefix in PREFIX_DIVISORS and base_unit in VALID_BASE_UNITS:
                    original_value = float(contexto_formatado[var_name])
                    divisor = PREFIX_DIVISORS[prefix]
                    converted_value = original_value / divisor
                    contexto_formatado[var_name] = int(converted_value) if converted_value == int(converted_value) else converted_value

        # Arredonda floats para exibição limpa
        for key, value in contexto_formatado.items():
            if isinstance(value, float):
                rounded_value = round(value, 2)
                if rounded_value == int(rounded_value):
                    contexto_formatado[key] = int(rounded_value)
                else:
                    contexto_formatado[key] = rounded_value

        enunciado_final = enunciado_template.format(**contexto_formatado)
        enunciado_final = re.sub(r'(\d+)\.(\d+)', r'\1,\2', enunciado_final)
        
        alternativas_valores = []
        resposta_valor = None

        if formato_questao == "Múltipla Escolha":
            if questao_base.get("gerar_alternativas_auto"):
                # Modo 1: Respostas múltiplas
                if isinstance(resposta_valor_calculado, dict) and "valores" in resposta_valor_calculado and "formato_texto" in resposta_valor_calculado:                   
                    is_multi_valor = True
                    
                    # Importação local para evitar circularidade
                    from .memory_optimizer import _gerar_pool_combinatorio
                    pool_de_tuplas = _gerar_pool_combinatorio(questao_base, params, contexto)

                    if not pool_de_tuplas:
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
                        return None
                    if any(abs(v) < 1e-9 for v in resposta_correta_dict_numerico.values() if isinstance(v, (int, float))):
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
                    
                # Modo 2: Resposta única
                elif isinstance(resposta_valor_calculado, (int, float)):
                    # Importação local para evitar circularidade
                    from .memory_optimizer import _gerar_pool_combinatorio
                    pool_numerico = _gerar_pool_combinatorio(questao_base, params, contexto)
                    
                    if pool_numerico is None:
                        print(f"AVISO: A questão ID {questao_base.get('id', 'N/A')} não é do tipo combinatório. Questão descartada.")
                        return None

                    pool_de_textos = set()
                    for valor_num in pool_numerico:
                        if not permitir_negativos and valor_num < 0:
                            continue
                        texto_formatado = formatar_unidade(valor_num, unidade)
                        if abs(valor_num) < 1e-15:
                            continue
                        pool_de_textos.add(texto_formatado)

                    if len(pool_de_textos) < num_alternativas:
                        print(f"FALHA: A questão ID {questao_base.get('id', 'N/A')} não gerou alternativas suficientes.")
                        return None

                    resposta_correta_num = resposta_valor_calculado
                    
                    if not permitir_negativos and resposta_correta_num < 0:
                        print(f"FALHA: Resposta correta negativa não permitida para ID {questao_base.get('id', 'N/A')}.")
                        return None

                    resposta_correta_texto = formatar_unidade(resposta_correta_num, unidade)

                    if resposta_correta_texto.strip().startswith('0'):
                        print(f"FALHA: Resposta correta zero não permitida para ID {questao_base.get('id', 'N/A')}.")
                        return None
                    
                    pool_de_textos.add(resposta_correta_texto)
                    if len(pool_de_textos) < num_alternativas:
                        print(f"FALHA: Pool insuficiente para ID {questao_base.get('id', 'N/A')}.")
                        return None
                    
                    max_pool_size = 30
                    if len(pool_de_textos) > max_pool_size:
                        pool_list = list(pool_de_textos)
                        if resposta_correta_texto in pool_list:
                            pool_list.remove(resposta_correta_texto)
                        pool_list_limited = random.sample(pool_list, max_pool_size - 1)
                        pool_de_textos = set(pool_list_limited) | {resposta_correta_texto}

                    pool_sem_resposta = set(pool_de_textos)
                    pool_sem_resposta.discard(resposta_correta_texto)
                    
                    distratores = random.sample(list(pool_sem_resposta), num_alternativas - 1)
                    
                    resposta_valor = resposta_correta_texto
                    alternativas_valores = [resposta_valor] + distratores
                
            else:
                # Modo 3: Alternativas manuais
                contexto_formatacao = {}
                if questao_base.get("parametros"):
                    params = questao_base.get("parametros", "")
                    temp_context = _get_math_context()
                    try:
                        exec(params, temp_context)
                        contexto_formatacao = temp_context
                    except Exception as e:
                        print(f"AVISO: Erro ao executar parâmetros para formatação do MODO 3 na ID {questao_base.get('id')}: {e}")
                
                alternativas_valores = []
                resposta_valor = None
                
                letras_base = ["a", "b", "c", "d", "e"]
                
                for letra in letras_base[:num_alternativas]:
                    alt_base = questao_base.get(f"alternativa_{letra}")
                    if alt_base:
                        try:
                            alternativas_valores.append(alt_base.format(**contexto_formatacao))
                        except KeyError as e:
                            print(f"AVISO: Erro de formatação na alternativa '{letra}': Variável {e} não encontrada.")
                            alternativas_valores.append(alt_base)
                
                resposta_letra = questao_base.get("resposta_correta", "?").lower()
                alt_correta_texto = questao_base.get(f"alternativa_{resposta_letra}")
                
                if alt_correta_texto:
                    try:
                        resposta_valor = alt_correta_texto.format(**contexto_formatacao)
                    except KeyError as e:
                        print(f"AVISO: Erro de formatação na resposta correta: Variável {e} não encontrada.")
                        resposta_valor = alt_correta_texto
                else:
                    print(f"AVISO: 'resposta_correta' ('{resposta_letra}') é inválida.")
        
        elif formato_questao == "Verdadeiro ou Falso":
            resposta_valor = resposta_valor_calculado
            if resposta_valor not in ["Verdadeiro", "Falso"] and resposta_valor is not None:
                resposta_valor = resposta_valor.format(**contexto)

    except KeyError as e:
        id_questao = questao_base.get('id', 'N/A')
        variavel_faltante = str(e).strip("'")
        aviso = f"AVISO: Erro de formatação na questão ID {id_questao}: Variável {{{variavel_faltante}}} não definida."
        print(aviso)
        return None
    except Exception as e:
        id_questao = questao_base.get('id', 'N/A')
        aviso = f"AVISO: Erro inesperado ao gerar a questão ID {id_questao}: {e}"
        print(aviso)
        import traceback
        traceback.print_exc()
        return None

    # Processa imagem
    imagem_path = questao_base.get("imagem", "")
    if imagem_path:
        imagem_path = imagem_path.replace('\\', '/')
        if not os.path.exists(imagem_path):
            print(f"⚠️ AVISO: Imagem não encontrada - {imagem_path}")
            imagem_path = ""
    
    largura_imagem = questao_base.get("imagem_largura_percentual") or 50
    
    variante_final = { 
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

    calculation_cache.set(cache_key, variante_final)
    
    return variante_final


def _gerar_gabarito_distribuido(num_questoes):
    """Gera gabarito com distribuição balanceada de respostas"""
    letras = ["A", "B", "C", "D", "E"]
    gabarito = []
    contagem = Counter()
    
    for _ in range(num_questoes):
        letras_ordenadas = sorted(letras, key=lambda l: contagem[l])
        letra_escolhida = letras_ordenadas[0]
        gabarito.append(letra_escolhida)
        contagem[letra_escolhida] += 1
    
    random.shuffle(gabarito)
    return gabarito


def _rotacionar_letra(letra, rotacao):
    """Rotaciona letra do gabarito entre versões"""
    letras = ["A", "B", "C", "D", "E"]
    if letra not in letras:
        return letra
    idx_original = letras.index(letra)
    idx_novo = (idx_original + rotacao) % len(letras)
    return letras[idx_novo]


def gerar_versoes_prova(questoes_base, num_versoes, opcoes_geracao, log_dialog=None):
    """
    Função principal - escolhe automaticamente entre paralelo e serial
    """
    # Importa funções de paralelismo quando necessário (evita circularidade)
    from .parallel_engine import gerar_versoes_prova_paralelo, gerar_versoes_prova_serial, _deve_usar_paralelismo
    
    # Inicia nova geração de cache
    nome_prova = opcoes_geracao.get('nome_prova', 'prova_geral')
    iniciar_nova_geracao_cache(f"prova_{nome_prova}")
    
    if log_dialog:
        log_dialog.append_log(f"🔄 Gerando {num_versoes} versão(ões)...")
        log_dialog.append_log(f"   {len(questoes_base)} questões de base")
    
    # Decide estratégia
    usar_paralelismo = _deve_usar_paralelismo(questoes_base, num_versoes)
    
    if usar_paralelismo:
        versoes_finais = gerar_versoes_prova_paralelo(questoes_base, num_versoes, opcoes_geracao)
        # Fallback se paralelismo falhar
        if versoes_finais is None:
            if log_dialog:
                log_dialog.append_log("⚠️  Fallback para serial...")
            versoes_finais = gerar_versoes_prova_serial(questoes_base, num_versoes, opcoes_geracao)
    else:
        versoes_finais = gerar_versoes_prova_serial(questoes_base, num_versoes, opcoes_geracao)
    
    # Estatísticas
    if log_dialog:
        print_cache_stats_to_log(log_dialog)
    else:
        from .cache_manager import finalizar_geracao_com_statistics
        finalizar_geracao_com_statistics()
    
    return versoes_finais


def gerar_cardapio_questoes(caminho_salvar_pdf, disciplina_id=None, tema=None, log_dialog=None):
    """
    Orquestra a criação do PDF do cardápio
    """
    from database import obter_todas_questoes_para_cardapio, obter_disciplina_nome_por_id
    import gerador_pdf
    
    def log_message(message):
        """Helper local para log"""
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
            # Lógica de tentativas
            variante = None
            numero_de_tentativas = 100

            for tentativa in range(numero_de_tentativas):
                seed_da_tentativa = questao_base['id'] + tentativa
                variante_tentativa = _gerar_variante_questao(questao_base, seed=seed_da_tentativa)
                
                if variante_tentativa:
                    variante = variante_tentativa
                    break

            if variante:
                if variante.get("formato_questao") == "Múltipla Escolha":
                    letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    alternativas_dict = {}
                    valores_ordenados = sorted(variante.get("alternativas_valores", []))
                    for i, valor in enumerate(valores_ordenados):
                        alternativas_dict[letras[i]] = valor
                    variante['alternativas'] = alternativas_dict

                variante['id_base'] = questao_base['id']
                variante['ativa'] = questao_base['ativa']
                variante['disciplina_id'] = questao_base['disciplina_id']
                questoes_geradas.append(variante)
            else:
                log_message(f"AVISO: Questão ID {questao_base['id']} foi descartada do cardápio após {numero_de_tentativas} tentativas.")

        log_message(f"Geradas {len(questoes_geradas)} variantes para o PDF.")

        contexto_extra = { "obter_disciplina_nome_por_id": obter_disciplina_nome_por_id }
        template_path = 'modelo_cardapio.tex'
        
        gerador_pdf.gerar_pdf_cardapio(
            questoes_geradas, caminho_salvar_pdf, template_path, contexto_extra, log_dialog
        )
        
        log_message("Cardápio de questões gerado com sucesso!")

        if log_dialog:
            print_cache_stats_to_log(log_dialog)
        else:
            from .cache_manager import finalizar_geracao_com_statistics
            finalizar_geracao_com_statistics()

        return True, "Cardápio gerado com sucesso!"

    except Exception as e:
        log_message(f"ERRO ao gerar cardápio: {e}")
        return False, f"Ocorreu um erro: {e}"