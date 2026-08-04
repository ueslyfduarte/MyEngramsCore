"""
Métrica Estilo v3 (Dominância Ofensiva — WhoScored)

Mede o perfil tático do time: do totalmente reativo (0) ao extremamente
dominante (100), com base em:
- Posse de bola (%)
- Chutes por jogo
- Cruzamentos por jogo (jogo pelas pontas)
- Bolas enfiadas por jogo (jogo vertical)
- Passes curtos por jogo (construção paciente)
- Bolas longas por jogo (jogo direto — invertido)
- % Terço adversário (presença ofensiva)

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
    'Posse': 'Poss',
    'Chutes': 'Shots',
    'Cruzamentos': 'Crs',
    'Bolas Enfiadas': 'ThrBall',
    'Passes Curtos': 'ShortPass',
    'Bolas Longas': 'LongBall',
    'Terço Adversário': 'AttThird',
}

# Indicadores que são "menor é melhor" (invertidos na normalização)
INDICADORES_INVERTIDOS = {'LongBall'}  # Time que dá chutão é menos dominante


def _calcular_indicador(valor_time: Optional[float],
                        media_liga: float,
                        n_jogos: int,
                        codigo: str,
                        alpha: float = ALPHA_PADRAO) -> Optional[float]:
    if valor_time is None:
        return None
    menor_melhor = codigo in INDICADORES_INVERTIDOS
    bruto = normalizar_indicador(valor_time, media_liga, menor_melhor=menor_melhor)
    return atualizacao_bayesiana(PRIOR_PADRAO, bruto, n_jogos, alpha)


def calcular_estilo(dados_time: Dict[str, float],
                    medias_liga: Dict[str, float],
                    n_jogos: int,
                    alpha: float = ALPHA_PADRAO) -> float:
    """
    Calcula a nota de dominância ofensiva (estilo) do time.

    Parâmetros:
        dados_time: dicionário com as médias por jogo.
                    Ex: {'Poss': 55.0, 'Shots': 14.5, 'Crs': 18.0, 
                         'ThrBall': 1.2, 'ShortPass': 420, 'LongBall': 45,
                         'AttThird': 30.0}
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
        ind = _calcular_indicador(valor_time, media_liga, n_jogos, cod)
        if ind is not None:
            valores.append(ind)

    if not valores:
        return PRIOR_PADRAO

    return sum(valores) / len(valores)
