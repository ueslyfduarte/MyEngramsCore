"""
Métrica FG - Força Geral

Avalia a força intrínseca de uma equipe com base em estatísticas da temporada,
agregando sub-métricas de Ataque, Defesa e Meio de Campo (e futuramente
Consistência e Resiliência).

Cada sub-métrica é composta por indicadores normalizados em relação à média
da liga (50 = média). Se um indicador não estiver disponível, é ignorado.
A FG é a média simples das sub-métricas ativas, com escala final [45,100].
"""

from typing import Dict, List, Optional

# Pesos do prior bayesiano (em número de jogos fictícios)
ALPHA_DEFAULT = 5

# Limites da escala
LIMITE_INFERIOR = 45.0
LIMITE_SUPERIOR = 100.0

# =========================================================
# FUNÇÕES GENÉRICAS
# =========================================================

def normalizar_indicador(valor_time: float, media_liga: float) -> float:
    """
    Normaliza um indicador em relação à média da liga.
    Escala base: (time / liga) * 50  ->  50 = média da liga.
    """
    if media_liga == 0:
        return 50.0  # evitar divisão por zero
    return (valor_time / media_liga) * 50.0


def atualizacao_bayesiana(prior: float, bruto: float, n_jogos: int,
                          alpha: float = ALPHA_DEFAULT) -> float:
    """Combina prior (50) e valor bruto observado, ponderado por n_jogos e alpha."""
    return (alpha * prior + n_jogos * bruto) / (alpha + n_jogos)


def truncar(valor: float) -> float:
    """Garante que o valor fique dentro dos limites [45, 100]."""
    return max(LIMITE_INFERIOR, min(LIMITE_SUPERIOR, valor))


def calcular_indicador(valor_time: Optional[float],
                       media_liga: float,
                       n_jogos: int,
                       alpha: float = ALPHA_DEFAULT) -> Optional[float]:
    """
    Calcula um indicador individual.
    Se valor_time for None, retorna None (indicador inativo).
    Caso contrário, normaliza, aplica bayesiano e trunca.
    """
    if valor_time is None:
        return None
    bruto = normalizar_indicador(valor_time, media_liga)
    posterior = atualizacao_bayesiana(50.0, bruto, n_jogos, alpha)
    return truncar(posterior)


def media_ativos(valores: List[float]) -> Optional[float]:
    """Calcula a média de uma lista de valores, ignorando None. Se todos None, retorna None."""
    validos = [v for v in valores if v is not None]
    if not validos:
        return None
    return sum(validos) / len(validos)


# =========================================================
# CONFIGURAÇÃO DOS INDICADORES POR SUB-MÉTRICA
# =========================================================

# Cada sub-métrica é um dict: chave do indicador -> chave usada nos dados de entrada
# As chaves dos dados devem corresponder aos nomes usados em `dados_time` e `medias_liga`.

INDICADORES_ATAQUE = {
    'Gols marcados':        'GM',
    'Finalizações no alvo': 'FA',
    'xG':                   'xG',
    'Conversão':            'Conv',
    'Grandes chances':      'GC',
}

INDICADORES_DEFESA = {
    'Gols sofridos':                'GS',
    'xG contra':                   'xGA',
    'Finalizações no alvo sofridas': 'FAS',
    'Chutes bloqueados':            'CB',
    'Duelos aéreos defensivos':     'DA',
}

INDICADORES_MEIO = {
    'Posse de bola':                'Posse',
    'Passes certos no terço central': 'PTC',
    'Passes progressivos':          'PP',
    'Duelos ganhos no meio':        'DGM',
    'Assistências esperadas':       'xA',
}

# =========================================================
# CÁLCULO DAS SUB-MÉTRICAS
# =========================================================

def calcular_submetrica(dados_time: Dict[str, float],
                        medias_liga: Dict[str, float],
                        n_jogos: int,
                        indicadores: Dict[str, str],
                        alpha: float = ALPHA_DEFAULT) -> Optional[float]:
    """
    Calcula o valor de uma sub-métrica (ex.: Ataque) com base nos indicadores ativos.

    Parâmetros:
        dados_time: dicionário com as estatísticas médias do time (chaves = nomes de dados)
        medias_liga: dicionário com as médias da liga (mesmas chaves)
        n_jogos: número de jogos disputados
        indicadores: mapa de {nome_do_indicador: chave_dado}
        alpha: peso do prior

    Retorna:
        Média truncada dos indicadores ativos, ou None se nenhum estiver disponível.
    """
    valores = []
    for nome, chave in indicadores.items():
        valor_time = dados_time.get(chave)  # None se não existir
        media_liga = medias_liga.get(chave, 0.0)
        ind = calcular_indicador(valor_time, media_liga, n_jogos, alpha)
        valores.append(ind)
    return media_ativos(valores)


# =========================================================
# CÁLCULO DA FORÇA GERAL (FG)
# =========================================================

def calcular_fg(dados_time: Dict[str, float],
                medias_liga: Dict[str, float],
                n_jogos: int,
                incluir_ataque: bool = True,
                incluir_defesa: bool = True,
                incluir_meio: bool = True,
                alpha: float = ALPHA_DEFAULT) -> float:
    """
    Calcula a Força Geral (FG) de uma equipe.

    Parâmetros:
        dados_time: estatísticas médias por jogo da equipe
        medias_liga: estatísticas médias da liga
        n_jogos: número de jogos da temporada
        incluir_ataque, incluir_defesa, incluir_meio: flags para ativar/desativar sub-métricas
        alpha: peso do prior bayesiano

    Retorna:
        float: valor da FG [45,100]. Se nenhuma sub-métrica ativa, retorna 50.0.
    """
    submetricas = []

    if incluir_ataque:
        atq = calcular_submetrica(dados_time, medias_liga, n_jogos,
                                  INDICADORES_ATAQUE, alpha)
        if atq is not None:
            submetricas.append(atq)

    if incluir_defesa:
        defe = calcular_submetrica(dados_time, medias_liga, n_jogos,
                                   INDICADORES_DEFESA, alpha)
        if defe is not None:
            submetricas.append(defe)

    if incluir_meio:
        mei = calcular_submetrica(dados_time, medias_liga, n_jogos,
                                  INDICADORES_MEIO, alpha)
        if mei is not None:
            submetricas.append(mei)

    # Futuramente: adicionar consistência e resiliência aqui com flags

    if not submetricas:
        return 50.0  # prior puro

    return sum(submetricas) / len(submetricas)
