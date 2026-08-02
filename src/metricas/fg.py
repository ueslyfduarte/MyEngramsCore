"""
Métrica FG - Força Geral (versão realista)

Avalia a força intrínseca de um time com base em estatísticas básicas da
temporada, disponíveis na maioria das plataformas de estatísticas.

Estrutura:
- Ataque: gols, finalizações no alvo, conversão, escanteios a favor.
- Defesa: gols sofridos, finalizações sofridas, total de chutes sofridos,
          escanteios contra, desarmes (ou duelos aéreos).
- Meio: posse, precisão de passes, passes por jogo, faltas cometidas,
        cartões amarelos.

Indicadores com "menor é melhor" são invertidos durante a normalização.
Se algum indicador não estiver disponível, é simplesmente ignorado.
A FG é a média simples das sub‑métricas ativas, escala 0–100.
"""

from typing import Dict, Optional

# ----------------------------------------------------------
# Constantes e utilitários
# ----------------------------------------------------------
PRIOR_PADRAO = 50.0       # valor inicial bayesiano
ALPHA_PADRAO = 5.0        # peso do prior (confiança no histórico)

# Indicadores a inverter (menor é melhor)
INDICADORES_INVERTIDOS = {'GS', 'FAS', 'TC', 'ECc', 'FC', 'CA'}

# Mapas de indicadores por sub‑métrica
INDICADORES_ATAQUE = {
    'Gols/jogo':             'GM',
    'Finalizações alvo/jogo': 'FA',
    'Conversão (%)':         'Conv',
    'Escanteios a favor/jogo': 'ECa',
}

INDICADORES_DEFESA = {
    'Gols sofridos/jogo':               'GS',
    'Finalizações alvo sofridas/jogo':  'FAS',
    'Total chutes sofridos/jogo':       'TC',
    'Escanteios contra/jogo':           'ECc',
    'Desarmes/jogo':                    'Des',   # ou 'DA' para duelos aéreos
}

INDICADORES_MEIO = {
    'Posse de bola (%)':      'Posse',
    'Precisão passes (%)':    'P%',
    'Passes/jogo':            'PP',
    'Faltas cometidas/jogo':  'FC',
    'Cartões amarelos/jogo':  'CA',
}


def normalizar_indicador(valor_time: float, media_liga: float,
                         menor_melhor: bool = False) -> float:
    """
    Normaliza um indicador em relação à média da liga.
    Se menor_melhor=True, a diferença é invertida.
    Retorna valor entre 0 e 100.
    """
    if media_liga == 0:
        return 50.0

    pct = (valor_time - media_liga) / media_liga
    if menor_melhor:
        pct = -pct

    # Limita a variação a ±100% para evitar notas extremas
    pct = max(-1.0, min(1.0, pct))
    nota = 50.0 + pct * 50.0
    return max(0.0, min(100.0, nota))


def atualizacao_bayesiana(prior: float, observacao: float,
                          n_jogos: int, alpha: float) -> float:
    """
    Combina o prior com a observação, ponderando pelo número de jogos.
    Quanto maior alpha, mais confiança no prior.
    """
    if n_jogos + alpha == 0:
        return prior
    return (alpha * prior + n_jogos * observacao) / (alpha + n_jogos)


def media_ativos(valores: list) -> Optional[float]:
    """Média dos valores não None. Retorna None se todos forem None."""
    validos = [v for v in valores if v is not None]
    return sum(validos) / len(validos) if validos else None


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
    return posterior  # já está entre 0 e 100


def _calcular_submetrica(dados_time: Dict[str, float],
                         medias_liga: Dict[str, float],
                         n_jogos: int,
                         mapa_indicadores: Dict[str, str],
                         alpha: float = ALPHA_PADRAO) -> Optional[float]:
    """
    Calcula a nota de uma sub‑métrica (Ataque, Defesa ou Meio)
    agregando seus indicadores disponíveis.
    Retorna None se nenhum indicador estiver disponível.
    """
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
                    Ex: {'GM': 1.8, 'FA': 5.2, 'Posse': 53.0, ...}
        medias_liga: dicionário com as médias por jogo da liga (mesmas chaves).
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
