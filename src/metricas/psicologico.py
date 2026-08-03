"""
Métrica Psicológico (v5 — Expandido)

Avalia aspectos intangíveis de um time:
- Consistência recente (estabilidade + nível + dificuldade dos adversários)
- Resiliência (aproveitamento como visitante + reação a desvantagens)
- Confronto direto contra o adversário atual (com saldo de gols)
- Moral (pontos nos últimos 3 jogos + saldo de gols)
- Pressão da partida (importância do jogo baseada em prateleiras)
- Momentum (variação de desempenho: acelerando, estável ou caindo)

A nota final é a média ponderada das sub‑métricas disponíveis, escala 0–100.
"""

from typing import Optional, List, Dict

# ----------------------------------------------------------
# Pesos das sub‑métricas
# ----------------------------------------------------------
PESOS_SUBMETRICAS = {
    'consistencia': 0.25,
    'resiliencia': 0.20,
    'confronto_direto': 0.15,
    'moral': 0.20,
    'pressao': 0.10,
    'momentum': 0.10,
}


# ----------------------------------------------------------
# Funções auxiliares
# ----------------------------------------------------------
def classificar_prateleira(pos_time: int, total_times: int = 24) -> str:
    """Retorna a prateleira do time com base em sua posição."""
    if pos_time <= 3:
        return 'elite'
    elif pos_time <= 7:
        return 'alta'
    elif pos_time <= 13:
        return 'media'
    elif pos_time <= 16:
        return 'baixa'
    else:
        return 'critica'


# ----------------------------------------------------------
# 1. Consistência (estabilidade + nível + dificuldade)
# ----------------------------------------------------------
def calcular_consistencia(pontos_ultimos_10: list,
                          prateleiras_ultimos_10: list = None) -> Optional[float]:
    """
    Nota de consistência: combina estabilidade (1 - CV), nível (média/3)
    e dificuldade dos adversários enfrentados.
    """
    if not pontos_ultimos_10 or len(pontos_ultimos_10) < 5:
        return None

    n = len(pontos_ultimos_10)
    media = sum(pontos_ultimos_10) / n

    if media == 0:
        return 25.0

    variancia = sum((p - media) ** 2 for p in pontos_ultimos_10) / n
    cv = (variancia ** 0.5) / media
    estabilidade = 1.0 - min(cv, 1.0)
    nivel = media / 3.0

    # Fator de dificuldade (se disponível)
    if prateleiras_ultimos_10 and len(prateleiras_ultimos_10) == n:
        mult_dificuldade = {
            'elite': 1.3, 'alta': 1.15, 'media': 1.0,
            'baixa': 0.85, 'critica': 0.7
        }
        fator_dificuldade = sum(mult_dificuldade.get(p, 1.0) for p in prateleiras_ultimos_10) / n
    else:
        fator_dificuldade = 1.0

    nota = (0.4 * estabilidade + 0.4 * nivel + 0.2 * min(fator_dificuldade, 1.5)) * 100
    return nota


# ----------------------------------------------------------
# 2. Resiliência (visitante + reação)
# ----------------------------------------------------------
def calcular_resiliencia(pontos_fora: int, jogos_fora: int,
                         pontos_virada: int = 0, jogos_virada: int = 0) -> Optional[float]:
    """
    Resiliência: aproveitamento como visitante + capacidade de reagir a desvantagens.
    """
    if jogos_fora == 0:
        return None

    apro_fora = (pontos_fora / (3 * jogos_fora)) * 100

    if jogos_virada > 0:
        apro_virada = (pontos_virada / (3 * jogos_virada)) * 100
        return 0.7 * apro_fora + 0.3 * apro_virada

    return apro_fora


# ----------------------------------------------------------
# 3. Confronto direto (com saldo de gols)
# ----------------------------------------------------------
def calcular_confronto_direto(historico: list) -> Optional[float]:
    """
    Aproveitamento contra o adversário atual, com bônus por saldo de gols.

    Parâmetros:
        historico: lista de dicts com:
            {'resultado': 'V'/'E'/'D', 'gols_pro': int, 'gols_contra': int}
    """
    if not historico or len(historico) < 2:
        return None

    pontos = sum(3 if r['resultado'] == 'V' else 1 if r['resultado'] == 'E' else 0 for r in historico)
    saldo = sum(r['gols_pro'] - r['gols_contra'] for r in historico)

    aproveitamento = (pontos / (3 * len(historico))) * 100
    bonus_saldo = min(saldo * 2, 10) if saldo > 0 else max(saldo * 2, -10)
    nota = aproveitamento + bonus_saldo
    return max(0, min(100, nota))


# ----------------------------------------------------------
# 4. Moral (pontos + saldo de gols recente)
# ----------------------------------------------------------
def calcular_moral(pontos_ultimos_3: int,
                   saldo_gols_ultimos_3: int = 0) -> float:
    """
    Moral recente: pontos nos últimos 3 jogos (0-9) + saldo de gols.
    """
    base = (pontos_ultimos_3 / 9) * 100
    bonus_saldo = min(max(saldo_gols_ultimos_3 * 2, -10), 10)
    nota = base + bonus_saldo
    return max(0, min(100, nota))


# ----------------------------------------------------------
# 5. Pressão da partida
# ----------------------------------------------------------
def calcular_pressao_tabela(pos_time: int,
                            total_times: int,
                            pos_adv: int,
                            dif_pontos_adv: int,
                            confronto_direto_max_pontos: int = 3,
                            choque_prateleira: bool = True) -> float:
    """Calcula a pressão (p_obj) de um time para o próximo jogo."""
    prat_time = classificar_prateleira(pos_time, total_times)
    prat_adv = classificar_prateleira(pos_adv, total_times)

    pressao_base = {
        'elite': 75, 'alta': 65, 'media': 50, 'baixa': 70, 'critica': 90
    }
    base = pressao_base[prat_time]

    if abs(dif_pontos_adv) <= confronto_direto_max_pontos:
        base += 10

    if choque_prateleira:
        hierarquia = {'elite': 0, 'alta': 1, 'media': 2, 'baixa': 3, 'critica': 4}
        if hierarquia[prat_time] > hierarquia[prat_adv]:
            base += 5
        elif hierarquia[prat_time] < hierarquia[prat_adv]:
            base -= 5

    return max(0, min(100, base))


def calcular_pressao_partida(p_obj: float, sensibilidade: float) -> float:
    """Aplica a sensibilidade sobre a pressão objetiva."""
    nota = 50 + (p_obj - 50) * sensibilidade
    return max(0, min(100, nota))


# ----------------------------------------------------------
# 6. Momentum (variação de desempenho)
# ----------------------------------------------------------
def calcular_momentum(pontos_ultimos_5: list,
                      pontos_5_anteriores: list = None) -> float:
    """
    Calcula o momentum: se o time está acelerando, estável ou caindo.
    Compara o desempenho nos últimos 5 jogos com os 5 anteriores.
    Retorna float entre 0 e 100 (50 = estável, >50 = acelerando, <50 = caindo).
    """
    if not pontos_ultimos_5 or len(pontos_ultimos_5) < 3:
        return 50.0

    media_recente = sum(pontos_ultimos_5) / len(pontos_ultimos_5)

    if pontos_5_anteriores and len(pontos_5_anteriores) >= 3:
        media_anterior = sum(pontos_5_anteriores) / len(pontos_5_anteriores)
        variacao = (media_recente - media_anterior) / 3.0
    else:
        tendencia = sum((i - 2) * p for i, p in enumerate(pontos_ultimos_5)) / len(pontos_ultimos_5)
        variacao = tendencia / 6.0

    nota = 50 + variacao * 50
    return max(0, min(100, nota))


# ----------------------------------------------------------
# Função principal
# ----------------------------------------------------------
def calcular_psicologico(
    consistencia_pontos: Optional[list] = None,
    prateleiras_consistencia: Optional[list] = None,
    resiliencia_fora: Optional[tuple] = None,
    resiliencia_virada: Optional[tuple] = None,
    confronto_direto_hist: Optional[list] = None,
    moral_pontos: Optional[int] = None,
    moral_saldo_gols: Optional[int] = 0,
    pressao_p_obj: Optional[float] = None,
    pressao_sensibilidade: float = 0.3,
    momentum_ultimos_5: Optional[list] = None,
    momentum_anteriores_5: Optional[list] = None,
    pesos: Dict[str, float] = None
) -> float:
    """
    Calcula a nota do pilar Psicológico.

    Retorna float entre 0 e 100.
    """
    if pesos is None:
        pesos = PESOS_SUBMETRICAS

    notas = {}
    pesos_ativos = {}

    # Consistência
    if consistencia_pontos is not None:
        c = calcular_consistencia(consistencia_pontos, prateleiras_consistencia)
        if c is not None:
            notas['consistencia'] = c
            pesos_ativos['consistencia'] = pesos.get('consistencia', 0.25)

    # Resiliência
    if resiliencia_fora is not None:
        r = calcular_resiliencia(*resiliencia_fora)
        if resiliencia_virada is not None:
            r = calcular_resiliencia(
                resiliencia_fora[0], resiliencia_fora[1],
                resiliencia_virada[0], resiliencia_virada[1]
            )
        if r is not None:
            notas['resiliencia'] = r
            pesos_ativos['resiliencia'] = pesos.get('resiliencia', 0.20)

    # Confronto direto
    if confronto_direto_hist is not None:
        cd = calcular_confronto_direto(confronto_direto_hist)
        if cd is not None:
            notas['confronto_direto'] = cd
            pesos_ativos['confronto_direto'] = pesos.get('confronto_direto', 0.15)

    # Moral
    if moral_pontos is not None:
        notas['moral'] = calcular_moral(moral_pontos, moral_saldo_gols or 0)
        pesos_ativos['moral'] = pesos.get('moral', 0.20)

    # Pressão
    if pressao_p_obj is not None:
        notas['pressao'] = calcular_pressao_partida(pressao_p_obj, pressao_sensibilidade)
        pesos_ativos['pressao'] = pesos.get('pressao', 0.10)

    # Momentum
    if momentum_ultimos_5 is not None:
        notas['momentum'] = calcular_momentum(momentum_ultimos_5, momentum_anteriores_5)
        pesos_ativos['momentum'] = pesos.get('momentum', 0.10)

    if not notas:
        return 50.0

    soma_pesos = sum(pesos_ativos.values())
    if soma_pesos == 0:
        return 50.0

    pesos_norm = {k: v / soma_pesos for k, v in pesos_ativos.items()}
    nota_final = sum(notas[k] * pesos_norm[k] for k in notas)
    return nota_final
