"""
Métrica Psicológica

Avalia fatores psicológicos/empíricos de uma equipe para um confronto.
Dimensões: Consistência, Resiliência, Confronto Direto, Moral/Momento
e Pressão da Partida.

Cada dimensão retorna um valor 0-100 (opcional, se não houver dados).
O pilar final é a média das dimensões disponíveis.
"""

from typing import Optional, Dict

# ----------------------------------------------------------
# 1. Consistência
# ----------------------------------------------------------
def calcular_consistencia(pontos_ultimos_10: list) -> Optional[float]:
    """
    Mede a regularidade do time (0-100).
    pontos_ultimos_10: lista dos pontos feitos nos últimos 10 jogos (ex.: [3,1,0,3,...])
    Retorna None se menos de 5 jogos ou lista vazia.
    """
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

# ----------------------------------------------------------
# 2. Resiliência
# ----------------------------------------------------------
def calcular_resiliencia(pontos_possiveis: int, pontos_conquistados: int) -> Optional[float]:
    """
    Capacidade de pontuar após sair atrás.
    pontos_possiveis: total de pontos disputados nos jogos em que saiu atrás (3 * n_jogos)
    pontos_conquistados: pontos reais conquistados nesses jogos.
    Retorna None se não houver jogos.
    """
    if pontos_possiveis == 0:
        return None
    return (pontos_conquistados / pontos_possiveis) * 100


# ----------------------------------------------------------
# 3. Confronto Direto
# ----------------------------------------------------------
def calcular_confronto_direto(historico: list) -> Optional[float]:
    """
    Aproveitamento nos últimos confrontos contra o adversário.
    historico: lista de resultados ('V','E','D') nos jogos mais recentes.
    Ex.: ['V','D','E','V','V'] -> 10 pontos em 15 -> 66.7
    Retorna None se menos de 2 jogos.
    """
    if len(historico) < 2:
        return None
    pontos = sum(3 if r == 'V' else 1 if r == 'E' else 0 for r in historico)
    return (pontos / (3 * len(historico))) * 100


# ----------------------------------------------------------
# 4. Moral / Momento
# ----------------------------------------------------------
def calcular_moral(pontos_ultimos_3: int) -> float:
    """
    Moral baseada nos últimos 3 jogos (0-100).
    pontos_ultimos_3: total de pontos conquistados (0 a 9).
    """
    return (pontos_ultimos_3 / 9) * 100


# ----------------------------------------------------------
# 5. Pressão da Partida
# ----------------------------------------------------------
def calcular_pressao_partida(p_obj: float, sensibilidade: float) -> float:
    """
    p_obj: pressão objetiva do jogo (0-100), calculada por regras ou manual.
    sensibilidade: como o time reage à pressão (-1 a +1). Positivo = cresce, negativo = sente.
    Retorna valor entre 0 e 100.
    """
    # Fórmula: 50 + (p_obj - 50) * sensibilidade
    # Se sensibilidade = 0, pressão não afeta (50).
    # Se p_obj = 80 e sensibilidade = 0.5, nota = 50 + 30*0.5 = 65.
    # Se p_obj = 80 e sensibilidade = -0.5, nota = 50 - 15 = 35.
    nota = 50 + (p_obj - 50) * sensibilidade
    return max(0, min(100, nota))


# ----------------------------------------------------------
# Função principal
# ----------------------------------------------------------
def calcular_psicologico(
    consistencia_pontos: Optional[list] = None,
    resiliencia_dados: Optional[tuple] = None,  # (pontos_possiveis, pontos_conquistados)
    confronto_direto_hist: Optional[list] = None,
    moral_pontos: Optional[int] = None,
    pressao_p_obj: Optional[float] = None,
    pressao_sensibilidade: float = 0.0
) -> float:
    """
    Calcula o pilar Psicológico para um time no confronto.
    Todos os parâmetros são opcionais. Se uma dimensão não for fornecida, é ignorada.
    Retorna a média das disponíveis (0-100). Se nenhuma, retorna 50 (neutro).
    """
    notas = []

    if consistencia_pontos is not None:
        c = calcular_consistencia(consistencia_pontos)
        if c is not None:
            notas.append(c)

    if resiliencia_dados is not None:
        r = calcular_resiliencia(*resiliencia_dados)
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
