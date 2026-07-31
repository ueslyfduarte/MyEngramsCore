"""
Métrica Estilo de Jogo

Avalia o perfil tático de uma equipe com base em indicadores de processo
(posse, pressão, transições, etc.) e gera, para cada confronto, um valor
de 0 a 100 que combina:

1. Nota de execução: quão bem o time pratica seus estilos.
2. Vantagem tática: quão favorável é o confronto de estilos contra o adversário.

Cada dimensão de estilo é calculada como a média dos indicadores disponíveis,
normalizados em relação à liga (prior 50, escala 0-100). Se um indicador ou
dimensão inteira estiver ausente, o sistema se adapta automaticamente.
"""

from typing import Dict, Optional, List, Tuple
from src.utils import normalizar_indicador, atualizacao_bayesiana, media_ativos

# ----------------------------------------------------------
# Dimensões de estilo e seus indicadores
# ----------------------------------------------------------
INDICADORES_ESTILO = {
    'posse': {                # Posse/Paciência
        'posse_bola': 'posse',           # % posse de bola
        'passes_sequencia': 'passes_seq',# passes por sequência de posse
        'passes_terco_ofensivo': 'passes_to', # passes no terço ofensivo
    },
    'pressao_alta': {         # Pressão alta
        'acoes_terco_ofensivo': 'acoes_to',   # ações defensivas no terço ofensivo
        'ppda': 'ppda',                       # passes permitidos por ação defensiva (invertido)
        'dist_acoes_def': 'dist_ad',          # distância média das ações defensivas (invertido)
    },
    'contra_ataque': {        # Contra-ataque
        'gols_contra_ataque': 'gols_ca',
        'chutes_transicao': 'chutes_trans',
        'pct_ataques_5_passes': 'pct_ataq_5',
    },
    'jogo_laterais': {        # Jogo pelas laterais
        'pct_ataques_lados': 'pct_lados',
        'cruzamentos': 'cruzamentos',
        'escanteios': 'escanteios',
    },
    'jogo_meio': {            # Jogo pelo meio
        'passes_progressivos_centrais': 'passes_prog_c',
        'infiltracoes_area_meio': 'infiltracoes',
        'assistencias_centrais': 'assists_c',
    },
    'transicao_rapida': {     # Transição rápida
        'velocidade_progressao': 'vel_prog',
        'passes_longos_verticais': 'passes_longos',
        'chutes_10s_recuperacao': 'chutes_10s',
    },
    'defesa_bloco_baixo': {   # Defesa em bloco baixo
        'dist_linha_defensiva': 'dist_ld',       # invertido (quanto menor, mais baixo)
        'pct_acoes_proprio_terco': 'pct_acoes_pt',
        'gols_sofridos_contra_ataque': 'gols_ca_sofridos', # invertido
    },
    'pressao_pos_perda': {    # Pressão pós-perda
        'recuperacoes_5s_ofensivo': 'recup_5s',
        'pct_pressao_bem_sucedida': 'pct_pressao_ok',
        'turnovers_forcados_adv': 'turnovers_forc',
    },
}

# ----------------------------------------------------------
# Parâmetros do método (não são dados fictícios)
# ----------------------------------------------------------
ALPHA_ESTILO = 5   # peso do prior para indicadores de estilo
PRIOR_ESTILO = 50.0

# ----------------------------------------------------------
# Matriz de vantagem tática (valores entre -1 e 1)
# Linha: estilo do time A, Coluna: estilo do time B
# ----------------------------------------------------------
MATRIZ_VANTAGEM = {
    ('posse',              'defesa_bloco_baixo'):  0.15,
    ('posse',              'pressao_alta'):       -0.15,
    ('pressao_alta',       'posse'):               0.20,
    ('pressao_alta',       'defesa_bloco_baixo'):  0.10,
    ('pressao_alta',       'contra_ataque'):      -0.20,
    ('contra_ataque',      'pressao_alta'):        0.25,
    ('contra_ataque',      'posse'):               0.10,
    ('contra_ataque',      'defesa_bloco_baixo'): -0.20,
    ('jogo_laterais',      'defesa_bloco_baixo'):  0.20,
    ('jogo_laterais',      'pressao_alta'):       -0.10,
    ('jogo_meio',          'defesa_bloco_baixo'): -0.10,
    ('jogo_meio',          'pressao_alta'):        0.05,
    ('transicao_rapida',   'defesa_bloco_baixo'): -0.15,
    ('transicao_rapida',   'pressao_alta'):        0.15,
    ('defesa_bloco_baixo', 'posse'):               0.10,
    ('defesa_bloco_baixo', 'contra_ataque'):       0.20,
    ('defesa_bloco_baixo', 'jogo_laterais'):      -0.15,
    ('defesa_bloco_baixo', 'transicao_rapida'):    0.05,
    ('pressao_pos_perda',  'transicao_rapida'):    0.15,
    ('pressao_pos_perda',  'posse'):               0.10,
    ('pressao_pos_perda',  'contra_ataque'):      -0.10,
}
# Se um par não estiver na matriz, o valor padrão é 0 (neutro).

# ----------------------------------------------------------
# Funções internas
# ----------------------------------------------------------

def _indicador_para_escala(valor_time: Optional[float],
                           media_liga: float,
                           n_jogos: int,
                           alpha: float = ALPHA_ESTILO,
                           inverter: bool = False) -> Optional[float]:
    """Calcula um indicador normalizado, com ou sem inversão (ex.: PPDA)."""
    if valor_time is None:
        return None
    # Se for indicador "quanto menor melhor", invertemos: usamos (2 - time/liga)*50
    if inverter:
        if media_liga == 0:
            bruto = PRIOR_ESTILO
        else:
            # Fórmula de inversão: 2 - (time / liga) => escala centrada em 1
            bruto = (2.0 - (valor_time / media_liga)) * 50.0
    else:
        bruto = normalizar_indicador(valor_time, media_liga)

    posterior = atualizacao_bayesiana(PRIOR_ESTILO, bruto, n_jogos, alpha)
    # Truncamento 0-100 (sem piso 45)
    return max(0.0, min(100.0, posterior))


def _calcular_dimensao(dados_time: Dict[str, float],
                       medias_liga: Dict[str, float],
                       n_jogos: int,
                       indicadores: Dict[str, str],
                       inversoes: List[str] = []) -> Optional[float]:
    """Calcula uma dimensão de estilo como a média dos indicadores disponíveis."""
    valores = []
    for nome_tecnico, chave_dado in indicadores.items():
        valor = dados_time.get(chave_dado)
        media = medias_liga.get(chave_dado, 0.0)
        inv = (chave_dado in inversoes)
        ind = _indicador_para_escala(valor, media, n_jogos, inverter=inv)
        valores.append(ind)
    return media_ativos(valores)


# Lista de chaves que devem ser invertidas (quanto menor, melhor)
INVERSOES = ['ppda', 'dist_ad', 'dist_ld', 'gols_ca_sofridos']


# ----------------------------------------------------------
# Funções principais (API pública)
# ----------------------------------------------------------

def calcular_vetor_estilo(dados_time: Dict[str, float],
                          medias_liga: Dict[str, float],
                          n_jogos: int) -> Dict[str, Optional[float]]:
    """
    Calcula o vetor de estilo de um time (0-100 por dimensão).

    Retorna um dicionário com as chaves das dimensões e os valores calculados.
    Dimensões sem indicadores disponíveis ficam como None.
    """
    vetor = {}
    for dim, indicadores in INDICADORES_ESTILO.items():
        valor = _calcular_dimensao(dados_time, medias_liga, n_jogos,
                                   indicadores, INVERSOES)
        vetor[dim] = valor
    return vetor


def calcular_vantagem_tatica(vetor_A: Dict[str, Optional[float]],
                             vetor_B: Dict[str, Optional[float]],
                             matriz: Dict[Tuple[str, str], float] = None) -> float:
    """
    Calcula a vantagem tática do Time A sobre o Time B (0-100),
    baseada nos vetores de estilo e na matriz de interação.
    """
    if matriz is None:
        matriz = MATRIZ_VANTAGEM

    # Normaliza: cada dimensão ausente é tratada como 50 (neutro)
    def get_score(vetor, dim):
        val = vetor.get(dim)
        return val if val is not None else 50.0

    soma = 0.0
    maximo = 0.0  # para normalização
    dims = list(INDICADORES_ESTILO.keys())

    for dA in dims:
        for dB in dims:
            scoreA = get_score(vetor_A, dA)
            scoreB = get_score(vetor_B, dB)
            mod = matriz.get((dA, dB), 0.0)
            # O produto dos scores e do modificador
            produto = scoreA * scoreB * mod
            soma += produto
            # Para o máximo teórico, consideramos scores 100 e mod = 1
            maximo += 100.0 * 100.0 * 1.0

    if maximo == 0:
        return 50.0  # neutro

    # A vantagem bruta pode ser negativa; normalizamos para 0-100
    # Queremos que 0 seja a pior desvantagem e 100 a maior vantagem.
    # A soma pode variar entre -maximo e +maximo (se mods forem -1 a 1).
    # Mapeamos de [-max, +max] para [0, 100]:
    vantagem_normalizada = (soma / maximo) * 50.0 + 50.0
    # Garantir limites
    return max(0.0, min(100.0, vantagem_normalizada))


def calcular_estilo(dados_time: Dict[str, float],
                    medias_liga: Dict[str, float],
                    n_jogos: int,
                    vetor_oponente: Dict[str, Optional[float]],
                    matriz: Dict[Tuple[str, str], float] = None) -> float:
    """
    Calcula o valor final do pilar Estilo para um time no confronto.

    Combina a nota de execução (média das dimensões em que é forte,
    ou média geral caso nenhuma seja >60) com a vantagem tática.

    Retorna um float entre 0 e 100.
    """
    vetor = calcular_vetor_estilo(dados_time, medias_liga, n_jogos)

    # Nota de execução: média das dimensões > 60; se nenhuma, média geral
    dimensoes_ativas = [v for v in vetor.values() if v is not None]
    if not dimensoes_ativas:
        nota_execucao = PRIOR_ESTILO
    else:
        acima_60 = [v for v in dimensoes_ativas if v > 60.0]
        if acima_60:
            nota_execucao = sum(acima_60) / len(acima_60)
        else:
            nota_execucao = sum(dimensoes_ativas) / len(dimensoes_ativas)

    # Vantagem tática
    vantagem = calcular_vantagem_tatica(vetor, vetor_oponente, matriz)

    # Média simples (pode ser ajustada)
    return (nota_execucao + vantagem) / 2.0
