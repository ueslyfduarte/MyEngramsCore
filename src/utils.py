"""
Utilitários compartilhados entre os pilares do método.
"""

from typing import List, Optional

# ----------------------------------------------------------
# Constantes
# ----------------------------------------------------------
LIMITE_INFERIOR = 45.0
LIMITE_SUPERIOR = 100.0
PRIOR_PADRAO = 50.0
ALPHA_PADRAO = 5

# Códigos de indicadores que são "menor é melhor"
INDICADORES_INVERTIDOS = {
    'GS', 'xGA', 'FAS', 'TC', 'ECc',   # defesa
    'FC', 'CA',                        # disciplina (se interpretado como menor = melhor)
}


# ----------------------------------------------------------
# Normalização robusta
# ----------------------------------------------------------
def normalizar_indicador(valor_time: float,
                         media_liga: float,
                         menor_melhor: bool = False) -> float:
    """
    Normaliza um indicador em relação à média da liga.

    - Calcula a diferença percentual (valor - média) / média.
    - Limita essa diferença entre -1 e 1 para evitar distorções extremas.
    - Inverte o sinal se menor_melhor=True.
    - Converte para escala 0-100 com centro 50.
    """
    if media_liga == 0:
        return PRIOR_PADRAO

    pct = (valor_time - media_liga) / media_liga
    if menor_melhor:
        pct = -pct

    pct = max(-1.0, min(1.0, pct))
    nota = 50.0 + pct * 50.0
    return max(0.0, min(100.0, nota))


# ----------------------------------------------------------
# Atualização bayesiana
# ----------------------------------------------------------
def atualizacao_bayesiana(prior: float,
                          bruto: float,
                          n_jogos: int,
                          alpha: float = ALPHA_PADRAO) -> float:
    """Combina o prior com a observação, ponderando pelo número de jogos."""
    if n_jogos + alpha == 0:
        return prior
    return (alpha * prior + n_jogos * bruto) / (alpha + n_jogos)


# ----------------------------------------------------------
# Truncamento e média
# ----------------------------------------------------------
def truncar(valor: float,
            minimo: float = LIMITE_INFERIOR,
            maximo: float = LIMITE_SUPERIOR) -> float:
    """Limita o valor entre minimo e maximo."""
    return max(minimo, min(maximo, valor))


def media_ativos(valores: List[Optional[float]]) -> Optional[float]:
    """Média dos valores não None. Retorna None se todos forem None."""
    validos = [v for v in valores if v is not None]
    if not validos:
        return None
    return sum(validos) / len(validos)
