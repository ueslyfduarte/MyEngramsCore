import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Optional, Tuple

from src.metricas.ma import calcular_ma, calcular_pontos_e_resultados
from src.metricas.fg import calcular_fg
from src.metricas.cpp import calcular_cpp
from src.metricas.estilo import calcular_vetor_estilo, calcular_estilo
from src.metricas.psicologico import calcular_psicologico
from src.mercados.gols import calcular_mercado_gols

# ==================== ENGRAMS CORE (com empate realista) ====================
PESOS_PADRAO = {
    'MA': 0.20,
    'FG': 0.25,
    'CPP': 0.20,
    'Estilo': 0.20,
    'Psicologico': 0.15,
}
THR_MANDANTE = 10
THR_VISITANTE = 8

def _redistribuir_pesos(pilares_disponiveis, pesos):
    ativos = {k: v for k, v in pilares_disponiveis.items() if v is not None}
    if not ativos:
        return {}
    peso_total = sum(pesos.get(k, 0.0) for k in ativos)
    if peso_total == 0:
        n = len(ativos)
        return {k: 1.0/n for k in ativos}
    return {k: pesos.get(k, 0.0)/peso_total for k in ativos}

def _aplicar_fator_casa(ma_casa, ma_fora, thr_casa=THR_MANDANTE, thr_fora=THR_VISITANTE):
    if ma_casa - ma_fora >= thr_casa:
        return 1.0, 0.0
    elif ma_fora - ma_casa >= thr_fora:
        return 0.0, 1.0
    else:
        return 0.0, 0.0

def calcular_engramscore(
    ma_a=None, fg_a=None, cpp_a=None, estilo_a=None, psicologico_a=None,
    ma_b=None, fg_b=None, cpp_b=None, estilo_b=None, psicologico_b=None,
    time_mandante='A', pesos=None, thr_mandante=THR_MANDANTE, thr_visitante=THR_VISITANTE
) -> Dict[str, float]:
    if pesos is None:
        pesos = PESOS_PADRAO.copy()

    pilares_a = {'MA': ma_a, 'FG': fg_a, 'CPP': cpp_a, 'Estilo': estilo_a, 'Psicologico': psicologico_a}
    pilares_b = {'MA': ma_b, 'FG': fg_b, 'CPP': cpp_b, 'Estilo': estilo_b, 'Psicologico': psicologico_b}

    ativos_ambos = {p for p in pilares_a if pilares_a[p] is not None and pilares_b[p] is not None}
    if not ativos_ambos:
        return {'EC_A': 50.0, 'EC_B': 50.0, 'P_A': 0.333, 'P_B': 0.333, 'P_E': 0.334, 'P_A_ou_E': 0.667, 'P_B_ou_E': 0.667}

    peso_ativos = {p: pesos[p] for p in ativos_ambos}
    soma_pesos = sum(peso_ativos.values())
    pesos_norm = {p: w/soma_pesos for p, w in peso_ativos.items()}

    ec_a = sum(pesos_norm[p] * pilares_a[p] for p in pesos_norm)
    ec_b = sum(pesos_norm[p] * pilares_b[p] for p in pesos_norm)

    bonus_a = bonus_b = 0.0
    if ma_a is not None and ma_b is not None:
        if time_mandante == 'A':
            b_a, b_b = _aplicar_fator_casa(ma_a, ma_b, thr_mandante, thr_visitante)
        elif time_mandante == 'B':
            b_b, b_a = _aplicar_fator_casa(ma_b, ma_a, thr_mandante, thr_visitante)
        else:
            raise ValueError("time_mandante deve ser 'A' ou 'B'")
        bonus_a, bonus_b = b_a, b_b

    ec_a = max(0.0, min(100.0, ec_a + bonus_a))
    ec_b = max(0.0, min(100.0, ec_b + bonus_b))

    # Probabilidade de empate baseada na diferença relativa
    soma = ec_a + ec_b
    if soma == 0:
        p_a = p_b = 0.333
        p_e = 0.334
    else:
        diff_rel = abs(ec_a - ec_b) / soma  # 0 a 1
        p_e = max(0.10, 0.35 - diff_rel * 0.3)  # mínimo 10% de empate
        p_a = (1.0 - p_e) * (ec_a / soma)
        p_b = (1.0 - p_e) * (ec_b / soma)

    return {
        'EC_A': round(ec_a, 2),
        'EC_B': round(ec_b, 2),
        'P_A': round(p_a, 4),
        'P_B': round(p_b, 4),
        'P_E': round(p_e, 4),
        'P_A_ou_E': round(p_a + p_e, 4),
        'P_B_ou_E': round(p_b + p_e, 4),
    }

# ==================== FUNÇÕES DE DESCRIÇÃO ====================
def descrever_fg(valor, nome):
    if valor >= 70: return f"{nome} apresenta **Força Geral muito acima da média** ({valor:.0f})."
    elif valor >= 55: return f"{nome} tem **Força Geral acima da média** ({valor:.0f})."
    elif valor >= 45: return f"{nome} está com **Força Geral dentro da média** ({valor:.0f})."
    else: return f"{nome} mostra **Força Geral abaixo da média** ({valor:.0f})."

def descrever_estilo(vetor, nome):
    if not vetor: return ""
    dims = [(k, v) for k, v in vetor.items() if v is not None]
    if not dims: return ""
    dim_max, valor_max = max(dims, key=lambda x: x[1])
    nomes = {
        'posse': 'Posse/Paciência', 'pressao_alta': 'Pressão Alta', 'contra_ataque': 'Contra-ataque',
        'jogo_laterais': 'Jogo pelas Laterais', 'jogo_meio': 'Jogo pelo Meio',
        'transicao_rapida': 'Transição Rápida', 'defesa_bloco_baixo': 'Defesa em Bloco Baixo',
        'pressao_pos_perda': 'Pressão Pós-Perda'
    }
    nome_dim = nomes.get(dim_max, dim_max)
    return f"{nome} se destaca no estilo **{nome_dim}** ({valor_max:.0f}/100)."

def gerar_descricao_completa(nome, ma, fg, cpp, estilo, psic, vetor_estilo, dados_fg, dados_estilo, prat):
    linhas = []
    linhas.append(f"### {nome}")
    linhas.append(descrever_fg(fg, nome))
    if ma is not None:
        if ma >= 70: linhas.append(f"O Momento Atual é excelente ({ma:.0f}), indicando ótima fase.")
        elif ma >= 50: linhas.append(f"O Momento Atual é estável ({ma:.0f}).")
        else: linhas.append(f"O Momento Atual preocupa ({ma:.0f}), mostrando fase ruim.")
    if cpp is not None:
        if cpp >= 70: linhas.append(f"Histórico muito favorável contra esta prateleira ({cpp:.0f}).")
        elif cpp >= 50: linhas.append(f"Histórico equilibrado contra esta prateleira ({cpp:.0f}).")
        else: linhas.append(f"Histórico desfavorável contra esta prateleira ({cpp:.0f}).")
    if vetor_estilo:
        linhas.append(descrever_estilo(vetor_estilo, nome))
    if psic is not None:
        if psic >= 70: linhas.append(f"Fator psicológico muito positivo ({psic:.0f}).")
        elif psic >= 45: linhas.append(f"Fator psicológico neutro ({psic:.0f}).")
        else: linhas.append(f"Fator psicológico pode atrapalhar ({psic:.0f}).")
    return "\n".join(linhas)

# ==================== INTERFACE STREAMLIT ====================
st.set_page_config(page_title="EngramsCore ⚽", page_icon="⚽", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0a0a0a; color: #FFD700; }
    h1, h2, h3, h4, h5, h6 { color: #FFD700 !important; }
    .stProgress > div > div { background-color: #FFD700; }
    .stMetric label, .stMetric [data-testid="stMetricValue"] { color: #FFD700 !important; }
    .stButton>button, .stTextInput>div>input, .stNumberInput>div>input {
        background-color: #2a2a2a; color: #FFD700; border: 1px solid #FFD700; border-radius: 5px;
    }
    .stSlider>div>div>div { background-color: #FFD700; }
    .big-card {
        background: #1a1a1a; border: 1px solid #FFD700; border-radius: 15px;
        padding: 20px; margin: 10px 0; box-shadow: 0 0 20px rgba(255,215,0,0.2);
    }
    .winner-card {
        border: 2px solid #FFD700; box-shadow: 0 0 30px rgba(255,215,0,0.6);
    }
    .metric-row { display: flex; justify-content: space-between; }
    .selo { background-color: #FFD700; color: #0a0a0a; padding: 5px 10px; border-radius: 20px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ ENGRAMS CORE")
st.markdown("<p style='color:#FFD700; font-size:1.2em;'>Sistema de Análise Esportiva Diferencial</p>", unsafe_allow_html=True)

# ==================== ENTRADA DE DADOS ====================
st.header("📝 Dados do Confronto")

st.subheader("📊 Liga (Referências)")
col_l1, col_l2, col_l3 = st.columns(3)
with col_l1:
    l_gm = st.number_input("Média Gols marcados/j", 0.1, 5.0, 1.4, 0.1, key="l_gm")
    l_fa = st.number_input("Média Finalizações alvo/j", 0.0, 10.0, 4.0, 0.1, key="l_fa")
    l_xg = st.number_input("Média xG/j", 0.0, 5.0, 1.4, 0.1, key="l_xg")
    l_posse = st.number_input("Média Posse %", 0.0, 100.0, 50.0, 1.0, key="l_posse")
with col_l2:
    l_gs = st.number_input("Média Gols sofridos/j", 0.1, 5.0, 1.4, 0.1, key="l_gs")
    l_xga = st.number_input("Média xG contra/j", 0.0, 5.0, 1.4, 0.1, key="l_xga")
    l_cb = st.number_input("Média Chutes bloqueados/j", 0.0, 10.0, 2.0, 0.1, key="l_cb")
with col_l3:
    l_ppda = st.number_input("Média PPDA", 0.0, 20.0, 10.0, 0.1, key="l_ppda")
    l_acoes_to = st.number_input("Média Desarmes/j", 0.0, 50.0, 15.0, 0.1, key="l_acoes_to")
    l_gols_ca = st.number_input("Média Gols contra-ataque/j", 0.0, 5.0, 0.5, 0.1, key="l_gols_ca")
    l_passes_longos = st.number_input("Média Passes longos/j", 0.0, 100.0, 40.0, 0.1, key="l_passes_longos")
    l_cruzamentos = st.number_input("Média Cruzamentos/j", 0.0, 50.0, 15.0, 0.1, key="l_cruzamentos")
    l_escanteios = st.number_input("Média Escanteios/j", 0.0, 20.0, 5.0, 0.1, key="l_escanteios")
    l_chutes_trans = st.number_input("Média Chutes transição/j", 0.0, 10.0, 3.0, 0.1, key="l_chutes_trans")

medias_liga = {
    'GM': l_gm, 'FA': l_fa, 'xG': l_xg, 'GS': l_gs, 'xGA': l_xga, 'CB': l_cb,
    'Posse': l_posse, 'posse': l_posse, 'ppda': l_ppda, 'acoes_to': l_acoes_to,
    'gols_ca': l_gols_ca, 'passes_longos': l_passes_longos,
    'cruzamentos': l_cruzamentos, 'escanteios': l_escanteios, 'chutes_trans': l_chutes_trans
}

st.markdown("---")
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("🏠 Time A (Mandante)")
    nome_a = st.text_input("Nome", "Time A", key="nome_a")
    n_jogos_a = st.number_input("Jogos na temporada", 1, 38, 10, key="nj_a")
    odd_a = st.number_input("Odd Vitória", 1.01, 10.0, 1.80, 0.01, key="odd_a")
    res_a = st.text_input("Últ. resultados (V/E/D)", "VVEDV", key="res_a").upper()
    gm_a = st.number_input("Gols/jogo", 0.0, 5.0, 2.0, 0.1, key="gm_a")
    fa_a = st.number_input("Finalizações alvo/j", 0.0, 10.0, 4.5, 0.1, key="fa_a")
    xg_a = st.number_input("xG/j", 0.0, 5.0, 1.8, 0.1, key="xg_a")
    gs_a = st.number_input("Gols sofridos/j", 0.0, 5.0, 0.8, 0.1, key="gs_a")
    xga_a = st.number_input("xG contra/j", 0.0, 5.0, 0.9, 0.1, key="xga_a")
    cb_a = st.number_input("Chutes bloqueados/j", 0.0, 10.0, 2.0, 0.1, key="cb_a")
    posse_a = st.slider("Posse %", 0, 100, 55, key="posse_a")
    pts_cpp_a = st.number_input("Pontos CPP", 0, 30, 6, key="pcpp_a")
    jogos_cpp_a = st.number_input("Jogos CPP", 0, 10, 3, key="jcpp_a")
    dados_estilo_a = {}
    posse_est_a = st.number_input("Posse % (estilo)", 0.0, 100.0, 55.0, key="a_posse")
    if posse_est_a > 0: dados_estilo_a['posse'] = posse_est_a
    ppda_a = st.number_input("PPDA", 0.0, 20.0, 0.0, key="a_ppda")
    if ppda_a > 0: dados_estilo_a['ppda'] = ppda_a
    acoes_to_a = st.number_input("Desarmes/j", 0.0, 50.0, 0.0, key="a_acoes_to")
    if acoes_to_a > 0: dados_estilo_a['acoes_to'] = acoes_to_a
    gols_ca_a = st.number_input("Gols contra-ataque/j", 0.0, 5.0, 0.0, key="a_gols_ca")
    if gols_ca_a > 0: dados_estilo_a['gols_ca'] = gols_ca_a
    chutes_trans_a = st.number_input("Chutes transição/j", 0.0, 10.0, 0.0, key="a_chutes_trans")
    if chutes_trans_a > 0: dados_estilo_a['chutes_trans'] = chutes_trans_a
    cruzamentos_a = st.number_input("Cruzamentos/j", 0.0, 50.0, 0.0, key="a_cruzamentos")
    if cruzamentos_a > 0: dados_estilo_a['cruzamentos'] = cruzamentos_a
    escanteios_a = st.number_input("Escanteios/j", 0.0, 20.0, 0.0, key="a_escanteios")
    if escanteios_a > 0: dados_estilo_a['escanteios'] = escanteios_a
    passes_longos_a = st.number_input("Passes longos/j", 0.0, 100.0, 0.0, key="a_passes_longos")
    if passes_longos_a > 0: dados_estilo_a['passes_longos'] = passes_longos_a
    cons_a = st.text_input("Últ. 10 resultados (psic.)", "VVEDVVEDVV", key="cons_a").upper()
    moral_a = st.slider("Moral (pts 3j)", 0, 9, 6, key="moral_a")
    p_obj_a = st.slider("Pressão", 0, 100, 40, key="pobj_a")
    sens_a = st.slider("Sensibilidade", -1.0, 1.0, 0.0, 0.1, key="sens_a")
    prat_a = st.selectbox("Prateleira", ["Elite","Alta","Média","Baixa","Crítico"], key="prat_a")

with col_b:
    st.subheader("✈️ Time B (Visitante)")
    nome_b = st.text_input("Nome", "Time B", key="nome_b")
    n_jogos_b = st.number_input("Jogos na temporada", 1, 38, 10, key="nj_b")
    odd_b = st.number_input("Odd Vitória", 1.01, 10.0, 4.00, 0.01, key="odd_b")
    res_b = st.text_input("Últ. resultados (V/E/D)", "DDVVE", key="res_b").upper()
    gm_b = st.number_input("Gols/jogo", 0.0, 5.0, 1.2, 0.1, key="gm_b")
    fa_b = st.number_input("Finalizações alvo/j", 0.0, 10.0, 3.2, 0.1, key="fa_b")
    xg_b = st.number_input("xG/j", 0.0, 5.0, 1.2, 0.1, key="xg_b")
    gs_b = st.number_input("Gols sofridos/j", 0.0, 5.0, 1.5, 0.1, key="gs_b")
    xga_b = st.number_input("xG contra/j", 0.0, 5.0, 1.4, 0.1, key="xga_b")
    cb_b = st.number_input("Chutes bloqueados/j", 0.0, 10.0, 1.5, 0.1, key="cb_b")
    posse_b = st.slider("Posse %", 0, 100, 48, key="posse_b")
    pts_cpp_b = st.number_input("Pontos CPP", 0, 30, 4, key="pcpp_b")
    jogos_cpp_b = st.number_input("Jogos CPP", 0, 10, 2, key="jcpp_b")
    dados_estilo_b = {}
    posse_est_b = st.number_input("Posse % (estilo)", 0.0, 100.0, 48.0, key="b_posse")
    if posse_est_b > 0: dados_estilo_b['posse'] = posse_est_b
    ppda_b = st.number_input("PPDA", 0.0, 20.0, 0.0, key="b_ppda")
    if ppda_b > 0: dados_estilo_b['ppda'] = ppda_b
    acoes_to_b = st.number_input("Desarmes/j", 0.0, 50.0, 0.0, key="b_acoes_to")
    if acoes_to_b > 0: dados_estilo_b['acoes_to'] = acoes_to_b
    gols_ca_b = st.number_input("Gols contra-ataque/j", 0.0, 5.0, 0.0, key="b_gols_ca")
    if gols_ca_b > 0: dados_estilo_b['gols_ca'] = gols_ca_b
    chutes_trans_b = st.number_input("Chutes transição/j", 0.0, 10.0, 0.0, key="b_chutes_trans")
    if chutes_trans_b > 0: dados_estilo_b['chutes_trans'] = chutes_trans_b
    cruzamentos_b = st.number_input("Cruzamentos/j", 0.0, 50.0, 0.0, key="b_cruzamentos")
    if cruzamentos_b > 0: dados_estilo_b['cruzamentos'] = cruzamentos_b
    escanteios_b = st.number_input("Escanteios/j", 0.0, 20.0, 0.0, key="b_escanteios")
    if escanteios_b > 0: dados_estilo_b['escanteios'] = escanteios_b
    passes_longos_b = st.number_input("Passes longos/j", 0.0, 100.0, 0.0, key="b_passes_longos")
    if passes_longos_b > 0: dados_estilo_b['passes_longos'] = passes_longos_b
    cons_b = st.text_input("Últ. 10 resultados (psic.)", "DDVVEDDVV", key="cons_b").upper()
    moral_b = st.slider("Moral (pts 3j)", 0, 9, 3, key="moral_b")
    p_obj_b = st.slider("Pressão", 0, 100, 60, key="pobj_b")
    sens_b = st.slider("Sensibilidade", -1.0, 1.0, -0.3, 0.1, key="sens_b")
    prat_b = st.selectbox("Prateleira", ["Elite","Alta","Média","Baixa","Crítico"], key="prat_b")

gerar = st.button("⚡ Gerar Engrama", type="primary")

if gerar:
    # --- Cálculos ---
    _, v_a, d_a = calcular_pontos_e_resultados(list(res_a))
    ma_a = calcular_ma(sum(3 if c=='V' else 1 if c=='E' else 0 for c in res_a), v_a, d_a, odd_a)
    _, v_b, d_b = calcular_pontos_e_resultados(list(res_b))
    ma_b = calcular_ma(sum(3 if c=='V' else 1 if c=='E' else 0 for c in res_b), v_b, d_b, odd_b)

    dados_fg_a = {'GM': gm_a, 'FA': fa_a, 'xG': xg_a, 'GS': gs_a, 'xGA': xga_a, 'CB': cb_a, 'Posse': posse_a}
    dados_fg_a = {k:v for k,v in dados_fg_a.items() if v != 0.0}
    dados_fg_b = {'GM': gm_b, 'FA': fa_b, 'xG': xg_b, 'GS': gs_b, 'xGA': xga_b, 'CB': cb_b, 'Posse': posse_b}
    dados_fg_b = {k:v for k,v in dados_fg_b.items() if v != 0.0}
    fg_a = calcular_fg(dados_fg_a, medias_liga, n_jogos_a)
    fg_b = calcular_fg(dados_fg_b, medias_liga, n_jogos_b)

    cpp_a = calcular_cpp(pts_cpp_a, jogos_cpp_a, odd_a)
    cpp_b = calcular_cpp(pts_cpp_b, jogos_cpp_b, odd_b)

    vetor_a = calcular_vetor_estilo(dados_estilo_a, medias_liga, n_jogos_a)
    vetor_b = calcular_vetor_estilo(dados_estilo_b, medias_liga, n_jogos_b)
    estilo_a = calcular_estilo(dados_estilo_a, medias_liga, n_jogos_a, vetor_b) if vetor_b else 50.0
    estilo_b = calcular_estilo(dados_estilo_b, medias_liga, n_jogos_b, vetor_a) if vetor_a else 50.0

    psic_a = calcular_psicologico(
        consistencia_pontos=[3 if c=='V' else 1 if c=='E' else 0 for c in cons_a],
        moral_pontos=moral_a, pressao_p_obj=p_obj_a, pressao_sensibilidade=sens_a
    )
    psic_b = calcular_psicologico(
        consistencia_pontos=[3 if c=='V' else 1 if c=='E' else 0 for c in cons_b],
        moral_pontos=moral_b, pressao_p_obj=p_obj_b, pressao_sensibilidade=sens_b
    )

    prat_map = {"Elite":0, "Alta":1, "Média":2, "Baixa":3, "Crítico":4}
    prat_a_num = prat_map[prat_a]
    prat_b_num = prat_map[prat_b]

    ec = calcular_engramscore(
        ma_a=ma_a, fg_a=fg_a, cpp_a=cpp_a, estilo_a=estilo_a, psicologico_a=psic_a,
        ma_b=ma_b, fg_b=fg_b, cpp_b=cpp_b, estilo_b=estilo_b, psicologico_b=psic_b,
        time_mandante='A'
    )

    # ==================== RESULTADOS EM ABAS ====================
    tab_visao, tab_graficos, tab_mercados, tab_descritivo = st.tabs([
        "📊 Visão Geral", "📈 Gráficos", "💰 Mercados & Probabilidades", "📝 Análise Descritiva"
    ])

    pilares = ['MA', 'FG', 'CPP', 'Estilo', 'Psicológico']
    vals_a = [ma_a, fg_a, cpp_a, estilo_a, psic_a]
    vals_b = [ma_b, fg_b, cpp_b, estilo_b, psic_b]

    # ---------- ABA VISÃO GERAL ----------
    with tab_visao:
        st.header("Confronto Direto")
        for i, p in enumerate(pilares):
            c1, c2 = st.columns(2)
            win_a = vals_a[i] > vals_b[i]
            win_b = vals_b[i] > vals_a[i]
            with c1:
                st.markdown(f"<div class='big-card {'winner-card' if win_a else ''}'>", unsafe_allow_html=True)
                st.metric(f"{p} - {nome_a}", f"{vals_a[i]:.0f}", delta=f"{vals_a[i]-vals_b[i]:.0f}")
                st.progress(int(vals_a[i]))
                st.markdown("</div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div class='big-card {'winner-card' if win_b else ''}'>", unsafe_allow_html=True)
                st.metric(f"{p} - {nome_b}", f"{vals_b[i]:.0f}", delta=f"{vals_b[i]-vals_a[i]:.0f}")
                st.progress(int(vals_b[i]))
                st.markdown("</div>", unsafe_allow_html=True)

        st.subheader("🏆 EngramsCore")
        col_ec1, col_ec2 = st.columns(2)
        with col_ec1:
            st.markdown(f"<div class='big-card {'winner-card' if ec['EC_A'] > ec['EC_B'] else ''}'>", unsafe_allow_html=True)
            st.markdown(f"<h2>{nome_a}</h2><h1>{ec['EC_A']:.1f}</h1>", unsafe_allow_html=True)
            st.progress(int(ec['EC_A']))
            st.markdown("</div>", unsafe_allow_html=True)
        with col_ec2:
            st.markdown(f"<div class='big-card {'winner-card' if ec['EC_B'] > ec['EC_A'] else ''}'>", unsafe_allow_html=True)
            st.markdown(f"<h2>{nome_b}</h2><h1>{ec['EC_B']:.1f}</h1>", unsafe_allow_html=True)
            st.progress(int(ec['EC_B']))
            st.markdown("</div>", unsafe_allow_html=True)

        st.subheader("🔮 Projeções Rápidas")
        proj = [
            ("Probabilidade de Vitória do Mandante", f"{ec['P_A']:.2%}"),
            ("Probabilidade de Vitória do Visitante", f"{ec['P_B']:.2%}"),
            ("Probabilidade de Empate", f"{ec['P_E']:.2%}"),
            ("Dupla Chance Mandante/Empate", f"{ec['P_A_ou_E']:.2%}"),
            ("Dupla Chance Visitante/Empate", f"{ec['P_B_ou_E']:.2%}"),
            ("Diferença de Força (EC)", f"{abs(ec['EC_A']-ec['EC_B']):.1f}"),
            ("Média de Gols Esperada (modelo)", f"{calcular_mercado_gols(gm_a, gs_a, gm_b, gs_b, max(n_jogos_a,n_jogos_b), ma_a, ma_b, {'ataque':fg_a,'defesa':fg_a,'meio':fg_a}, {'ataque':fg_b,'defesa':fg_b,'meio':fg_b}, cpp_a, cpp_b, vetor_a, vetor_b, {'moral':moral_a,'pressao_obj':p_obj_a,'sensibilidade':sens_a}, {'moral':moral_b,'pressao_obj':p_obj_b,'sensibilidade':sens_b}, ec['EC_A'], ec['EC_B'], prat_a_num, prat_b_num, 1.90)['lambda_final']:.2f}"),
            ("Vantagem Tática (Estilo)", f"{estilo_a - estilo_b:.1f}"),
            ("Pressão Psicológica", f"{psic_a - psic_b:.1f}"),
            ("Consistência Recente", f"{ma_a - ma_b:.1f}"),
        ]
        df_proj = pd.DataFrame(proj, columns=["Indicador", "Valor"])
        st.table(df_proj)

    # ---------- ABA GRÁFICOS ----------
    with tab_graficos:
        st.subheader("Radar Comparativo")
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=vals_a, theta=pilares, fill='toself', name=nome_a, marker=dict(color='#FFD700')))
        fig_radar.add_trace(go.Scatterpolar(r=vals_b, theta=pilares, fill='toself', name=nome_b, marker=dict(color='#B8860B')))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,100])), template='plotly_dark')
        st.plotly_chart(fig_radar, use_container_width=True)

        st.subheader("Estilos de Jogo")
        col_e1, col_e2 = st.columns(2)
        for col, vetor, nome in [(col_e1, vetor_a, nome_a), (col_e2, vetor_b, nome_b)]:
            with col:
                st.markdown(f"**{nome}**")
                if vetor:
                    dims = list(vetor.keys())
                    vals_dim = [vetor[d] if vetor[d] is not None else 0 for d in dims]
                    max_dim = dims[vals_dim.index(max(vals_dim))]
                    st.markdown(f"🔷 Ênfase: **{max_dim.replace('_',' ').title()}** ({max(vals_dim):.0f})")
                    fig = px.bar(x=vals_dim, y=dims, orientation='h',
                                 color=[1 if d==max_dim else 0 for d in dims],
                                 color_continuous_scale=['#B8860B','#FFD700'])
                    fig.update_layout(template='plotly_dark', showlegend=False, height=300)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Sem dados de estilo.")

    # ---------- ABA MERCADOS & PROBABILIDADES ----------
    with tab_mercados:
        st.header("Probabilidades 1X2")
        col_p1, col_p2, col_p3 = st.columns(3)
        col_p1.metric(f"Vitória {nome_a}", f"{ec['P_A']:.2%}")
        col_p2.metric("Empate", f"{ec['P_E']:.2%}")
        col_p3.metric(f"Vitória {nome_b}", f"{ec['P_B']:.2%}")
        col_d1, col_d2 = st.columns(2)
        col_d1.metric(f"Dupla {nome_a} ou Empate", f"{ec['P_A_ou_E']:.2%}")
        col_d2.metric(f"Dupla {nome_b} ou Empate", f"{ec['P_B_ou_E']:.2%}")

        st.header("⚽ Mercado de Gols")
        odd_over25 = st.number_input("Odd Over 2.5", 1.01, 10.0, 1.90, 0.01, key="odd_over")
        gols = calcular_mercado_gols(
            gols_marcados_a=gm_a, gols_sofridos_a=gs_a,
            gols_marcados_b=gm_b, gols_sofridos_b=gs_b,
            n_jogos=max(n_jogos_a, n_jogos_b),
            ma_a=ma_a, ma_b=ma_b,
            fg_a={'ataque':fg_a,'defesa':fg_a,'meio':fg_a},
            fg_b={'ataque':fg_b,'defesa':fg_b,'meio':fg_b},
            cpp_a=cpp_a, cpp_b=cpp_b,
            estilo_a=vetor_a, estilo_b=vetor_b,
            psic_a={'moral':moral_a,'pressao_obj':p_obj_a,'sensibilidade':sens_a},
            psic_b={'moral':moral_b,'pressao_obj':p_obj_b,'sensibilidade':sens_b},
            ec_a=ec['EC_A'], ec_b=ec['EC_B'],
            prateleira_a=prat_a_num, prateleira_b=prat_b_num,
            odd_over25=odd_over25
        )
        col_g1, col_g2, col_g3 = st.columns(3)
        col_g1.metric("Over 1.5", f"{gols['over_1.5']:.2%}")
        col_g2.metric("Over 2.5", f"{gols['over_2.5']:.2%}")
        col_g3.metric("Over 3.5", f"{gols['over_3.5']:.2%}")
        col_g4, col_g5 = st.columns(2)
        col_g4.metric("BTTS Sim", f"{gols['btts_yes']:.2%}")
        col_g5.metric("BTTS Não", f"{gols['btts_no']:.2%}")

        st.subheader("🔍 Selos de Validação")
        prob_mercado = 1.0 / odd_over25 if odd_over25 > 0 else 0
        nosso_over = gols['over_2.5']
        edge = nosso_over - prob_mercado
        if edge > 0.1:
            st.success(f"🚀 Edge Over 2.5: +{edge:.2%} (Confiança Alta)")
        elif edge > 0.05:
            st.info(f"📈 Edge Over 2.5: +{edge:.2%} (Confiança Média)")
        elif edge < -0.1:
            st.error(f"🔻 Under 2.5 favorecido: {1-nosso_over:.2%} (modelo) vs {1-prob_mercado:.2%} (mercado)")
        else:
            st.warning("Sem edge significativo no Over/Under 2.5.")

        prob_1 = 1.0 / odd_a if odd_a > 0 else 0
        edge_1 = ec['P_A'] - prob_1
        if edge_1 > 0.1:
            st.success(f"🏆 Edge Vitória {nome_a}: +{edge_1:.2%}")
        prob_2 = 1.0 / odd_b if odd_b > 0 else 0
        edge_2 = ec['P_B'] - prob_2
        if edge_2 > 0.1:
            st.success(f"🏆 Edge Vitória {nome_b}: +{edge_2:.2%}")

    # ---------- ABA ANÁLISE DESCRITIVA ----------
    with tab_descritivo:
        st.header("Análise Inteligente")
        desc_a = gerar_descricao_completa(nome_a, ma_a, fg_a, cpp_a, estilo_a, psic_a, vetor_a, dados_fg_a, dados_estilo_a, prat_a)
        desc_b = gerar_descricao_completa(nome_b, ma_b, fg_b, cpp_b, estilo_b, psic_b, vetor_b, dados_fg_b, dados_estilo_b, prat_b)
        st.markdown(desc_a)
        st.markdown("---")
        st.markdown(desc_b)
