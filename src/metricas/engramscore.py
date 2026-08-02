"""
EngramsCore - Índice Absoluto de Confronto (v2)

Unifica os cinco pilares do método em uma pontuação final (0-100) para cada
time, aplicando pesos configuráveis e um fator casa composto por:
- um bônus fixo (HOME_ADV) representando a vantagem intrínseca de jogar em casa;
- um bônus dinâmico baseado na diferença de MA (mantido, mas com thresholds ajustados).

A conversão para probabilidades 1X2 utiliza um modelo de Poisson com média de
gols calibrada, garantindo que o empate nunca seja zero.

Se odds justas (sem margem) forem fornecidas, calcula também o valor esperado
de cada desfecho.
"""

from typing import Dict, Optional, Tuple
import math

# ----------------------------------------------------------
# Pesos padrão (configuráveis)
# ----------------------------------------------------------
PESOS_PADRAO = {
    'MA': 0.20,
    'FG': 0.25,
    'CPP': 0.20,
    'Estilo': 0.20,
    'Psicologico': 0.15,
}

# Parâmetros do modelo Poisson
MEDIA_GOLS_BASE = 2.5       # média de gols por jogo da liga
HOME_ADV_GOLS = 0.3         # acréscimo de gols esperados para o mandante
MAX_GOLS = 10               # limite para truncar a distribuição

# Thresholds para bônus dinâmico (agora com pequeno ajuste)
THR_MANDANTE = 6            # diferença de MA a favor do mandante para +1
THR_VISITANTE = 6           # diferença a favor do visitante para +1


# ----------------------------------------------------------
# Funções auxiliares
# ----------------------------------------------------------
def _redistribuir_pesos(pilares_disponiveis: Dict[str, Optional[float]],
                        pesos: Dict[str, float]) -> Dict[str, float]:
    """Remove pilares ausentes e redistribui pesos proporcionalmente."""
    ativos = {k: v for k, v in pilares_disponiveis.items() if v is not None}
    if not ativos:
        return {}
    peso_total = sum(pesos.get(k, 0.0) for k in ativos)
    if peso_total == 0:
        n = len(ativos)
        return {k: 1.0 / n for k in ativos}
    return {k: pesos.get(k, 0.0) / peso_total for k in ativos}


def _aplicar_fator_casa(ma_casa: float, ma_fora: float,
                        thr_casa: float = THR_MANDANTE,
                        thr_fora: float = THR_VISITANTE) -> Tuple[float, float]:
    """
    Bônus dinâmico de +1 no EC se a diferença de MA for grande.
    Retorna (bonus_casa, bonus_fora).
    """
    diff = ma_casa - ma_fora
    if diff >= thr_casa:
        return 1.0, 0.0
    elif diff <= -thr_fora:
        return 0.0, 1.0
    return 0.0, 0.0


def _poisson_prob(gols_esperados: float, max_gols: int = MAX_GOLS) -> list:
    """Retorna lista de probabilidades de 0 a max_gols gols (Poisson)."""
    probs = []
    for k in range(max_gols + 1):
        prob = (gols_esperados ** k) * math.exp(-gols_esperados) / math.factorial(k)
        probs.append(prob)
    return probs


def _probabilidades_poisson(ec_a: float, ec_b: float,
                            time_mandante: str,
                            media_gols: float = MEDIA_GOLS_BASE,
                            home_adv_gols: float = HOME_ADV_GOLS) -> Tuple[float, float, float]:
    """
    Converte ECs (0-100) em probabilidades 1X2 usando Poisson.
    ec_a e ec_b são as forças brutas; o fator casa é adicionado conforme time_mandante.
    """
    # Escala os EC para gols esperados, proporcional à média da liga
    # Exemplo: EC=50 → força média → gols esperados ~ media_gols/2
    fator = media_gols / 100.0
    xg_a = ec_a * fator
    xg_b = ec_b * fator

    if time_mandante == 'A':
        xg_a += home_adv_gols
    elif time_mandante == 'B':
        xg_b += home_adv_gols

    # Distribuições de Poisson
    probs_a = _poisson_prob(xg_a)
    probs_b = _poisson_prob(xg_b)

    p_a = p_b = p_e = 0.0
    for i in range(MAX_GOLS + 1):
        for j in range(MAX_GOLS + 1):
            prob = probs_a[i] * probs_b[j]
            if i > j:
                p_a += prob
            elif j > i:
                p_b += prob
            else:
                p_e += prob

    # Normaliza para garantir soma 1 (trunca em MAX_GOLS causa pequena perda)
    total = p_a + p_b + p_e
    if total > 0:
        p_a /= total
        p_b /= total
        p_e /= total

    return p_a, p_b, p_e


# ----------------------------------------------------------
# Função principal
# ----------------------------------------------------------
def calcular_engramscore(
    # Pilares para Time A
    ma_a: Optional[float] = None,
    fg_a: Optional[float] = None,
    cpp_a: Optional[float] = None,
    estilo_a: Optional[float] = None,
    psicologico_a: Optional[float] = None,
    # Pilares para Time B
    ma_b: Optional[float] = None,
    fg_b: Optional[float] = None,
    cpp_b: Optional[float] = None,
    estilo_b: Optional[float] = None,
    psicologico_b: Optional[float] = None,
    # Configurações
    time_mandante: str = 'A',
    pesos: Dict[str, float] = None,
    thr_mandante: float = THR_MANDANTE,
    thr_visitante: float = THR_VISITANTE,
    # Novos parâmetros
    odds: Optional[Dict[str, float]] = None,   # {'1': odd_casa, 'X': odd_empate, '2': odd_fora}
    media_gols: float = MEDIA_GOLS_BASE,
    home_adv_gols: float = HOME_ADV_GOLS,
) -> Dict[str, float]:
    """
    Calcula o EngramsCore para ambos os times, gera probabilidades 1X2
    e, se odds forem fornecidas, o valor esperado de cada desfecho.
    """
    if pesos is None:
        pesos = PESOS_PADRAO.copy()

    pilares_a = {
        'MA': ma_a,
        'FG': fg_a,
        'CPP': cpp_a,
        'Estilo': estilo_a,
        'Psicologico': psicologico_a,
    }
    pilares_b = {
        'MA': ma_b,
        'FG': fg_b,
        'CPP': cpp_b,
        'Estilo': estilo_b,
        'Psicologico': psicologico_b,
    }

    # Pilares ativos em ambos os times
    ativos_ambos = {p for p in pilares_a if pilares_a[p] is not None and pilares_b[p] is not None}

    if not ativos_ambos:
        # Caso não haja pilar comum, retorna empate total
        return {
            'EC_A': 50.0,
            'EC_B': 50.0,
            'P_A': 0.333, 'P_B': 0.333, 'P_E': 0.334,
            'P_A_ou_E': 0.667, 'P_B_ou_E': 0.667,
        }

    # Pesos normalizados apenas para os pilares ativos
    peso_ativos = {p: pesos[p] for p in ativos_ambos}
    soma_pesos = sum(peso_ativos.values())
    pesos_norm = {p: w / soma_pesos for p, w in peso_ativos.items()}

    # EC brutos
    ec_a = sum(pesos_norm[p] * pilares_a[p] for p in pesos_norm)
    ec_b = sum(pesos_norm[p] * pilares_b[p] for p in pesos_norm)

    # Bônus dinâmico de casa baseado no MA (se disponível)
    bonus_a = bonus_b = 0.0
    if ma_a is not None and ma_b is not None:
        if time_mandante == 'A':
            b_a, b_b = _aplicar_fator_casa(ma_a, ma_b, thr_mandante, thr_visitante)
        elif time_mandante == 'B':
            b_b, b_a = _aplicar_fator_casa(ma_b, ma_a, thr_mandante, thr_visitante)
        else:
            raise ValueError("time_mandante deve ser 'A' ou 'B'")
        bonus_a, bonus_b = b_a, b_b

    ec_a += bonus_a
    ec_b += bonus_b

    # Truncamento
    ec_a = max(0.0, min(100.0, ec_a))
    ec_b = max(0.0, min(100.0, ec_b))

    # Probabilidades via Poisson com fator casa intrínseco
    p_a, p_b, p_e = _probabilidades_poisson(
        ec_a, ec_b, time_mandante, media_gols, home_adv_gols
    )

    # Dupla chance
    p_a_ou_e = p_a + p_e
    p_b_ou_e = p_b + p_e

    resultado = {
        'EC_A': round(ec_a, 2),
        'EC_B': round(ec_b, 2),
        'P_A': round(p_a, 4),
        'P_B': round(p_b, 4),
        'P_E': round(p_e, 4),
        'P_A_ou_E': round(p_a_ou_e, 4),
        'P_B_ou_E': round(p_b_ou_e, 4),
    }

    # Cálculo do valor esperado (EV) se odds forem fornecidas
    if odds is not None:
        odd_1 = odds.get('1')
        odd_X = odds.get('X')
        odd_2 = odds.get('2')

        def ev(prob: float, odd: Optional[float]) -> Optional[float]:
            if odd is not None and odd > 1.0:
                return round(prob * odd - 1.0, 4)
            return None

        resultado['EV_A'] = ev(p_a, odd_1)
        resultado['EV_B'] = ev(p_b, odd_2)
        resultado['EV_E'] = ev(p_e, odd_X)

        # Indica onde há valor positivo (EV > 0) para alertar o usuário
        resultado['VALOR_A'] = (resultado['EV_A'] or -1) > 0
        resultado['VALOR_B'] = (resultado['EV_B'] or -1) > 0
        resultado['VALOR_E'] = (resultado['EV_E'] or -1) > 0

    return resultado
