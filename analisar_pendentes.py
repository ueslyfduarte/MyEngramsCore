"""
analisar_pendentes.py — Calcula EngramScore para jogos pendentes

Roda no PC Linux (não no Streamlit Cloud).
Lê a lista de jogos pendentes e gera as análises completas.

Como usar:
    python3 analisar_pendentes.py

Pré-requisitos:
    - Ter rodado coleta_fbref.py antes (para ter os CSVs das ligas)
    - Ter jogos_pendentes.csv na pasta dados/
"""

import pandas as pd
import numpy as np
import math
import os
import sys
from datetime import datetime
from pathlib import Path

# Adicionar raiz do projeto ao path para importar os módulos
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.metricas.ma import calcular_ma_simples, calcular_ma
from src.metricas.fg import calcular_fg
from src.metricas.fg_v2 import calcular_fg_v2
from src.metricas.cpp import calcular_cpp
from src.metricas.estilo import calcular_estilo
from src.metricas.estilo_perfil import obter_perfil_time
from src.metricas.psicologico import (
    calcular_psicologico,
    calcular_pressao_tabela,
    classificar_prateleira,
)

# ========== CONFIGURAÇÕES ==========
PASTA_DADOS = "dados"
PESOS_EC = {'MA': 0.25, 'FG': 0.25, 'CPP': 0.25, 'Psicologico': 0.25}
BONUS_CASA = 2.0


# ========== CARREGAR DADOS DE UMA LIGA ==========
def carregar_dados_liga(chave_liga):
    """Carrega os CSVs de times e médias de uma liga."""
    arquivo_times = os.path.join(PASTA_DADOS, f"{chave_liga}_times.csv")
    arquivo_medias = os.path.join(PASTA_DADOS, f"{chave_liga}_medias.csv")

    if not os.path.exists(arquivo_times) or not os.path.exists(arquivo_medias):
        print(f"❌ Dados não encontrados para: {chave_liga}")
        return None, None

    df_times = pd.read_csv(arquivo_times)
    df_medias = pd.read_csv(arquivo_medias)

    return df_times, df_medias.iloc[0].to_dict()


# ========== BUSCAR ESTATÍSTICAS DE UM TIME ==========
def buscar_time(nome_time, df_times):
    """Busca as estatísticas de um time pelo nome (aproximado)."""
    if df_times is None:
        return None

    # Procurar na primeira coluna (geralmente 'Squad')
    col_nome = df_times.columns[0]

    # Busca por correspondência parcial
    for idx, row in df_times.iterrows():
        nome_na_tabela = str(row[col_nome]).lower()
        if nome_time.lower() in nome_na_tabela or nome_na_tabela in nome_time.lower():
            return row

    return None


# ========== CALCULAR ENGRAMSCORE PARA UM JOGO ==========
def analisar_jogo(casa_nome, fora_nome, chave_liga, odds=None):
    """Calcula o EngramScore completo para um confronto."""

    print(f"\n⚽ Analisando: {casa_nome} x {fora_nome} ({chave_liga})")

    # Carregar dados da liga
    df_times, medias_liga = carregar_dados_liga(chave_liga)
    if df_times is None:
        return None

    # Buscar estatísticas dos times
    dados_casa = buscar_time(casa_nome, df_times)
    dados_fora = buscar_time(fora_nome, df_times)

    if dados_casa is None:
        print(f"❌ Time não encontrado: {casa_nome}")
        return None
    if dados_fora is None:
        print(f"❌ Time não encontrado: {fora_nome}")
        return None

    # Extrair médias por jogo (valores padrão se não encontrados)
    def extrair_metrica(row, padroes, default=0.0):
        for padrao in padroes:
            colunas = [c for c in row.index if padrao.lower() in str(c).lower()]
            if colunas:
                try:
                    return float(row[colunas[0]])
                except:
                    continue
        return default

    # Métricas de ataque
    gm_casa = extrair_metrica(dados_casa, ['Gls', 'Goals'])
    fa_casa = extrair_metrica(dados_casa, ['SoT'])
    eca_casa = extrair_metrica(dados_casa, ['CK'])
    posse_casa = extrair_metrica(dados_casa, ['Poss'])

    gm_fora = extrair_metrica(dados_fora, ['Gls', 'Goals'])
    fa_fora = extrair_metrica(dados_fora, ['SoT'])
    eca_fora = extrair_metrica(dados_fora, ['CK'])
    posse_fora = extrair_metrica(dados_fora, ['Poss'])

    # Métricas de defesa
    gs_casa = extrair_metrica(dados_casa, ['GA', 'Goals Against'])
    fas_casa = extrair_metrica(dados_casa, ['SoTA'])
    des_casa = extrair_metrica(dados_casa, ['Tkl'])

    gs_fora = extrair_metrica(dados_fora, ['GA', 'Goals Against'])
    fas_fora = extrair_metrica(dados_fora, ['SoTA'])
    des_fora = extrair_metrica(dados_fora, ['Tkl'])

    # Disciplina
    fc_casa = extrair_metrica(dados_casa, ['Fls'])
    ca_casa = extrair_metrica(dados_casa, ['CrdY'])
    fc_fora = extrair_metrica(dados_fora, ['Fls'])
    ca_fora = extrair_metrica(dados_fora, ['CrdY'])

    # Número de jogos (estimado)
    n_jogos_casa = 20  # idealmente viria do CSV
    n_jogos_fora = 20

    # FG (usando v2 se disponível, senão v1)
    dados_dict_casa = {
        'GM': gm_casa, 'FA': fa_casa, 'ECa': eca_casa, 'Posse': posse_casa,
        'GS': gs_casa, 'FAS': fas_casa, 'ECc': 0, 'Des': des_casa,
        'FC': fc_casa, 'CA': ca_casa
    }
    dados_dict_fora = {
        'GM': gm_fora, 'FA': fa_fora, 'ECa': eca_fora, 'Posse': posse_fora,
        'GS': gs_fora, 'FAS': fas_fora, 'ECc': 0, 'Des': des_fora,
        'FC': fc_fora, 'CA': ca_fora
    }

    fg_A = calcular_fg(dados_dict_casa, medias_liga, n_jogos_casa)
    fg_B = calcular_fg(dados_dict_fora, medias_liga, n_jogos_fora)

    # CPP (simplificado - usa valores padrão)
    cpp_A = 50.0
    cpp_B = 50.0

    # Estilo
    estilo_A = calcular_estilo(dados_dict_casa, medias_liga, n_jogos_casa)
    estilo_B = calcular_estilo(dados_dict_fora, medias_liga, n_jogos_fora)

    # Perfil tático
    perfil_A = obter_perfil_time(dados_dict_casa, medias_liga)
    perfil_B = obter_perfil_time(dados_dict_fora, medias_liga)

    # MA (simplificado)
    ma_A = 50.0
    ma_B = 50.0

    # Psicológico (simplificado)
    psic_A = 50.0
    psic_B = 50.0

    # Calcular EC
    EC_A = (ma_A * 0.25 + fg_A * 0.25 + cpp_A * 0.25 + psic_A * 0.25) + BONUS_CASA
    EC_B = (ma_B * 0.25 + fg_B * 0.25 + cpp_B * 0.25 + psic_B * 0.25)
    EC_A = max(0, min(100, EC_A))
    EC_B = max(0, min(100, EC_B))

    # Probabilidades 1X2
    total = EC_A + EC_B
    diff_ec = abs(EC_A - EC_B)
    LIMIAR_EMPATE = 5.0
    BONUS_MAX = 0.06
    P_EMP_BASE = 0.29
    P_EMP_MIN = 0.18

    if diff_ec < LIMIAR_EMPATE:
        p_emp = P_EMP_BASE + (1 - diff_ec / LIMIAR_EMPATE) * BONUS_MAX
    else:
        p_emp = max(P_EMP_MIN, P_EMP_BASE - (diff_ec / 100) * 0.15)

    p_A = (1 - p_emp) * (EC_A / total) if total > 0 else 0.33
    p_B = 1 - p_A - p_emp

    # Lambda e gols
    lambda_casa = (gm_casa + gs_fora) / 2
    lambda_fora = (gm_fora + gs_casa) / 2

    # Ajustar pelo EC
    fator = (EC_A - EC_B) / 100.0
    lambda_casa_adj = max(0, lambda_casa * (1 + fator * 0.5))
    lambda_fora_adj = max(0, lambda_fora * (1 - fator * 0.5))

    # Poisson
    results = []
    for i in range(6):
        for j in range(6):
            prob = math.exp(-lambda_casa_adj)*(lambda_casa_adj**i)/math.factorial(i) * \
                   math.exp(-lambda_fora_adj)*(lambda_fora_adj**j)/math.factorial(j)
            results.append((i, j, prob))

    over15 = sum(p for gA, gB, p in results if gA+gB > 1.5)
    over25 = sum(p for gA, gB, p in results if gA+gB > 2.5)
    over35 = sum(p for gA, gB, p in results if gA+gB > 3.5)
    btts = sum(p for gA, gB, p in results if gA > 0 and gB > 0)

    # Gol 1º tempo
    FATOR_HT = 0.44
    ajuste_estilo = 0
    if perfil_A in ["Pressão Alta", "Dominante"]:
        ajuste_estilo += 0.05
    if perfil_B in ["Pressão Alta", "Dominante"]:
        ajuste_estilo -= 0.05
    lambda_ht = (lambda_casa_adj + lambda_fora_adj) * (FATOR_HT + ajuste_estilo)
    prob_gol_ht = 1 - math.exp(-lambda_ht)

    # Identificar resultado mais provável
    if p_A >= p_B and p_A >= p_emp:
        resultado_previsto = f"Vitória {casa_nome}"
        prob_vencedor = p_A
    elif p_B >= p_A and p_B >= p_emp:
        resultado_previsto = f"Vitória {fora_nome}"
        prob_vencedor = p_B
    else:
        resultado_previsto = "Empate"
        prob_vencedor = p_emp

    return {
        "casa": casa_nome,
        "fora": fora_nome,
        "liga": chave_liga,
        "EC_A": round(EC_A, 1),
        "EC_B": round(EC_B, 1),
        "p_A": round(p_A * 100, 1),
        "p_emp": round(p_emp * 100, 1),
        "p_B": round(p_B * 100, 1),
        "over15": round(over15 * 100, 1),
        "over25": round(over25 * 100, 1),
        "over35": round(over35 * 100, 1),
        "btts": round(btts * 100, 1),
        "gol_ht": round(prob_gol_ht * 100, 1),
        "resultado_previsto": resultado_previsto,
        "prob_vencedor": round(prob_vencedor * 100, 1),
        "perfil_casa": perfil_A,
        "perfil_fora": perfil_B,
        "fg_casa": round(fg_A, 1),
        "fg_fora": round(fg_B, 1),
        "analisado_em": datetime.now().strftime('%Y-%m-%d %H:%M'),
    }


# ========== EXECUÇÃO PRINCIPAL ==========
if __name__ == "__main__":
    print("⚽ ENGRAMSCORE — Análise de Jogos Pendentes")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # Carregar lista de jogos pendentes
    arquivo_pendentes = os.path.join(PASTA_DADOS, "jogos_pendentes.csv")

    if not os.path.exists(arquivo_pendentes):
        print("❌ Arquivo jogos_pendentes.csv não encontrado!")
        print("💡 Adicione jogos pelo app Streamlit antes de rodar este script.")
        sys.exit(1)

    df_pendentes = pd.read_csv(arquivo_pendentes)

    if df_pendentes.empty:
        print("❌ Nenhum jogo pendente para analisar.")
        sys.exit(0)

    print(f"📋 {len(df_pendentes)} jogos pendentes encontrados.\n")

    # Analisar cada jogo
    analises = []

    for idx, row in df_pendentes.iterrows():
        casa = row.get('casa', row.get('time_casa', ''))
        fora = row.get('fora', row.get('time_fora', ''))
        liga = row.get('liga', 'brasileirao_serie_a')

        resultado = analisar_jogo(casa, fora, liga)

        if resultado:
            analises.append(resultado)
            print(f"✅ {casa} x {fora}: {resultado['resultado_previsto']} ({resultado['prob_vencedor']}%)")
        else:
            print(f"❌ Falha ao analisar: {casa} x {fora}")

    # Salvar resultados
    if analises:
        df_resultados = pd.DataFrame(analises)
        arquivo_saida = os.path.join(PASTA_DADOS, "analises_prontas.csv")
        df_resultados.to_csv(arquivo_saida, index=False)
        print(f"\n✅ {len(analises)} análises salvas em: {arquivo_saida}")
    else:
        print("\n❌ Nenhuma análise foi concluída.")
