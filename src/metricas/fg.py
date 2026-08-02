# fg.py (versão corrigida)
from typing import Dict, Optional
from utils import atualizacao_bayesiana, truncar, media_ativos, PRIOR_PADRAO, ALPHA_PADRAO

# Conjuntos de indicadores a serem invertidos (menor é melhor)
INDICADORES_INVERTIDOS = {'GS', 'xGA', 'FAS'}

# Mapas de indicadores (não alterados)
INDICADORES_ATAQUE = {
    'Gols marcados': 'GM',
    'Finalizações no alvo': 'FA',
    'xG': 'xG',
    'Conversão': 'Conv',
    'Grandes chances': 'GC',
}

INDICADORES_DEFESA = {
    'Gols sofridos': 'GS',
    'xG contra': 'xGA',
    'Finalizações no alvo sofridas': 'FAS',
    'Chutes bloqueados': 'CB',
    'Duelos aéreos defensivos': 'DA',
}

INDICADORES_MEIO = {
    'Posse de bola (%)': 'Posse',
    'Passes certos no terço central': 'PTC',
    'Passes progressivos': 'PP',
    'Duelos ganhos no meio': 'DGM',
    'Assistências esperadas': 'xA',
}


def normalizar_indicador(valor_time: float, media_liga: float, menor_melhor: bool = False) -> float:
    """Normaliza o indicador em relação à média da liga. Inverte se menor_melhor=True."""
    if media_liga == 0:
        return 50.0
    pct = (valor_time - media_liga) / media_liga
    if menor_melhor:
        pct = -pct
    # Limita a diferença percentual para não explodir
    pct = max(-1.0, min(1.0, pct))
    nota = 50.0 + pct * 50.0   # usando 50 como amplitude total para manter 0-100
    return nota


def _calcular_indicador(valor_time: Optional[float],
                        media_liga: float,
                        n_jogos: int,
                        codigo_indicador: str,
                        alpha: float = ALPHA_PADRAO) -> Optional[float]:
    if valor_time is None:
        return None
    menor_melhor = codigo_indicador in INDICADORES_INVERTIDOS
    bruto = normalizar_indicador(valor_time, media_liga, menor_melhor)
    posterior = atualizacao_bayesiana(PRIOR_PADRAO, bruto, n_jogos, alpha)
    return truncar(posterior)


def _calcular_submetrica(dados_time: Dict[str, float],
                         medias_liga: Dict[str, float],
                         n_jogos: int,
                         mapa_indicadores: Dict[str, str],
                         alpha: float = ALPHA_PADRAO) -> Optional[float]:
    valores = []
    for chave_dado, codigo in mapa_indicadores.items():
        valor_time = dados_time.get(codigo)
        media_liga = medias_liga.get(codigo, 0.0)
        ind = _calcular_indicador(valor_time, media_liga, n_jogos, codigo, alpha)
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
