"""
EngramsCore - Índice Absoluto de Confronto

Unifica os cinco pilares do método em uma pontuação final (0-100) para cada
time, aplicando pesos configuráveis e um fator casa dinâmico baseado no MA.

Fornece também probabilidades 1X2, dupla chance e empate de forma imparcial.
"""

from typing import Dict, Optional, Tuple

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

# Thresholds para bônus de casa dinâmico (baseado no MA)
THR_MANDANTE = 10   # diferença de MA a favor do mandante para ganhar +1
THR_VISITANTE = 8   # diferença de MA a favor do visitante para ganhar +1


# ----------------------------------------------------------
# Funções auxiliares
# ----------------------------------------------------------
def _redistribuir_pesos(pilares_disponiveis: Dict[str, Optional[float]],
                        pesos: Dict[str, float]) -> Dict[str, float]:
    """
    Remove pilares com valor None e redistribui os pesos proporcionalmente.
    Retorna um dicionário {pilar: peso_normalizado}.
    """
    ativos = {k: v for k, v in pilares_disponiveis.items() if v is not None}
    if not ativos:
        return {}  # sem pilares ativos, EC será 0 depois
    peso_total = sum(pesos.get(k, 0.0) for k in ativos)
    if peso_total == 0:
        # Se nenhum pilar ativo tiver peso, distribui igualmente
        n = len(ativos)
        return {k: 1.0/n for k in ativos}
    return {k: pesos.get(k, 0.0)/peso_total for k in ativos}


def _aplicar_fator_casa(ma_casa: float, ma_fora: float,
                        thr_casa: float = THR_MANDANTE,
                        thr_fora: float = THR_VISITANTE) -> Tuple[float, float]:
    """
    Calcula bônus de +1 para mandante ou visitante conforme diferença de MA.
    Retorna (bonus_casa, bonus_fora).
    """
    diff_casa = ma_casa - ma_fora
    diff_fora = ma_fora - ma_casa

    if diff_casa >= thr_casa:
        return 1.0, 0.0
    elif diff_fora >= thr_fora:
        return 0.0, 1.0
    else:
        return 0.0, 0.0


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
    time_mandante: str = 'A',      # 'A' ou 'B'
    pesos: Dict[str, float] = None,
    thr_mandante: float = THR_MANDANTE,
    thr_visitante: float = THR_VISITANTE,
) -> Dict[str, float]:
    """
    Calcula o EngramsCore para ambos os times em um confronto.

    Parâmetros:
        ma_a, fg_a, cpp_a, estilo_a, psicologico_a: valores dos pilares do Time A (0-100, FG: 45-100).
        idem para Time B.
        time_mandante: 'A' se Time A é o mandante, 'B' se Time B é o mandante.
        pesos: dicionário com pesos para cada pilar. Default: PESOS_PADRAO.
        thr_mandante, thr_visitante: thresholds para bônus de casa.

    Retorna:
        dict com:
            'EC_A': EngramsCore do Time A (0-100)
            'EC_B': EngramsCore do Time B (0-100)
            'P_A': probabilidade de vitória de A (0-1)
            'P_B': probabilidade de vitória de B (0-1)
            'P_E': probabilidade de empate (0-1)
            'P_A_ou_E': dupla chance A ou empate
            'P_B_ou_E': dupla chance B ou empate
    """
    if pesos is None:
        pesos = PESOS_PADRAO.copy()

    # Dicionários de pilares
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

    # Redistribuir pesos apenas com pilares ativos em ambos os times
    # Consideramos um pilar ativo se ambos os times têm valor não None
    ativos_ambos = {}
    for pilar in ['MA', 'FG', 'CPP', 'Estilo', 'Psicologico']:
        if pilares_a[pilar] is not None and pilares_b[pilar] is not None:
            ativos_ambos[pilar] = True

    if not ativos_ambos:
        # Caso extremo: nenhum pilar comum; retornar neutro
        return {
            'EC_A': 50.0,
            'EC_B': 50.0,
            'P_A': 0.333,
            'P_B': 0.333,
            'P_E': 0.334,
            'P_A_ou_E': 0.667,
            'P_B_ou_E': 0.667,
        }

    # Pesos redistribuídos só com pilares ativos em ambos
    peso_ativos = {p: pesos[p] for p in ativos_ambos}
    soma_pesos = sum(peso_ativos.values())
    pesos_norm = {p: w/soma_pesos for p, w in peso_ativos.items()}

    # Calcular EC parcial (sem bônus casa)
    ec_a = sum(pesos_norm[p] * pilares_a[p] for p in pesos_norm)
    ec_b = sum(pesos_norm[p] * pilares_b[p] for p in pesos_norm)

    # Fator casa dinâmico (se ambos MA disponíveis)
    bonus_a = 0.0
    bonus_b = 0.0
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

    # Limitar a 0-100 (por segurança, FG já vem >=45, mas outros podem ser negativos em teoria?)
    ec_a = max(0.0, min(100.0, ec_a))
    ec_b = max(0.0, min(100.0, ec_b))

    # Probabilidades 1X2
    soma = ec_a + ec_b
    if soma == 0:
        p_a = p_b = 0.333
        p_e = 0.334
    else:
        p_a = ec_a / soma
        p_b = ec_b / soma
        p_e = 1.0 - p_a - p_b
        # Se por acaso p_e < 0, redistribui
        if p_e < 0:
            p_e = 0.0
            total = p_a + p_b
            if total > 0:
                p_a /= total
                p_b /= total

    p_a_ou_e = p_a + p_e
    p_b_ou_e = p_b + p_e

    return {
        'EC_A': round(ec_a, 2),
        'EC_B': round(ec_b, 2),
        'P_A': round(p_a, 4),
        'P_B': round(p_b, 4),
        'P_E': round(p_e, 4),
        'P_A_ou_E': round(p_a_ou_e, 4),
        'P_B_ou_E': round(p_b_ou_e, 4),
    }
