"""
Métrica MA - Momento Atual (v3)

Avalia a fase recente de um time combinando:
- Aproveitamento real nos últimos JANELA jogos (0-100).
- Expectativa de desempenho extraída das probabilidades justas (vitória + empate)
  do próximo jogo, convertida em aproveitamento esperado (0-100).

Se o time já disputou pelo menos N_MIN jogos na temporada, o MA é 100% baseado
no histórico recente. Caso contrário, faz uma média ponderada entre o real e o
esperado, com peso do histórico proporcional ao número de jogos já realizados.

Isso evita distorções de início de temporada e mantém o índice sempre entre 0 e 100.
"""

from typing import Tuple

# ----------------------------------------------------------
# Parâmetros configuráveis
# ----------------------------------------------------------
N_MIN = 6          # jogos totais na temporada para confiar só no histórico
ALPHA_MA = 3.0     # peso da odd na mistura (quanto maior, mais confiança na odd)
JANELA = 6         # número de jogos recentes considerados para o "momento"


def _aproveitamento(pontos: int, jogos: int) -> float:
    """Aproveitamento percentual (0-100). Retorna 0 se não houver jogos."""
    if jogos == 0:
        return 0.0
    return (pontos / (3 * jogos)) * 100


def _aproveitamento_esperado(prob_vitoria: float, prob_empate: float) -> float:
    """
    Converte probabilidades justas (0-1) em aproveitamento esperado (0-100).
    Fórmula: (p_vitória * 3 + p_empate * 1) / 3 * 100
    """
    if prob_vitoria + prob_empate > 1.0:
        raise ValueError("prob_vitoria + prob_empate > 1.0")
    return (prob_vitoria * 3 + prob_empate * 1) / 3 * 100


def calcular_ma(
    pontos_recentes: int,
    jogos_recentes: int,
    jogos_total_temporada: int,
    prob_vitoria: float,
    prob_empate: float,
    n_min: int = N_MIN,
    alpha: float = ALPHA_MA
) -> float:
    """
    Calcula o Momento Atual (MA).

    Parâmetros:
        pontos_recentes: pontos conquistados nos últimos JANELA jogos (ou menos, se
                         o time ainda não tiver esse número de partidas).
        jogos_recentes: quantos desses jogos realmente ocorreram (≤ JANELA).
        jogos_total_temporada: total de partidas que o time já fez na liga.
        prob_vitoria: probabilidade justa de vitória no próximo jogo (0-1).
        prob_empate: probabilidade justa de empate no próximo jogo (0-1).
        n_min: jogos totais mínimos para usar 100% histórico.
        alpha: peso da odd na mistura (usado apenas se jogos_total < n_min).

    Retorna:
        float entre 0 e 100.
    """
    # Se a temporada já tem jogos suficientes, usa só o desempenho recente
    if jogos_total_temporada >= n_min:
        return _aproveitamento(pontos_recentes, jogos_recentes)

    # Caso contrário, mistura histórico recente com expectativa da odd
    apro_real = _aproveitamento(pontos_recentes, jogos_recentes)
    apro_esp = _aproveitamento_esperado(prob_vitoria, prob_empate)

    if jogos_total_temporada == 0:
        return apro_esp

    # Média ponderada: peso do histórico = jogos_total, peso da odd = alpha
    peso_hist = jogos_total_temporada
    peso_odd = alpha
    ma = (peso_hist * apro_real + peso_odd * apro_esp) / (peso_hist + peso_odd)
    return ma
