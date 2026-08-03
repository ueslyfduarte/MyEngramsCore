"""
Métrica CPP v2 — Confronto por Prateleira (Automático)

Versão expandida para uso com coleta automática de dados (PC Linux).
Calcula o desempenho histórico contra TODAS as prateleiras e retorna
a nota específica para a prateleira do próximo adversário.

Diferente do cpp.py (manual), este módulo recebe um histórico completo
de jogos e calcula automaticamente os confrontos por prateleira.
"""

from typing import List, Dict, Optional

# ----------------------------------------------------------
# Parâmetros configuráveis
# ----------------------------------------------------------
N_MIN = 3          # jogos mínimos contra a prateleira para confiar no histórico
ALPHA_CPP = 3.0    # peso da odd na mistura quando há poucos jogos


def classificar_prateleira(posicao: int) -> str:
    """Retorna a prateleira com base na posição na tabela."""
    if posicao <= 3:
        return 'elite'
    elif posicao <= 7:
        return 'alta'
    elif posicao <= 13:
        return 'media'
    elif posicao <= 16:
        return 'baixa'
    else:
        return 'critica'


def construir_historico_prateleiras(
    resultados: List[Dict]
) -> Dict[str, Dict[str, int]]:
    """
    Constrói um dicionário com o desempenho do time contra cada prateleira.

    Parâmetros:
        resultados: lista de dicionários com:
            - 'adversario': nome do adversário
            - 'posicao_adversario': posição do adversário na tabela no momento do jogo
            - 'resultado': 'V', 'E' ou 'D'
            - 'gols_pro': gols marcados
            - 'gols_contra': gols sofridos

    Retorna:
        dict como:
        {
            'elite': {'pontos': 7, 'jogos': 4, 'v': 2, 'e': 1, 'd': 1, 'gp': 5, 'gc': 3},
            'alta': {...},
            ...
        }
    """
    historico = {
        'elite': {'pontos': 0, 'jogos': 0, 'v': 0, 'e': 0, 'd': 0, 'gp': 0, 'gc': 0},
        'alta': {'pontos': 0, 'jogos': 0, 'v': 0, 'e': 0, 'd': 0, 'gp': 0, 'gc': 0},
        'media': {'pontos': 0, 'jogos': 0, 'v': 0, 'e': 0, 'd': 0, 'gp': 0, 'gc': 0},
        'baixa': {'pontos': 0, 'jogos': 0, 'v': 0, 'e': 0, 'd': 0, 'gp': 0, 'gc': 0},
        'critica': {'pontos': 0, 'jogos': 0, 'v': 0, 'e': 0, 'd': 0, 'gp': 0, 'gc': 0},
    }

    for jogo in resultados:
        prat = classificar_prateleira(jogo['posicao_adversario'])
        historico[prat]['jogos'] += 1
        if jogo['resultado'] == 'V':
            historico[prat]['pontos'] += 3
            historico[prat]['v'] += 1
        elif jogo['resultado'] == 'E':
            historico[prat]['pontos'] += 1
            historico[prat]['e'] += 1
        else:
            historico[prat]['d'] += 1
        historico[prat]['gp'] += jogo['gols_pro']
        historico[prat]['gc'] += jogo['gols_contra']

    return historico


def _aproveitamento(pontos: int, jogos: int) -> float:
    """Aproveitamento percentual (0-100)."""
    if jogos == 0:
        return 0.0
    return (pontos / (3 * jogos)) * 100


def _aproveitamento_esperado(prob_vitoria: float, prob_empate: float) -> float:
    """Converte probabilidades em aproveitamento esperado (0-100)."""
    if prob_vitoria + prob_empate > 1.0:
        raise ValueError("prob_vitoria + prob_empate > 1.0")
    return (prob_vitoria * 3 + prob_empate * 1) / 3 * 100


def calcular_cpp_v2(
    historico: Dict[str, Dict[str, int]],
    prateleira_alvo: str,
    prob_vitoria: float,
    prob_empate: float,
    n_min: int = N_MIN,
    alpha: float = ALPHA_CPP
) -> float:
    """
    Calcula o CPP para uma prateleira específica.

    Parâmetros:
        historico: dicionário retornado por construir_historico_prateleiras()
        prateleira_alvo: prateleira do próximo adversário ('elite', 'alta', etc.)
        prob_vitoria: probabilidade justa de vitória (0-1)
        prob_empate: probabilidade justa de empate (0-1)
        n_min: jogos mínimos para confiar só no histórico
        alpha: peso da odd na mistura

    Retorna:
        float entre 0 e 100
    """
    dados = historico.get(prateleira_alvo, {'pontos': 0, 'jogos': 0})

    if dados['jogos'] >= n_min:
        return _aproveitamento(dados['pontos'], dados['jogos'])

    apro_real = _aproveitamento(dados['pontos'], dados['jogos'])
    apro_esp = _aproveitamento_esperado(prob_vitoria, prob_empate)

    if dados['jogos'] == 0:
        return apro_esp

    return (dados['jogos'] * apro_real + alpha * apro_esp) / (dados['jogos'] + alpha)


def obter_todos_cpp(
    historico: Dict[str, Dict[str, int]],
    prob_vitoria: float,
    prob_empate: float
) -> Dict[str, float]:
    """
    Retorna o CPP para TODAS as prateleiras de uma vez.

    Útil para exibir um resumo completo do desempenho do time.
    """
    return {
        prat: calcular_cpp_v2(historico, prat, prob_vitoria, prob_empate)
        for prat in ['elite', 'alta', 'media', 'baixa', 'critica']
    }
