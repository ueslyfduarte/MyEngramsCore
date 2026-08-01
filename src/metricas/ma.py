def calcular_ma(pontos_conquistados: float, vitorias: int, derrotas: int, odd_vitoria: float, k: float = 0.15) -> float:
    ajuste = k * (vitorias * odd_vitoria - derrotas * (1.0 / odd_vitoria))
    return pontos_conquistados + ajuste

def calcular_pontos_e_resultados(resultados: list) -> tuple:
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
            raise ValueError(f"Resultado inválido: {r}")
    return pontos, v, d
