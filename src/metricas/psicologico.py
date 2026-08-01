from typing import Optional, Dict

def calcular_consistencia(pontos_ultimos_10: list) -> Optional[float]:
    if not pontos_ultimos_10 or len(pontos_ultimos_10) < 5:
        return None
    n = len(pontos_ultimos_10)
    media = sum(pontos_ultimos_10) / n
    if media == 0:
        return 100.0
    variancia = sum((p - media) ** 2 for p in pontos_ultimos_10) / n
    cv = (variancia ** 0.5) / media
    nota = (1 - min(cv, 1.0)) * 100
    return nota

def calcular_resiliencia(pontos_possiveis: int, pontos_conquistados: int) -> Optional[float]:
    if pontos_possiveis == 0:
        return None
    return (pontos_conquistados / pontos_possiveis) * 100

def calcular_confronto_direto(historico: list) -> Optional[float]:
    if not historico or len(historico) < 2:
        return None
    pontos = sum(3 if r == 'V' else 1 if r == 'E' else 0 for r in historico)
    return (pontos / (3 * len(historico))) * 100

def calcular_moral(pontos_ultimos_3: int) -> float:
    return (pontos_ultimos_3 / 9) * 100

def calcular_pressao_partida(p_obj: float, sensibilidade: float) -> float:
    nota = 50 + (p_obj - 50) * sensibilidade
    return max(0, min(100, nota))

def calcular_psicologico(
    consistencia_pontos: Optional[list] = None,
    resiliencia_dados: Optional[tuple] = None,
    confronto_direto_hist: Optional[list] = None,
    moral_pontos: Optional[int] = None,
    pressao_p_obj: Optional[float] = None,
    pressao_sensibilidade: float = 0.0
) -> float:
    notas = []
    if consistencia_pontos is not None:
        c = calcular_consistencia(consistencia_pontos)
        if c is not None: notas.append(c)
    if resiliencia_dados is not None:
        r = calcular_resiliencia(*resiliencia_dados)
        if r is not None: notas.append(r)
    if confronto_direto_hist is not None:
        cd = calcular_confronto_direto(confronto_direto_hist)
        if cd is not None: notas.append(cd)
    if moral_pontos is not None:
        notas.append(calcular_moral(moral_pontos))
    if pressao_p_obj is not None:
        notas.append(calcular_pressao_partida(pressao_p_obj, pressao_sensibilidade))
    if not notas:
        return 50.0
    return sum(notas) / len(notas)
