"""
Métrica FG - Força Geral

Avalia a força intrínseca de uma equipe com base em estatísticas da temporada,
agregando sub-métricas de Ataque, Defesa e Meio de Campo.

Cada sub-métrica é composta por indicadores normalizados em relação à média
da liga. Se um indicador não estiver disponível, é ignorado.
A FG é a média simples das sub-métricas ativas, escala [45,100].
"""

from typing import Dict, Optional
from src.utils import (
    normalizar_indicador,
    atualizacao_bayesiana,
    truncar,
    media_ativos,
    PRIOR_PADRAO,
    ALPHA_PADRAO
)

# ----------------------------------------------------------
# Configuração dos indicadores por sub-métrica
# ----------------------------------------------------------
INDICADORES_ATAQUE = {
    'Gols marcados':        'GM',
    'Finalizações no alvo': 'FA',
    'xG':                   'xG',
    'Conversão':            'Conv',
    'Grandes chances':      'GC',
}

INDICADORES_DEFESA = {
    'Gols sofridos':                'GS',
    'xG contra':                    'xGA',
    'Finalizações no alvo sofridas': 'FAS',
    'Chutes bloqueados':            'CB',
    'Duelos aéreos defensivos':     'DA',
}

INDICADORES_MEIO = {
    'Posse de bola (%)':            'Posse',
    'Passes certos no terço central': 'PTC',
    'Passes progressivos':          'PP',
    'Duelos ganhos no meio':        'DGM',
    'Assistências esperadas':       'xA',
}


def _calcular_indicador(valor_time: Optional[float],
                        media_liga: float,
                        n_jogos: int,
                        alpha: float = ALPHA_PADRAO) -> Optional[float]:
    if valor_time is None:
        return None
    bruto = normalizar_indicador(valor_time, media_liga)
    posterior = atualizacao_bayesiana(PRIOR_PADRAO, bruto, n_jogos, alpha)
    return truncar(posterior)


def _calcular_submetrica(dados_time: Dict[str, float],
                         medias_liga: Dict[str, float],
                         n_jogos: int,
                         mapa_indicadores: Dict[str, str],
                         alpha: float = ALPHA_PADRAO) -> Optional[float]:
    valores = []
    for chave_dado in mapa_indicadores.values():
        valor_time = dados_time.get(chave_dado)
        media_liga = medias_liga.get(chave_dado, 0.0)
        ind = _calcular_indicador(valor_time, media_liga, n_jogos, alpha)
        valores.append(ind)
    return media_ativos(valores)


def calcular_fg(dados_time: Dict[str, float],
                medias_liga: Dict[str, float],
                n_jogos: int,
                incluir_ataque: bool = True,
                incluir_defesa: bool = True,
                incluir_meio: bool = True,
                alpha: float = ALPHA_PADRAO) -> float:
    sub_notas = []

    if incluir_ataque:
        atq = _calcular_submetrica(dados_time, medias_liga, n_jogos,
                                   INDICADORES_ATAQUE, alpha)
        if atq is not None:
            sub_notas.append(atq)

    if incluir_defesa:
        defe = _calcular_submetrica(dados_time, medias_liga, n_jogos,
                                    INDICADORES_DEFESA, alpha)
        if defe is not None:
            sub_notas.append(defe)

    if incluir_meio:
        mei = _calcular_submetrica(dados_time, medias_liga, n_jogos,
                                   INDICADORES_MEIO, alpha)
        if mei is not None:
            sub_notas.append(mei)

    if not sub_notas:
        return PRIOR_PADRAO

    return sum(sub_notas) / len(sub_notas)
