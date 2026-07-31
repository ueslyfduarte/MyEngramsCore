"""
Métrica CPP - Confronto por Prateleira

Avalia o desempenho histórico de uma equipe contra adversários da mesma
prateleira que o oponente do próximo jogo.

- Se houver pelo menos N_MIN jogos, usa o aproveitamento real (0–100).
- Caso contrário, combina o pouco histórico com a odd fornecida manualmente,
  usando o parâmetro ALPHA_CPP.
"""

# Parâmetros do método (não são dados fictícios)
N_MIN = 3        # número mínimo de jogos para confiar apenas no histórico
ALPHA_CPP = 3.0  # peso da odd na mistura quando n < N_MIN


def _aproveitamento(pontos: int, jogos: int) -> float:
    """Retorna o aproveitamento percentual (0–100)."""
    if jogos == 0:
        return 0.0
    return (pontos / (3 * jogos)) * 100


def calcular_cpp(pontos: int, jogos: int, odd: float,
                 n_min: int = N_MIN, alpha: float = ALPHA_CPP) -> float:
    """
    Calcula o CPP de um time contra a prateleira do adversário.

    Parâmetros:
        pontos: total de pontos conquistados nos jogos contra a prateleira alvo.
        jogos: número de jogos contra essa prateleira.
        odd: odd de vitória do time no próximo jogo (1X2).
        n_min: jogos mínimos para usar só histórico.
        alpha: peso da odd na mistura.

    Retorna:
        float entre 0 e 100.
    """
    if jogos >= n_min:
        return _aproveitamento(pontos, jogos)

    # Mistura entre histórico real e probabilidade implícita da odd
    apro = _aproveitamento(pontos, jogos)
    prob_odd = (1.0 / odd) * 100.0

    if jogos == 0:
        return prob_odd

    # Média ponderada: histórico (peso jogos) + odd (peso alpha)
    return (jogos * apro + alpha * prob_odd) / (jogos + alpha)
