# cpp.py
def _aproveitamento(pontos: int, jogos: int) -> float:
    """Aproveitamento percentual (0-100)."""
    if jogos == 0:
        return 0.0
    return (pontos / (3 * jogos)) * 100


def calcular_cpp(pontos: int, jogos: int,
                 prob_vitoria: float, prob_empate: float,
                 n_min: int = 3, alpha: float = 3.0) -> float:
    """
    CPP corrigido: usa probabilidades justas de vitória e empate.

    Parâmetros:
        pontos: total de pontos (3 por vitória, 1 por empate).
        jogos: número de jogos contra a prateleira.
        prob_vitoria: probabilidade justa de vitória (0–1).
        prob_empate: probabilidade justa de empate (0–1).
        n_min: jogos mínimos para confiar só no histórico.
        alpha: peso da odd na mistura.

    Retorna:
        float entre 0 e 100.
    """
    if jogos >= n_min:
        return _aproveitamento(pontos, jogos)

    if prob_vitoria + prob_empate > 1.0:
        raise ValueError("prob_vitoria + prob_empate > 1.0")

    apro_real = _aproveitamento(pontos, jogos)
    pontos_esperados = prob_vitoria * 3 + prob_empate * 1
    apro_esperado = (pontos_esperados / 3) * 100.0

    if jogos == 0:
        return apro_esperado

    return (jogos * apro_real + alpha * apro_esperado) / (jogos + alpha)
