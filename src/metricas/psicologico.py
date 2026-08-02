"""
Métrica Psicológico (v4)

Avalia aspectos intangíveis de um time:
- Consistência recente (estabilidade + nível)
- Resiliência (aproveitamento como visitante)
- Confronto direto contra o adversário atual
- Moral (pontos nos últimos 3 jogos)
- Pressão da partida (importância do jogo baseada em prateleiras)

A nota final é a média simples das sub‑métricas disponíveis, escala 0–100.
"""

from typing import Optional


# ----------------------------------------------------------
# Funções auxiliares
# ----------------------------------------------------------

def classificar_prateleira(pos_time: int, total_times: int) -> str:
    """
    Retorna a prateleira do time com base em sua posição.
    A divisão é fixa e independe do número total de times:
        1-3  : elite (briga por título)
        4-7  : alta  (briga por classificação)
        8-13 : média (meio da tabela)
        14-16: baixa (ameaça de rebaixamento)
        17+  : crítica (zona de rebaixamento)
    """
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


def calcular_pressao_tabela(pos_time: int,
                            total_times: int,
                            pos_adv: int,
                            dif_pontos_adv: int,
                            confronto_direto_max_pontos: int = 3,
                            choque_prateleira: bool = True) -> float:
    """
    Calcula a pressão (p_obj) de um time para o próximo jogo.

    - Pressão base definida pela prateleira:
        elite   -> 75  (briga por título)
        alta    -> 65  (briga por G4)
        media   -> 50  (tranquilidade)
        baixa   -> 70  (ameaça de rebaixamento)
        critica -> 90  (zona de rebaixamento)
    - Ajuste por confronto direto (diferença de pontos ≤ limiar): +10
    - Ajuste por choque de prateleiras (opcional):
        * time de prateleira inferior enfrentando superior: +5
        * time de prateleira superior enfrentando inferior: -5

    Parâmetros:
        pos_time: posição do time (1 = líder).
        total_times: número total de times na liga.
        pos_adv: posição do adversário.
        dif_pontos_adv: diferença de pontos (time - adversário).
        confronto_direto_max_pontos: diferença máxima para considerar confronto direto.
        choque_prateleira: se True, modula a pressão conforme diferença de prateleira.

    Retorna:
        float entre 0 e 100.
    """
    prat_time = classificar_prateleira(pos_time, total_times)
    prat_adv = classificar_prateleira(pos_adv, total_times)

    # Pressão base por prateleira
    pressao_base = {
        'elite': 75,
        'alta': 65,
        'media': 50,
        'baixa': 70,
        'critica': 90
    }
    base = pressao_base[prat_time]

    # Confronto direto (times próximos em pontos)
    if abs(dif_pontos_adv) <= confronto_direto_max_pontos:
        base += 10

    # Choque de prateleiras (opcional)
    if choque_prateleira:
        hierarquia = {'elite': 0, 'alta': 1, 'media': 2, 'baixa': 3, 'critica': 4}
        if hierarquia[prat_time] > hierarquia[prat_adv]:
            # time em prateleira inferior enfrentando superior
            base += 5
        elif hierarquia[prat_time] < hierarquia[prat_adv]:
            # time em prateleira superior enfrentando inferior
            base -= 5

    return max(0, min(100, base))


def calcular_pressao_partida(p_obj: float, sensibilidade: float) -> float:
    """
    Aplica a sensibilidade sobre a pressão objetiva.
    p_obj: nota de 0-100 (importância do jogo).
    sensibilidade: 0 = sem efeito, 1 = efeito máximo.
    """
    nota = 50 + (p_obj - 50) * sensibilidade
    return max(0, min(100, nota))


def calcular_consistencia(pontos_ultimos_10: list) -> Optional[float]:
    """
    Nota de consistência recente: combina estabilidade (1 - CV) e nível (média/3).
    Corrige o problema de times que perdem sempre recebendo 100.
    """
    if not pontos_ultimos_10 or len(pontos_ultimos_10) < 5:
        return None

    n = len(pontos_ultimos_10)
    media = sum(pontos_ultimos_10) / n
    if media == 0:
        # Nível zero, mas não queremos premiar com 100
        nivel = 0.0
        estabilidade = 0.5  # valor neutro para não distorcer
        return (0.5 * estabilidade + 0.5 * nivel) * 100  # 25

    variancia = sum((p - media) ** 2 for p in pontos_ultimos_10) / n
    cv = (variancia ** 0.5) / media
    estabilidade = 1.0 - min(cv, 1.0)
    nivel = media / 3.0
    nota = (0.5 * estabilidade + 0.5 * nivel) * 100
    return nota


def calcular_resiliencia(pontos_fora: int, jogos_fora: int) -> Optional[float]:
    """
    Resiliência: aproveitamento como visitante.
    Mede a capacidade de pontuar sob pressão da torcida adversária.
    Se não houver jogos fora, retorna None.
    """
    if jogos_fora == 0:
        return None
    return (pontos_fora / (3 * jogos_fora)) * 100


def calcular_confronto_direto(historico: list) -> Optional[float]:
    """
    Aproveitamento contra o adversário atual (últimos confrontos diretos).
    historico: lista de strings 'V','E','D'.
    """
    if not historico or len(historico) < 2:
        return None
    pontos = sum(3 if r == 'V' else 1 if r == 'E' else 0 for r in historico)
    return (pontos / (3 * len(historico))) * 100


def calcular_moral(pontos_ultimos_3: int) -> float:
    """Moral recente: pontos nos últimos 3 jogos (0-9)."""
    return (pontos_ultimos_3 / 9) * 100


# ----------------------------------------------------------
# Função principal
# ----------------------------------------------------------

def calcular_psicologico(
    consistencia_pontos: Optional[list] = None,
    resiliencia_fora: Optional[tuple] = None,  # (pontos_fora, jogos_fora)
    confronto_direto_hist: Optional[list] = None,
    moral_pontos: Optional[int] = None,
    pressao_p_obj: Optional[float] = None,
    pressao_sensibilidade: float = 0.0
) -> float:
    """
    Calcula a nota do pilar Psicológico.

    Parâmetros:
        consistencia_pontos: lista de pontos (0,1,3) dos últimos 10 jogos.
        resiliencia_fora: tupla (pontos, jogos) como visitante.
        confronto_direto_hist: lista de resultados ('V','E','D') contra o adversário.
        moral_pontos: total de pontos nos últimos 3 jogos (0-9).
        pressao_p_obj: nota de pressão (0-100) vinda de calcular_pressao_tabela.
        pressao_sensibilidade: quanto a pressão afeta a nota (0 = sem efeito).

    Retorna:
        float entre 0 e 100.
    """
    notas = []

    if consistencia_pontos is not None:
        c = calcular_consistencia(consistencia_pontos)
        if c is not None:
            notas.append(c)

    if resiliencia_fora is not None:
        r = calcular_resiliencia(*resiliencia_fora)
        if r is not None:
            notas.append(r)

    if confronto_direto_hist is not None:
        cd = calcular_confronto_direto(confronto_direto_hist)
        if cd is not None:
            notas.append(cd)

    if moral_pontos is not None:
        notas.append(calcular_moral(moral_pontos))

    if pressao_p_obj is not None:
        notas.append(calcular_pressao_partida(pressao_p_obj, pressao_sensibilidade))

    if not notas:
        return 50.0

    return sum(notas) / len(notas)
