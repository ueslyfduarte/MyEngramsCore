"""
Métrica Estilo (Dominância Ofensiva)

Mede o perfil tático do time: do totalmente reativo (0) ao extremamente
dominante (100), com base em posse, finalizações no alvo e escanteios.
Indicadores normalizados em relação à média da liga, com atualização bayesiana.
"""

from typing import Dict, Optional
from src.utils import (
    normalizar_indicador,
    atualizacao_bayesiana,
    PRIOR_PADRAO,
    ALPHA_PADRAO,
)

INDICADORES_ESTILO = {
    'Posse': 'Posse',
    'FA': 'FA',
    'ECa': 'ECa',
}


def _calcular_indicador(valor_time: Optional[float],
                        media_liga: float,
                        n_jogos: int,
                        alpha: float = ALPHA_PADRAO) -> Optional[float]:
    if valor_time is None:
        return None
    bruto = normalizar_indicador(valor_time, media_liga, menor_melhor=False)
    return atualizacao_bayesiana(PRIOR_PADRAO, bruto, n_jogos, alpha)


def calcular_estilo(dados_time: Dict[str, float],
                    medias_liga: Dict[str, float],
                    n_jogos: int,
                    alpha: float = ALPHA_PADRAO) -> float:
    """
    Calcula a nota de dominância ofensiva (estilo) do time.

    Parâmetros:
        dados_time: dicionário com as médias por jogo.
                    Ex: {'Posse': 55.0, 'FA': 5.2, 'ECa': 6.1}
        medias_liga: médias da liga (mesmas chaves).
        n_jogos: partidas já disputadas.
        alpha: peso do prior bayesiano.

    Retorna:
        float entre 0 e 100 (quanto maior, mais dominante).
    """
    valores = []
    for nome, cod in INDICADORES_ESTILO.items():
        valor_time = dados_time.get(cod)
        media_liga = medias_liga.get(cod, 0.0)
        ind = _calcular_indicador(valor_time, media_liga, n_jogos, alpha)
        if ind is not None:
            valores.append(ind)

    if not valores:
        return PRIOR_PADRAO

    return sum(valores) / len(valores)
