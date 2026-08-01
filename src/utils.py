"""
Utilitários compartilhados entre os pilares do método.
"""
from typing import List, Optional

LIMITE_INFERIOR = 45.0
LIMITE_SUPERIOR = 100.0
PRIOR_PADRAO = 50.0
ALPHA_PADRAO = 5

def normalizar_indicador(valor_time: float, media_liga: float) -> float:
    if media_liga == 0:
        return PRIOR_PADRAO
    return (valor_time / media_liga) * 50.0

def atualizacao_bayesiana(prior: float, bruto: float, n_jogos: int,
                          alpha: float = ALPHA_PADRAO) -> float:
    return (alpha * prior + n_jogos * bruto) / (alpha + n_jogos)

def truncar(valor: float) -> float:
    return max(LIMITE_INFERIOR, min(LIMITE_SUPERIOR, valor))

def media_ativos(valores: List[Optional[float]]) -> Optional[float]:
    validos = [v for v in valores if v is not None]
    if not validos:
        return None
    return sum(validos) / len(validos)
