"""
Métrica FG - Força Geral (versão expandida — FBref + WhoScored)

Avalia a força intrínseca de um time com base em estatísticas da temporada.

Estrutura (3 sub‑métricas mantidas):
- Ataque: gols, finalizações no alvo, conversão, escanteios, chutes totais (🆕)
- Defesa: gols sofridos, finalizações sofridas, total de chutes sofridos,
          escanteios contra, desarmes, interceptações (🆕)
- Meio: posse, precisão de passes, passes por jogo, faltas cometidas,
        cartões amarelos, passes curtos (🆕), bolas longas (🆕 invertido)

Indicadores com "menor é melhor" são invertidos durante a normalização.
Se algum indicador não estiver disponível, é simplesmente ignorado.
A FG é a média simples das sub‑métricas ativas, escala 0–100.
"""

from typing import Dict, Optional
from src.utils import (
    normalizar_indicador,
    atualizacao_bayesiana,
    media_ativos,
    PRIOR_PADRAO,
    ALPHA_PADRAO,
)

# ----------------------------------------------------------
# Indicadores a inverter (menor é melhor)
# ----------------------------------------------------------
INDICADORES_INVERTIDOS = {
    'GS', 'FAS', 'TC', 'ECc',   # defesa
    'FC', 'CA',                  # disciplina
    'LongBall',                  # bolas longas = menos dominante 🆕
}

# ----------------------------------------------------------
# Mapas de indicadores por sub‑métrica
# ----------------------------------------------------------
INDICADORES_ATAQUE = {
    'Gols/jogo':             'GM',
    'Finalizações alvo/jogo': 'FA',
    'Conversão (%)':         'Conv',
    'Escanteios a favor/jogo': 'ECa',
    'Chutes totais/jogo':    'Shots',  # 🆕 WhoScored
}

INDICADORES_DEFESA = {
    'Gols sofridos/jogo':               'GS',
    'Finalizações alvo sofridas/jogo':  'FAS',
    'Total chutes sofridos/jogo':       'TC',
    'Escanteios contra/jogo':           'ECc',
    'Desarmes/jogo':                    'Des',
    'Interceptações/jogo':              'Int',  # 🆕 FBref/WhoScored
}

INDICADORES_MEIO = {
    'Posse de bola (%)':      'Posse',
    'Precisão passes (%)':    'P%',
    'Passes/jogo':            'PP',
    'Faltas cometidas/jogo':  'FC',
    'Cartões amarelos/jogo':  'CA',
    'Passes curtos/jogo':     'ShortPass',  # 🆕 WhoScored
    'Bolas longas/jogo':      'LongBall',   # 🆕 WhoScored (invertido)
}


# ----------------------------------------------------------
# Funções internas da FG
# ----------------------------------------------------------
def _calcular_indicador(valor_time: Optional[float],
                        media_liga: float,
                        n_jogos: int,
                        codigo_indicador: str,
                        alpha: float = ALPHA_PADRAO) -> Optional[float]:
    """Calcula a nota bayesiana de um indicador individual."""
    if valor_time is None:
        return None

    menor_melhor = codigo_indicador in INDICADORES_INVERTIDOS
    bruto = normalizar_indicador(valor_time, media_liga, menor_melhor)
    posterior = atualizacao_bayesiana(PRIOR_PADRAO, bruto, n_jogos, alpha)
    return posterior


def _calcular_submetrica(dados_time: Dict[str, float],
                         medias_liga: Dict[str, float],
                         n_jogos: int,
                         mapa_indicadores: Dict[str, str],
                         alpha: float = ALPHA_PADRAO) -> Optional[float]:
    """Calcula a nota de uma sub‑métrica agregando seus indicadores disponíveis."""
    valores = []
    for chave, codigo in mapa_indicadores.items():
        valor_time = dados_time.get(codigo)
        media_liga = medias_liga.get(codigo, 0.0)
        ind = _calcular_indicador(valor_time, media_liga, n_jogos, codigo, alpha)
        if ind is not None:
            valores.append(ind)
    return media_ativos(valores)


# ----------------------------------------------------------
# Função principal
# ----------------------------------------------------------
def calcular_fg(dados_time: Dict[str, float],
                medias_liga: Dict[str, float],
                n_jogos: int,
                incluir_ataque: bool = True,
                incluir_defesa: bool = True,
                incluir_meio: bool = True,
                alpha: float = ALPHA_PADRAO) -> float:
    """
    Calcula a Força Geral (FG) de um time.

    Parâmetros:
        dados_time: dicionário com as médias por jogo do time.
        medias_liga: dicionário com as médias por jogo da liga.
        n_jogos: número de partidas já disputadas pelo time.
        incluir_*: flags para incluir cada sub‑métrica.
        alpha: peso do prior bayesiano.

    Retorna:
        float entre 0 e 100 representando a força geral.
    """
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
