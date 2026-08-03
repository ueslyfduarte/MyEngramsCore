"""
Métrica FG v2 — Força Geral (versão automática com FBref)

Avalia a força intrínseca de um time com base em estatísticas do FBref.

Estrutura (4 sub‑métricas):
- Ataque: gols, xG, finalizações no alvo, chutes totais, escanteios.
- Defesa: gols sofridos, xG contra, finalizações sofridas, interceptações, desarmes.
- Meio: posse, passes progressivos, precisão de passes, faltas, cartões.
- Intensidade: pressões, pressões bem‑sucedidas, bolas recuperadas, desarmes+interceptações.

Indicadores com "menor é melhor" são invertidos durante a normalização.
Se algum indicador não estiver disponível, é simplesmente ignorado.
A FG é a média ponderada das sub‑métricas ativas, escala 0–100.
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
    'GS', 'xGA', 'FAS', 'TC', 'ECc',   # defesa
    'FC', 'CA', 'Err',                   # disciplina / erros
}

# ----------------------------------------------------------
# Pesos das sub‑métricas
# ----------------------------------------------------------
PESOS_SUBMETRICAS = {
    'ataque': 0.25,
    'defesa': 0.25,
    'meio': 0.25,
    'intensidade': 0.25,
}

# ----------------------------------------------------------
# Mapas de indicadores por sub‑métrica
# ----------------------------------------------------------
INDICADORES_ATAQUE = {
    'Gols/jogo':                'GM',
    'xG/jogo':                  'xG',
    'Finalizações alvo/jogo':   'FA',
    'Chutes totais/jogo':       'Sh',
    'Escanteios a favor/jogo':  'ECa',
}

INDICADORES_DEFESA = {
    'Gols sofridos/jogo':               'GS',
    'xG contra/jogo':                   'xGA',
    'Finalizações alvo sofridas/jogo':  'FAS',
    'Interceptações/jogo':              'Int',
    'Desarmes/jogo':                    'Des',
}

INDICADORES_MEIO = {
    'Posse de bola (%)':          'Posse',
    'Passes progressivos/jogo':   'PrgP',
    'Precisão passes (%)':        'Cmp%',
    'Faltas cometidas/jogo':      'FC',
    'Cartões amarelos/jogo':      'CA',
}

INDICADORES_INTENSIDADE = {
    'Pressões/jogo':                      'Press',
    'Pressões bem‑sucedidas (%)':         'Press%',
    'Bolas recuperadas/jogo':             'Recov',
    'Desarmes + Interceptações/jogo':     'Tkl+Int',
}


# ----------------------------------------------------------
# Funções internas
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
def calcular_fg_v2(dados_time: Dict[str, float],
                   medias_liga: Dict[str, float],
                   n_jogos: int,
                   incluir_ataque: bool = True,
                   incluir_defesa: bool = True,
                   incluir_meio: bool = True,
                   incluir_intensidade: bool = True,
                   alpha: float = ALPHA_PADRAO,
                   pesos: Dict[str, float] = None) -> float:
    """
    Calcula a Força Geral (FG) v2 de um time.

    Parâmetros:
        dados_time: dicionário com as médias por jogo do time.
                    Ex: {'GM': 1.8, 'xG': 1.6, 'PrgP': 45.2, ...}
        medias_liga: dicionário com as médias por jogo da liga (mesmas chaves).
        n_jogos: número de partidas já disputadas pelo time.
        incluir_*: flags para incluir cada sub‑métrica.
        alpha: peso do prior bayesiano.
        pesos: dicionário opcional com pesos das sub‑métricas.
               Padrão: {'ataque': 0.25, 'defesa': 0.25, 'meio': 0.25, 'intensidade': 0.25}

    Retorna:
        float entre 0 e 100 representando a força geral.
    """
    if pesos is None:
        pesos = PESOS_SUBMETRICAS

    sub_notas = []
    pesos_ativos = []

    if incluir_ataque:
        atq = _calcular_submetrica(dados_time, medias_liga, n_jogos,
                                   INDICADORES_ATAQUE, alpha)
        if atq is not None:
            sub_notas.append(atq)
            pesos_ativos.append(pesos.get('ataque', 0.25))

    if incluir_defesa:
        defe = _calcular_submetrica(dados_time, medias_liga, n_jogos,
                                    INDICADORES_DEFESA, alpha)
        if defe is not None:
            sub_notas.append(defe)
            pesos_ativos.append(pesos.get('defesa', 0.25))

    if incluir_meio:
        mei = _calcular_submetrica(dados_time, medias_liga, n_jogos,
                                   INDICADORES_MEIO, alpha)
        if mei is not None:
            sub_notas.append(mei)
            pesos_ativos.append(pesos.get('meio', 0.25))

    if incluir_intensidade:
        intens = _calcular_submetrica(dados_time, medias_liga, n_jogos,
                                      INDICADORES_INTENSIDADE, alpha)
        if intens is not None:
            sub_notas.append(intens)
            pesos_ativos.append(pesos.get('intensidade', 0.25))

    if not sub_notas:
        return PRIOR_PADRAO

    # Média ponderada pelas sub‑métricas disponíveis
    soma_pesos = sum(pesos_ativos)
    if soma_pesos == 0:
        return PRIOR_PADRAO

    # Normalizar pesos
    pesos_norm = [p / soma_pesos for p in pesos_ativos]

    return sum(n * p for n, p in zip(sub_notas, pesos_norm))


# ----------------------------------------------------------
# Função de compatibilidade (mesma assinatura do fg.py atual)
# ----------------------------------------------------------
def calcular_fg(dados_time: Dict[str, float],
                medias_liga: Dict[str, float],
                n_jogos: int,
                incluir_ataque: bool = True,
                incluir_defesa: bool = True,
                incluir_meio: bool = True,
                alpha: float = ALPHA_PADRAO) -> float:
    """
    Wrapper compatível com a assinatura do fg.py atual.
    Redireciona para calcular_fg_v2 sem a sub‑métrica de intensidade.
    """
    return calcular_fg_v2(
        dados_time, medias_liga, n_jogos,
        incluir_ataque=incluir_ataque,
        incluir_defesa=incluir_defesa,
        incluir_meio=incluir_meio,
        incluir_intensidade=False,  # desativado para compatibilidade
        alpha=alpha
    )
