"""
Utilitários compartilhados entre os pilares do método.
"""

from typing import List, Optional

# Limites universais das escalas
LIMITE_INFERIOR = 45.0   # usado apenas pela FG
LIMITE_SUPERIOR = 100.0
PRIOR_PADRAO = 50.0      # ponto de partida bayesiano (média da liga)
ALPHA_PADRAO = 5         # peso do prior em jogos (parâmetro do método)


def normalizar_indicador(valor_time: float, media_liga: float) -> float:
    """Normaliza um indicador em relação à média da liga: (time / liga) * 50."""
    if media_liga == 0:
        return PRIOR_PADRAO
    return (valor_time / media_liga) * 50.0


def atualizacao_bayesiana(prior: float, bruto: float, n_jogos: int,
                          alpha: float = ALPHA_PADRAO) -> float:
    """Combina prior com valor bruto ponderado pelo número de jogos."""
    return (alpha * prior + n_jogos * bruto) / (alpha + n_jogos)


def truncar(valor: float) -> float:
    """Garante que o valor esteja no intervalo [45, 100]."""
    return max(LIMITE_INFERIOR, min(LIMITE_SUPERIOR, valor))


def media_ativos(valores: List[Optional[float]]) -> Optional[float]:
    """Calcula a média de uma lista de valores, ignorando None."""
    validos = [v for v in valores if v is not None]
    if not validos:
        return None
    return sum(validos) / len(validos)
