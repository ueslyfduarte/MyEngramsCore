"""
Métrica MA - Momento Atual

Calcula a pontuação de momento de uma equipe para um confronto futuro,
combinando pontos recentes e um ajuste baseado na odd de vitória (1X2)
do jogo futuro, aplicando uma lógica de precificação diferencial.

Fórmula:
    MA = S + k * ( V * odd - D * (1 / odd) )

onde:
    S  = soma dos pontos conquistados nos últimos 0 a 10 jogos
         (3 por vitória, 1 por empate, 0 por derrota)
    V  = número de vitórias no recorte
    D  = número de derrotas no recorte
    odd = odd da equipe para vencer o próximo confronto (fonte: casas de apostas)
    k  = fator de ajuste (default 0.15)
"""

def calcular_ma(pontos_conquistados: float,
                vitorias: int,
                derrotas: int,
                odd_vitoria: float,
                k: float = 0.15) -> float:
    """
    Calcula o Momento Atual (MA) de uma equipe.

    Parâmetros:
        pontos_conquistados: soma de pontos nos últimos jogos (3V, 1E, 0D)
        vitorias: número de vitórias no período
        derrotas: número de derrotas no período
        odd_vitoria: odd para vitória da equipe no próximo jogo
        k: fator de ajuste do bônus/penalidade (default 0.15)

    Retorna:
        float: valor do MA (pode ser negativo se penalidades superarem pontos)
    """
    ajuste = k * (vitorias * odd_vitoria - derrotas * (1.0 / odd_vitoria))
    ma = pontos_conquistados + ajuste
    return ma


def calcular_pontos_e_resultados(resultados: list) -> tuple:
    """
    Auxiliar para converter uma lista de resultados em 
    pontos, vitórias e derrotas.

    Parâmetros:
        resultados: lista de strings 'V', 'E', 'D' (Vitória, Empate, Derrota)
                    ordenada do jogo mais antigo para o mais recente
    Retorna:
        tuple: (pontos, vitorias, derrotas)
    """
    pontos = 0
    v = 0
    d = 0
    for r in resultados:
        if r.upper() == 'V':
            pontos += 3
            v += 1
        elif r.upper() == 'E':
            pontos += 1
        elif r.upper() == 'D':
            d += 1
        else:
            raise ValueError(f"Resultado inválido: {r}. Use 'V', 'E' ou 'D'.")
    return pontos, v, d
