"""
Módulo de Gols
Calcula probabilidades para mercados de Over/Under e Ambas Marcam (BTTS),
combinando a expectativa do modelo com a odd de Over 2.5 fornecida manualmente.
"""

from typing import Dict, Optional, Tuple
import math

# Constantes calibráveis
C_ALPHA = 10.0
MOD_MA_ALTO = 0.1
MOD_MA_BAIXO = -0.1
MOD_PRATELEIRA_DIF = 0.2
MOD_CLASSICO_POUCOS = -0.2
MOD_MORAL_ALTA = 0.1
MOD_PRESSAO_SENSIVEL = -0.1

def poisson_pmf(lmbda: float, k: int) -> float:
    if lmbda <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lmbda) * (lmbda ** k) / math.factorial(k)

def prob_over(lmbda: float, linha: float) -> float:
    p = 0.0
    for k in range(int(linha) + 1):
        p += poisson_pmf(lmbda, k)
    return max(0.0, min(1.0, 1.0 - p))

def prob_under(lmbda: float, linha: float) -> float:
    p = 0.0
    for k in range(int(linha) + 1):
        p += poisson_pmf(lmbda, k)
    return max(0.0, min(1.0, p))

def prob_btts(lmbda_casa: float, lmbda_fora: float) -> float:
    p_casa_marca = 1.0 - poisson_pmf(lmbda_casa, 0)
    p_fora_marca = 1.0 - poisson_pmf(lmbda_fora, 0)
    return p_casa_marca * p_fora_marca

def extrair_lambda_mercado(odd_over25: float, margem: float = 0.05) -> float:
    prob_implícita = (1.0 / odd_over25) * (1.0 - margem)
    prob_implícita = max(0.01, min(0.99, prob_implícita))
    lo, hi = 0.1, 6.0
    for _ in range(30):
        mid = (lo + hi) / 2.0
        p = prob_over(mid, 2.5)
        if p > prob_implícita:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0

def calcular_delta_gols(
    ma_a: float, ma_b: float,
    fg_a: Dict, fg_b: Dict,
    estilo_a: Dict, estilo_b: Dict,
    psic_a: Dict, psic_b: Dict,
    ec_a: float, ec_b: float,
    prateleira_a: int, prateleira_b: int,
) -> float:
    delta = 0.0
    if ma_a > 60 and ma_b > 60:
        delta += MOD_MA_ALTO
    elif ma_a < 40 and ma_b < 40:
        delta += MOD_MA_BAIXO

    ataque_a = fg_a.get('ataque', 50.0)
    ataque_b = fg_b.get('ataque', 50.0)
    defesa_a = fg_a.get('defesa', 50.0)
    defesa_b = fg_b.get('defesa', 50.0)
    delta += ((ataque_a + ataque_b - defesa_a - defesa_b) / 100.0) * 0.1

    diff_prat = abs(prateleira_a - prateleira_b)
    if diff_prat >= 2:
        delta += MOD_PRATELEIRA_DIF

    posse_a = estilo_a.get('posse', 50.0)
    posse_b = estilo_b.get('posse', 50.0)
    transicao_a = estilo_a.get('transicao_rapida', 50.0)
    transicao_b = estilo_b.get('transicao_rapida', 50.0)
    pressao_a = estilo_a.get('pressao_alta', 50.0)
    pressao_b = estilo_b.get('pressao_alta', 50.0)

    delta += ((posse_a + posse_b) / 2.0 - 50.0) * 0.002
    delta += ((transicao_a + transicao_b) / 2.0 - 50.0) * 0.004
    delta += ((pressao_a + pressao_b) / 2.0 - 50.0) * 0.003

    moral_a = psic_a.get('moral', 50.0)
    moral_b = psic_b.get('moral', 50.0)
    if moral_a > 70 and moral_b > 70:
        delta += MOD_MORAL_ALTA
    pressao_obj = psic_a.get('pressao_obj', 50.0)
    sensibilidade = psic_a.get('sensibilidade', 0.0)
    if pressao_obj > 70 and sensibilidade < -0.3:
        delta += MOD_PRESSAO_SENSIVEL
    pressao_obj_b = psic_b.get('pressao_obj', 50.0)
    sensibilidade_b = psic_b.get('sensibilidade', 0.0)
    if pressao_obj_b > 70 and sensibilidade_b < -0.3:
        delta += MOD_PRESSAO_SENSIVEL

    diff_ec = abs(ec_a - ec_b)
    delta += (diff_ec - 10.0) / 100.0

    return delta

def calcular_mercado_gols(
    gols_marcados_a: float, gols_sofridos_a: float,
    gols_marcados_b: float, gols_sofridos_b: float,
    n_jogos: int,
    ma_a: float, ma_b: float,
    fg_a: Dict, fg_b: Dict,
    cpp_a: Optional[float], cpp_b: Optional[float],
    estilo_a: Dict, estilo_b: Dict,
    psic_a: Dict, psic_b: Dict,
    ec_a: float, ec_b: float,
    prateleira_a: int, prateleira_b: int,
    odd_over25: float,
    alpha_c: float = C_ALPHA,
) -> Dict[str, float]:
    lambda_base = (gols_marcados_a + gols_sofridos_b + gols_marcados_b + gols_sofridos_a) / 4.0

    delta = calcular_delta_gols(
        ma_a, ma_b, fg_a, fg_b, estilo_a, estilo_b,
        psic_a, psic_b, ec_a, ec_b, prateleira_a, prateleira_b
    )

    lambda_modelo = max(0.5, lambda_base + delta)
    lambda_mercado = extrair_lambda_mercado(odd_over25)
    alpha = alpha_c / (1.0 + n_jogos)
    w_modelo = 1.0 / (1.0 + alpha)
    w_mercado = alpha / (1.0 + alpha)
    lambda_final = w_modelo * lambda_modelo + w_mercado * lambda_mercado

    ataque_a = fg_a.get('ataque', 50.0)
    ataque_b = fg_b.get('ataque', 50.0)
    total_ataque = ataque_a + ataque_b
    frac_a = ataque_a / total_ataque if total_ataque != 0 else 0.5
    lambda_a = lambda_final * frac_a
    lambda_b = lambda_final * (1.0 - frac_a)

    return {
        'lambda_final': round(lambda_final, 3),
        'over_0.5': round(prob_over(lambda_final, 0.5), 4),
        'under_0.5': round(prob_under(lambda_final, 0.5), 4),
        'over_1.5': round(prob_over(lambda_final, 1.5), 4),
        'under_1.5': round(prob_under(lambda_final, 1.5), 4),
        'over_2.5': round(prob_over(lambda_final, 2.5), 4),
        'under_2.5': round(prob_under(lambda_final, 2.5), 4),
        'over_3.5': round(prob_over(lambda_final, 3.5), 4),
        'under_3.5': round(prob_under(lambda_final, 3.5), 4),
        'btts_yes': round(prob_btts(lambda_a, lambda_b), 4),
        'btts_no': round(1.0 - prob_btts(lambda_a, lambda_b), 4),
        'lambda_modelo': round(lambda_modelo, 3),
        'lambda_mercado': round(lambda_mercado, 3),
        'alpha': round(alpha, 3),
        'delta_modelo': round(delta, 3),
    }
