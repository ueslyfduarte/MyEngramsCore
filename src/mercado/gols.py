"""
Módulo de Gols

Calcula probabilidades para mercados de Over/Under (0.5, 1.5, 2.5, 3.5)
e Ambas Marcam (BTTS), combinando a expectativa do modelo com a odd
de Over 2.5 fornecida manualmente.
"""

from typing import Dict, Optional, Tuple
import math

# ----------------------------------------------------------
# Constantes e parâmetros calibráveis
# ----------------------------------------------------------
# Peso dinâmico do mercado: alpha = C / (1 + n_jogos)
C_ALPHA = 10.0

# Coeficientes dos modificadores dos pilares (ajustáveis)
MOD_MA_ALTO = 0.1      # ambos MA > 60
MOD_MA_BAIXO = -0.1    # ambos MA < 40
MOD_PRATELEIRA_DIF = 0.2   # diferença >= 2 prateleiras
MOD_CLASSICO_POUCOS = -0.2 # clássico com histórico de poucos gols (opcional, pode ser manual)
MOD_MORAL_ALTA = 0.1
MOD_PRESSAO_SENSIVEL = -0.1

# ----------------------------------------------------------
# Funções auxiliares
# ----------------------------------------------------------
def poisson_pmf(lmbda: float, k: int) -> float:
    """Probabilidade de Poisson P(X = k)."""
    if lmbda <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lmbda) * (lmbda ** k) / math.factorial(k)


def prob_over(lmbda: float, linha: float) -> float:
    """Probabilidade de mais de `linha` gols (ex.: 2.5 -> P(X >= 3))."""
    p = 0.0
    for k in range(int(linha) + 1):  # soma até floor(linha)
        p += poisson_pmf(lmbda, k)
    return max(0.0, min(1.0, 1.0 - p))


def prob_under(lmbda: float, linha: float) -> float:
    """Probabilidade de menos de `linha` gols (ex.: 2.5 -> P(X <= 2))."""
    p = 0.0
    for k in range(int(linha) + 1):
        p += poisson_pmf(lmbda, k)
    return max(0.0, min(1.0, p))


def prob_btts(lmbda_casa: float, lmbda_fora: float) -> float:
    """
    Probabilidade de Ambas Marcam (BTTS).
    Assume independência: P(ambos marcarem) = (1 - P(0 gols casa)) * (1 - P(0 gols fora)).
    """
    p_casa_marca = 1.0 - poisson_pmf(lmbda_casa, 0)
    p_fora_marca = 1.0 - poisson_pmf(lmbda_fora, 0)
    return p_casa_marca * p_fora_marca


def extrair_lambda_mercado(odd_over25: float, margem: float = 0.05) -> float:
    """
    Estima a média de gols implícita na odd de Over 2.5.
    Remove margem básica (proporcional).
    Retorna lambda estimado via Poisson.
    """
    # Probabilidade implícita ajustada (tirando margem)
    prob_implícita = (1.0 / odd_over25) * (1.0 - margem)
    prob_implícita = max(0.01, min(0.99, prob_implícita))

    # Busca binária para encontrar lambda
    lo, hi = 0.1, 6.0
    for _ in range(30):
        mid = (lo + hi) / 2.0
        p = prob_over(mid, 2.5)
        if p > prob_implícita:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


# ----------------------------------------------------------
# Cálculo do delta de gols (ΔG) a partir dos pilares
# ----------------------------------------------------------
def calcular_delta_gols(
    ma_a: float, ma_b: float,
    fg_a: Dict, fg_b: Dict,    # cada dict deve ter 'ataque', 'defesa' (valores 45-100)
    estilo_a: Dict, estilo_b: Dict,  # dict com scores 0-100 por dimensão
    psic_a: Dict, psic_b: Dict,      # dict com 'moral', 'pressao_sensibilidade' etc.
    ec_a: float, ec_b: float,
    prateleira_a: int, prateleira_b: int,  # 0=Elite, 1=Alta, 2=Média, 3=Baixa, 4=Crítico
) -> float:
    """
    Calcula o ajuste (ΔG) à expectativa-base de gols, usando os pilares.
    Pode ser positivo (mais gols) ou negativo (menos gols).
    """
    delta = 0.0

    # --- MA (Momento Atual) ---
    if ma_a > 60 and ma_b > 60:
        delta += MOD_MA_ALTO
    elif ma_a < 40 and ma_b < 40:
        delta += MOD_MA_BAIXO

    # --- FG (Ataque/Defesa) ---
    # Já será usado na base, aqui podemos adicionar um ajuste extra se ambos ataques fortes e defesas fracas
    ataque_a = fg_a.get('ataque', 50.0)
    ataque_b = fg_b.get('ataque', 50.0)
    defesa_a = fg_a.get('defesa', 50.0)
    defesa_b = fg_b.get('defesa', 50.0)
    # Normalizar para escala ~0-1 em torno de 50
    delta += ((ataque_a + ataque_b - defesa_a - defesa_b) / 100.0) * 0.1

    # --- CPP (Prateleira) ---
    diff_prat = abs(prateleira_a - prateleira_b)
    if diff_prat >= 2:
        delta += MOD_PRATELEIRA_DIF
    # Para clássico com poucos gols, você pode passar como parâmetro adicional se quiser, senão ignora.

    # --- Estilo ---
    # Contribuições de dimensões de estilo
    posse_a = estilo_a.get('posse', 50.0)
    posse_b = estilo_b.get('posse', 50.0)
    transicao_a = estilo_a.get('transicao_rapida', 50.0)
    transicao_b = estilo_b.get('transicao_rapida', 50.0)
    pressao_a = estilo_a.get('pressao_alta', 50.0)
    pressao_b = estilo_b.get('pressao_alta', 50.0)

    # Posse alta reduz gols; transição e pressão aumentam
    delta += ((posse_a + posse_b) / 2.0 - 50.0) * 0.002  # -0.2 no máximo
    delta += ((transicao_a + transicao_b) / 2.0 - 50.0) * 0.004  # +0.3 no máximo
    delta += ((pressao_a + pressao_b) / 2.0 - 50.0) * 0.003

    # --- Psicológico ---
    moral_a = psic_a.get('moral', 50.0)
    moral_b = psic_b.get('moral', 50.0)
    if moral_a > 70 and moral_b > 70:
        delta += MOD_MORAL_ALTA
    # Pressão alta em time sensível
    pressao_obj = psic_a.get('pressao_obj', 50.0)  # se disponível
    sensibilidade = psic_a.get('sensibilidade', 0.0)
    if pressao_obj > 70 and sensibilidade < -0.3:
        delta += MOD_PRESSAO_SENSIVEL
    pressao_obj_b = psic_b.get('pressao_obj', 50.0)
    sensibilidade_b = psic_b.get('sensibilidade', 0.0)
    if pressao_obj_b > 70 and sensibilidade_b < -0.3:
        delta += MOD_PRESSAO_SENSIVEL

    # --- EngramsCore ---
    diff_ec = abs(ec_a - ec_b)
    delta += (diff_ec - 10.0) / 100.0  # se diff > 10, positivo; caso contrário, negativo

    return delta


# ----------------------------------------------------------
# Função principal do mercado de gols
# ----------------------------------------------------------
def calcular_mercado_gols(
    # Dados básicos de gols (médias reais por jogo)
    gols_marcados_a: float, gols_sofridos_a: float,
    gols_marcados_b: float, gols_sofridos_b: float,
    n_jogos: int,                     # número de jogos na temporada (para alfa dinâmico)
    # Pilares (valores já calculados)
    ma_a: float, ma_b: float,
    fg_a: Dict, fg_b: Dict,           # {'ataque': float, 'defesa': float, 'meio': float}
    cpp_a: Optional[float], cpp_b: Optional[float],  # não usamos diretamente, mas pode entrar depois
    estilo_a: Dict, estilo_b: Dict,
    psic_a: Dict, psic_b: Dict,
    ec_a: float, ec_b: float,
    prateleira_a: int, prateleira_b: int,
    # Odd Over 2.5 (fornecida manualmente)
    odd_over25: float,
    # Parâmetros opcionais
    alpha_c: float = C_ALPHA,
) -> Dict[str, float]:
    """
    Retorna um dicionário com probabilidades para diversos mercados de gols.
    """
    # 1. Expectativa-base (média simples de gols totais)
    # Gols esperados totais = (GM_A + GM_B)/2 + (GS_A + GS_B)/2? Vamos usar ataque médio e defesa adversária.
    # Modelo simples: gols_casa = (ataque_casa * defesa_visitante) / média_liga... mas aqui vamos usar as médias reais.
    lambda_base = (gols_marcados_a + gols_sofridos_b + gols_marcados_b + gols_sofridos_a) / 4.0
    # Alternativamente, use ataque_A vs defesa_B e ataque_B vs defesa_A, mas para simplicidade inicial usamos a média.

    # 2. Delta do modelo (ΔG)
    delta = calcular_delta_gols(
        ma_a, ma_b, fg_a, fg_b, estilo_a, estilo_b,
        psic_a, psic_b, ec_a, ec_b, prateleira_a, prateleira_b
    )

    lambda_modelo = max(0.5, lambda_base + delta)

    # 3. Expectativa do mercado (a partir da odd Over 2.5)
    lambda_mercado = extrair_lambda_mercado(odd_over25)

    # 4. Combinação com peso dinâmico
    alpha = alpha_c / (1.0 + n_jogos)
    w_modelo = 1.0 / (1.0 + alpha)
    w_mercado = alpha / (1.0 + alpha)
    lambda_final = w_modelo * lambda_modelo + w_mercado * lambda_mercado

    # 5. Distribuição dos gols entre casa e fora (proporcional ao ataque)
    ataque_a = fg_a.get('ataque', 50.0)
    ataque_b = fg_b.get('ataque', 50.0)
    total_ataque = ataque_a + ataque_b
    if total_ataque == 0:
        frac_a = 0.5
    else:
        frac_a = ataque_a / total_ataque
    lambda_a = lambda_final * frac_a
    lambda_b = lambda_final * (1.0 - frac_a)

    # 6. Cálculo das probabilidades
    probs = {
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
        # Metadados
        'lambda_modelo': round(lambda_modelo, 3),
        'lambda_mercado': round(lambda_mercado, 3),
        'alpha': round(alpha, 3),
        'delta_modelo': round(delta, 3),
    }

    return probs
