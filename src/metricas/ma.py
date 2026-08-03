"""
Métrica MA - Momento Atual (v4 — Automático)

Avalia a fase recente de um time combinando:
- Aproveitamento real nos últimos JANELA jogos, ponderado pela força do adversário.
- Peso temporal: jogos mais recentes valem mais.
- Expectativa da odd quando há poucos jogos na temporada.

Compatível com coleta automática do FBref (até 10 jogos).
"""

from typing import List, Optional

# ----------------------------------------------------------
# Parâmetros configuráveis
# ----------------------------------------------------------
N_MIN = 8             # jogos totais na temporada para confiar só no histórico
ALPHA_MA = 3.0        # peso da odd na mistura
JANELA = 10           # número de jogos recentes (ampliado para automático)

# Multiplicadores de dificuldade por prateleira
MULTIPLICADOR_PRATELEIRA = {
    'elite': 1.5,
    'alta': 1.3,
    'media': 1.0,
    'baixa': 0.7,
    'critica': 0.5,
}

# Pesos temporais: jogo mais recente = último da lista = maior peso
PESOS_TEMPORAIS = [0.4, 0.4, 0.5, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2]


def classificar_prateleira(posicao: int) -> str:
    """Retorna a prateleira com base na posição na tabela."""
    if posicao <= 3:
        return 'elite'
    elif posicao <= 7:
        return 'alta'
    elif posicao <= 13:
        return 'media'
    elif posicao <= 16:
        return 'baixa'
    else:
        return 'critica'


def _aproveitamento(pontos: int, jogos: int) -> float:
    """Aproveitamento percentual (0-100)."""
    if jogos == 0:
        return 0.0
    return (pontos / (3 * jogos)) * 100


def _aproveitamento_esperado(prob_vitoria: float, prob_empate: float) -> float:
    """Converte probabilidades justas em aproveitamento esperado (0-100)."""
    if prob_vitoria + prob_empate > 1.0:
        raise ValueError("prob_vitoria + prob_empate > 1.0")
    return (prob_vitoria * 3 + prob_empate * 1) / 3 * 100


def calcular_ma(
    resultados_recentes: List[dict],
    jogos_total_temporada: int,
    prob_vitoria: float,
    prob_empate: float,
    n_min: int = N_MIN,
    alpha: float = ALPHA_MA,
    janela: int = JANELA
) -> float:
    """
    Calcula o Momento Atual (MA) com pesos temporais e por prateleira.

    Parâmetros:
        resultados_recentes: lista dos últimos jogos (máximo 'janela'), cada um como dict:
            {'resultado': 'V'/'E'/'D', 'posicao_adversario': int}
        jogos_total_temporada: total de partidas que o time já fez na liga.
        prob_vitoria: probabilidade justa de vitória no próximo jogo (0-1).
        prob_empate: probabilidade justa de empate no próximo jogo (0-1).
        n_min: jogos totais mínimos para usar 100% histórico.
        alpha: peso da odd na mistura.
        janela: número máximo de jogos recentes considerados.

    Retorna:
        float entre 0 e 100.
    """
    # Limitar ao tamanho da janela
    if len(resultados_recentes) > janela:
        resultados_recentes = resultados_recentes[-janela:]

    n_jogos = len(resultados_recentes)

    # Se a temporada já tem jogos suficientes, usa só o desempenho recente
    if jogos_total_temporada >= n_min:
        if n_jogos == 0:
            return 50.0

        soma_ponderada = 0.0
        soma_pesos = 0.0

        for i, jogo in enumerate(resultados_recentes):
            prat = classificar_prateleira(jogo['posicao_adversario'])
            mult = MULTIPLICADOR_PRATELEIRA.get(prat, 1.0)
            peso_temporal = PESOS_TEMPORAIS[i] if i < len(PESOS_TEMPORAIS) else 1.0
            peso_total = peso_temporal * mult

            if jogo['resultado'] == 'V':
                pontos = 3
            elif jogo['resultado'] == 'E':
                pontos = 1
            else:
                pontos = 0

            soma_ponderada += peso_total * pontos
            soma_pesos += peso_total * 3  # máximo possível

        if soma_pesos == 0:
            return 50.0

        return (soma_ponderada / soma_pesos) * 100

    # Caso contrário, mistura histórico recente com expectativa da odd
    apro_real = _aproveitamento(
        sum(3 if j['resultado'] == 'V' else 1 if j['resultado'] == 'E' else 0 for j in resultados_recentes),
        n_jogos
    )
    apro_esp = _aproveitamento_esperado(prob_vitoria, prob_empate)

    if jogos_total_temporada == 0:
        return apro_esp

    peso_hist = jogos_total_temporada
    peso_odd = alpha
    return (peso_hist * apro_real + peso_odd * apro_esp) / (peso_hist + peso_odd)


def calcular_ma_simples(
    pontos_recentes: int,
    jogos_recentes: int,
    jogos_total_temporada: int,
    prob_vitoria: float,
    prob_empate: float,
    n_min: int = N_MIN,
    alpha: float = ALPHA_MA
) -> float:
    """
    Versão simplificada para uso manual (sem dados de prateleira).
    Mantida para compatibilidade com o modo manual do app.py.
    """
    if jogos_total_temporada >= n_min:
        return _aproveitamento(pontos_recentes, jogos_recentes)

    apro_real = _aproveitamento(pontos_recentes, jogos_recentes)
    apro_esp = _aproveitamento_esperado(prob_vitoria, prob_empate)

    if jogos_total_temporada == 0:
        return apro_esp

    peso_hist = jogos_total_temporada
    peso_odd = alpha
    return (peso_hist * apro_real + peso_odd * apro_esp) / (peso_hist + peso_odd)
