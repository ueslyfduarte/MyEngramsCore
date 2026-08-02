"""
EngramsCore App - Interface Principal (v2)
Totalmente reformulada com todos os pilares corrigidos.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
import pandas as pd
import numpy as np
import math
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Optional

# Importação dos módulos corrigidos
from src.utils import PRIOR_PADRAO, ALPHA_PADRAO, normalizar_indicador, atualizacao_bayesiana, truncar, media_ativos
from src.metricas.ma import calcular_ma
from src.metricas.fg import calcular_fg
from src.metricas.cpp import calcular_cpp
from src.metricas.psicologico import (
    calcular_psicologico,
    classificar_prateleira,
    calcular_pressao_tabela
)
from src.metricas.estilo_perfil import obter_perfil_time, classificar_perfil
from src.metricas.engramscore import calcular_engramscore

# ----------------------------------------------------------
# Configuração da página
# ----------------------------------------------------------
st.set_page_config(
    page_title="EngramsCore ⚽",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tema escuro
st.markdown("""
<style>
    .stApp { background-color: #0f1117; color: #e0e0e0; }
    h1, h2, h3 { color: #f0c040 !important; }
    .stMetric label { color: #a0a0a0 !important; }
    .stMetric [data-testid="stMetricValue"] { color: #f0c040 !important; }
    .card {
        background: #1a1d27; border: 1px solid #2a2f38; border-radius: 12px;
        padding: 20px; margin: 10px 0;
    }
    .card-destaque {
        border: 1px solid #f0c040; box-shadow: 0 0 15px rgba(240,192,64,0.2);
    }
    .tag-verde {
        background: #00cc66; color: #000; font-weight: bold;
        border-radius: 8px; padding: 6px 16px; display: inline-block;
    }
    .tag-vermelha {
        background: #cc3333; color: #fff; font-weight: bold;
        border-radius: 8px; padding: 6px 16px; display: inline-block;
    }
    .tag-amarela {
        background: #f0c040; color: #000; font-weight: bold;
        border-radius: 8px; padding: 6px 16px; display: inline-block;
    }
    .ev-positivo {
        background: #00cc66; color: #000; padding: 10px; border-radius: 8px;
        text-align: center; font-weight: bold;
    }
    .ev-negativo {
        background: #cc3333; color: #fff; padding: 10px; border-radius: 8px;
        text-align: center;
    }
    .perfil-badge {
        background: #2a2f38; border: 1px solid #f0c040; border-radius: 20px;
        padding: 8px 20px; text-align: center; font-weight: bold; color: #f0c040;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# Sidebar - Configurações
# ----------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/football2--v1.png", width=80)
    st.title("⚙️ Configurações")

    st.markdown("---")
    st.subheader("📊 Médias da Liga")

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        media_gm = st.number_input("Gols/jogo", 0.1, 5.0, 1.4, 0.1)
        media_fa = st.number_input("Finalizações alvo/j", 0.1, 10.0, 4.0, 0.1)
        media_posse = st.number_input("Posse %", 10.0, 90.0, 50.0, 1.0)
        media_eca = st.number_input("Escanteios/j", 0.0, 20.0, 5.0, 0.1)
    with col_s2:
        media_gs = st.number_input("Gols sofridos/j", 0.1, 5.0, 1.4, 0.1)
        media_fas = st.number_input("Finalizações alvo sofridas/j", 0.1, 10.0, 4.0, 0.1)
        media_tc = st.number_input("Total chutes sofridos/j", 0.1, 30.0, 12.0, 0.1)
        media_ecc = st.number_input("Escanteios contra/j", 0.0, 20.0, 5.0, 0.1)

    st.markdown("---")
    st.subheader("🎯 Pesos dos Pilares")
    peso_ma = st.slider("MA (Momento Atual)", 0.0, 1.0, 0.25, 0.05)
    peso_fg = st.slider("FG (Força Geral)", 0.0, 1.0, 0.25, 0.05)
    peso_cpp = st.slider("CPP (Confronto Prateleira)", 0.0, 1.0, 0.25, 0.05)
    peso_psic = st.slider("Psicológico", 0.0, 1.0, 0.25, 0.05)

    st.markdown("---")
    st.subheader("🏟️ Fator Casa")
    home_adv_gols = st.slider("Vantagem em gols", 0.0, 1.0, 0.3, 0.05)
    media_gols_liga = st.slider("Média gols/jogo (Poisson)", 1.0, 4.0, 2.5, 0.1)

    st.markdown("---")
    st.caption("EngramsCore v2 • Todos os pilares corrigidos")

# ----------------------------------------------------------
# Cabeçalho
# ----------------------------------------------------------
st.title("⚽ ENGRAMS CORE")
st.markdown("*Sistema de Análise Esportiva Diferencial*")

# ----------------------------------------------------------
# Área principal - Dados dos Times
# ----------------------------------------------------------
st.markdown("---")
st.header("📝 Dados do Confronto")

col_a, col_b = st.columns(2)

# ==================== TIME A ====================
with col_a:
    st.subheader("🏠 Time Mandante")
    nome_a = st.text_input("Nome", "Time A", key="nome_a")

    with st.expander("📊 Estatísticas da Temporada", expanded=True):
        n_jogos_a = st.number_input("Jogos disputados", 1, 38, 10, key="nj_a")
        gm_a = st.number_input("Gols marcados/jogo", 0.0, 5.0, 2.0, 0.1, key="gm_a")
        fa_a = st.number_input("Finalizações alvo/jogo", 0.0, 10.0, 4.5, 0.1, key="fa_a")
        eca_a = st.number_input("Escanteios a favor/jogo", 0.0, 20.0, 6.0, 0.1, key="eca_a")
        gs_a = st.number_input("Gols sofridos/jogo", 0.0, 5.0, 0.8, 0.1, key="gs_a")
        fas_a = st.number_input("Finalizações alvo sofridas/jogo", 0.0, 10.0, 3.0, 0.1, key="fas_a")
        tc_a = st.number_input("Total chutes sofridos/jogo", 0.0, 30.0, 10.0, 0.1, key="tc_a")
        ecc_a = st.number_input("Escanteios contra/jogo", 0.0, 20.0, 4.0, 0.1, key="ecc_a")
        posse_a = st.slider("Posse de bola %", 0, 100, 55, key="posse_a")
        des_a = st.number_input("Desarmes/jogo", 0.0, 30.0, 18.0, 0.1, key="des_a")
        fc_a = st.number_input("Faltas cometidas/jogo", 0.0, 25.0, 12.0, 0.1, key="fc_a")
        ca_a = st.number_input("Cartões amarelos/jogo", 0.0, 5.0, 2.0, 0.1, key="ca_a")

    with st.expander("📈 Momento & Histórico", expanded=True):
        res_a = st.text_input("Últimos resultados (V/E/D)", "VVEDV", key="res_a").upper()
        odd_v_a = st.number_input("Odd Vitória", 1.01, 10.0, 1.80, 0.01, key="odd_v_a")
        odd_e_a = st.number_input("Odd Empate", 1.01, 10.0, 3.50, 0.01, key="odd_e_a")

    with st.expander("🧠 Psicológico", expanded=True):
        pts_fora_a = st.number_input("Pontos como visitante", 0, 57, 10, key="pts_fora_a")
        jgs_fora_a = st.number_input("Jogos como visitante", 0, 19, 5, key="jgs_fora_a")
        hist_conf_a = st.text_input("Confronto direto (V/E/D)", "VEDV", key="hist_a").upper()
        moral_a = st.slider("Pontos últimos 3 jogos", 0, 9, 6, key="moral_a")
        pos_a = st.number_input("Posição na tabela", 1, 20, 2, key="pos_a")
        total_times = st.number_input("Total times na liga", 2, 24, 20, key="total_times")

    with st.expander("📋 CPP", expanded=True):
        pts_cpp_a = st.number_input("Pontos contra prateleira", 0, 30, 6, key="pcpp_a")
        jgs_cpp_a = st.number_input("Jogos contra prateleira", 0, 10, 3, key="jcpp_a")

# ==================== TIME B ====================
with col_b:
    st.subheader("✈️ Time Visitante")
    nome_b = st.text_input("Nome", "Time B", key="nome_b")

    with st.expander("📊 Estatísticas da Temporada", expanded=True):
        n_jogos_b = st.number_input("Jogos disputados", 1, 38, 10, key="nj_b")
        gm_b = st.number_input("Gols marcados/jogo", 0.0, 5.0, 1.2, 0.1, key="gm_b")
        fa_b = st.number_input("Finalizações alvo/jogo", 0.0, 10.0, 3.2, 0.1, key="fa_b")
        eca_b = st.number_input("Escanteios a favor/jogo", 0.0, 20.0, 4.0, 0.1, key="eca_b")
        gs_b = st.number_input("Gols sofridos/jogo", 0.0, 5.0, 1.5, 0.1, key="gs_b")
        fas_b = st.number_input("Finalizações alvo sofridas/jogo", 0.0, 10.0, 4.0, 0.1, key="fas_b")
        tc_b = st.number_input("Total chutes sofridos/jogo", 0.0, 30.0, 13.0, 0.1, key="tc_b")
        ecc_b = st.number_input("Escanteios contra/jogo", 0.0, 20.0, 5.0, 0.1, key="ecc_b")
        posse_b = st.slider("Posse de bola %", 0, 100, 48, key="posse_b")
        des_b = st.number_input("Desarmes/jogo", 0.0, 30.0, 16.0, 0.1, key="des_b")
        fc_b = st.number_input("Faltas cometidas/jogo", 0.0, 25.0, 14.0, 0.1, key="fc_b")
        ca_b = st.number_input("Cartões amarelos/jogo", 0.0, 5.0, 2.5, 0.1, key="ca_b")

    with st.expander("📈 Momento & Histórico", expanded=True):
        res_b = st.text_input("Últimos resultados (V/E/D)", "DDVVE", key="res_b").upper()
        odd_v_b = st.number_input("Odd Vitória", 1.01, 10.0, 4.00, 0.01, key="odd_v_b")
        odd_e_b = st.number_input("Odd Empate", 1.01, 10.0, 3.50, 0.01, key="odd_e_b")

    with st.expander("🧠 Psicológico", expanded=True):
        pts_fora_b = st.number_input("Pontos como visitante", 0, 57, 7, key="pts_fora_b")
        jgs_fora_b = st.number_input("Jogos como visitante", 0, 19, 5, key="jgs_fora_b")
        hist_conf_b = st.text_input("Confronto direto (V/E/D)", "DVDE", key="hist_b").upper()
        moral_b = st.slider("Pontos últimos 3 jogos", 0, 9, 3, key="moral_b")
        pos_b = st.number_input("Posição na tabela", 1, 20, 12, key="pos_b")

    with st.expander("📋 CPP", expanded=True):
        pts_cpp_b = st.number_input("Pontos contra prateleira", 0, 30, 4, key="pcpp_b")
        jgs_cpp_b = st.number_input("Jogos contra prateleira", 0, 10, 2, key="jcpp_b")

# ----------------------------------------------------------
# Botão de execução
# ----------------------------------------------------------
st.markdown("---")
col_btn, _ = st.columns([1, 3])
with col_btn:
    gerar = st.button("⚡ GERAR ANÁLISE", type="primary", use_container_width=True)

if not gerar:
    st.info("👈 Preencha os dados e clique em **GERAR ANÁLISE** para ver os resultados.")
    st.stop()

# ==================== CÁLCULOS ====================

# --- Montagem dos dicionários de médias ---
medias_liga = {
    'GM': media_gm, 'FA': media_fa, 'GS': media_gs, 'FAS': media_fas,
    'TC': media_tc, 'ECa': media_eca, 'ECc': media_ecc,
    'Posse': media_posse, 'Conv': 10.0, 'Des': 15.0, 'FC': 12.0, 'CA': 2.0
}

dados_a = {
    'GM': gm_a, 'FA': fa_a, 'GS': gs_a, 'FAS': fas_a,
    'TC': tc_a, 'ECa': eca_a, 'ECc': ecc_a,
    'Posse': posse_a, 'Conv': (gm_a / max(media_gm, 0.01)) * 10,
    'Des': des_a, 'FC': fc_a, 'CA': ca_a
}

dados_b = {
    'GM': gm_b, 'FA': fa_b, 'GS': gs_b, 'FAS': fas_b,
    'TC': tc_b, 'ECa': eca_b, 'ECc': ecc_b,
    'Posse': posse_b, 'Conv': (gm_b / max(media_gm, 0.01)) * 10,
    'Des': des_b, 'FC': fc_b, 'CA': ca_b
}

# --- FG ---
fg_a = calcular_fg(dados_a, medias_liga, n_jogos_a)
fg_b = calcular_fg(dados_b, medias_liga, n_jogos_b)

# --- Probabilidades justas a partir das odds (remoção de margem) ---
inv_sum_a = 1/odd_v_a + 1/odd_e_a + (1/(1.01) if odd_v_a and odd_e_a else 0.01)
# Assumindo odd derrota = 1 / (1 - prob_v - prob_e) aproximado
odd_d_a = 1.0 / max(0.01, 1.0 - 1/odd_v_a - 1/odd_e_a) if (1/odd_v_a + 1/odd_e_a) < 1 else 3.0
inv_sum_a = 1/odd_v_a + 1/odd_e_a + 1/odd_d_a
prob_v_a = (1/odd_v_a) / inv_sum_a
prob_e_a = (1/odd_e_a) / inv_sum_a

odd_d_b = 1.0 / max(0.01, 1.0 - 1/odd_v_b - 1/odd_e_b) if (1/odd_v_b + 1/odd_e_b) < 1 else 3.0
inv_sum_b = 1/odd_v_b + 1/odd_e_b + 1/odd_d_b
prob_v_b = (1/odd_v_b) / inv_sum_b
prob_e_b = (1/odd_e_b) / inv_sum_b

# --- MA ---
# Últimos JANELA jogos (6)
def extrair_pontos_recentes(res_str, janela=6):
    res_str = res_str[:janela]
    pts = sum(3 if c == 'V' else 1 if c == 'E' else 0 for c in res_str)
    return pts, len(res_str)

pts_rec_a, jogos_rec_a = extrair_pontos_recentes(res_a)
pts_rec_b, jogos_rec_b = extrair_pontos_recentes(res_b)

ma_a = calcular_ma(
    pontos_recentes=pts_rec_a,
    jogos_recentes=jogos_rec_a,
    jogos_total_temporada=n_jogos_a,
    prob_vitoria=prob_v_a,
    prob_empate=prob_e_a
)
ma_b = calcular_ma(
    pontos_recentes=pts_rec_b,
    jogos_recentes=jogos_rec_b,
    jogos_total_temporada=n_jogos_b,
    prob_vitoria=prob_v_b,
    prob_empate=prob_e_b
)

# --- CPP ---
# Precisamos da prateleira do adversário para o CPP? Não, CPP usa prob_v e prob_e
cpp_a = calcular_cpp(pts_cpp_a, jgs_cpp_a, prob_v_a, prob_e_a)
cpp_b = calcular_cpp(pts_cpp_b, jgs_cpp_b, prob_v_b, prob_e_b)

# --- Psicológico ---
cons_a = [3 if c == 'V' else 1 if c == 'E' else 0 for c in res_a[:10]]
cons_b = [3 if c == 'V' else 1 if c == 'E' else 0 for c in res_b[:10]]

hist_a = list(hist_conf_a.upper()) if hist_conf_a else []
hist_b = list(hist_conf_b.upper()) if hist_conf_b else []

# Pressão por prateleira
dif_pontos = (pos_a - pos_b) * 3  # aproximação
p_obj_a = calcular_pressao_tabela(pos_a, total_times, pos_b, dif_pontos)
p_obj_b = calcular_pressao_tabela(pos_b, total_times, pos_a, -dif_pontos)

psic_a = calcular_psicologico(
    consistencia_pontos=cons_a,
    resiliencia_fora=(pts_fora_a, jgs_fora_a),
    confronto_direto_hist=hist_a,
    moral_pontos=moral_a,
    pressao_p_obj=p_obj_a,
    pressao_sensibilidade=0.5
)
psic_b = calcular_psicologico(
    consistencia_pontos=cons_b,
    resiliencia_fora=(pts_fora_b, jgs_fora_b),
    confronto_direto_hist=hist_b,
    moral_pontos=moral_b,
    pressao_p_obj=p_obj_b,
    pressao_sensibilidade=0.5
)

# --- Perfil Tático ---
perfil_a = obter_perfil_time(dados_a, medias_liga)
perfil_b = obter_perfil_time(dados_b, medias_liga)

# --- EngramsCore ---
pesos = {'MA': peso_ma, 'FG': peso_fg, 'CPP': peso_cpp, 'Psicologico': peso_psic}
ec = calcular_engramscore(
    ma_a=ma_a, fg_a=fg_a, cpp_a=cpp_a, psicologico_a=psic_a,
    ma_b=ma_b, fg_b=fg_b, cpp_b=cpp_b, psicologico_b=psic_b,
    time_mandante='A',
    pesos=pesos,
    odds={'1': odd_v_a, 'X': odd_e_a, '2': odd_v_b},
    media_gols=media_gols_liga,
    home_adv_gols=home_adv_gols
)

# ==================== EXIBIÇÃO DOS RESULTADOS ====================

st.markdown("---")
st.header("📊 Resultados da Análise")

# --- Cards dos Pilares ---
st.subheader("🔬 Comparativo de Pilares")

pilares_nomes = ['MA', 'FG', 'CPP', 'Psicológico']
valores_a = [ma_a, fg_a, cpp_a, psic_a]
valores_b = [ma_b, fg_b, cpp_b, psic_b]

cols_pilares = st.columns(4)
for i, (nome_pilar, va, vb) in enumerate(zip(pilares_nomes, valores_a, valores_b)):
    with cols_pilares[i]:
        st.markdown(f"<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"**{nome_pilar}**")
        col_ia, col_ib = st.columns(2)
        with col_ia:
            cor_a = '#00cc66' if va > vb else '#cc3333' if va < vb else '#f0c040'
            st.markdown(f"<span style='color:{cor_a}; font-weight:bold;'>{nome_a[:3]}: {va:.0f}</span>", unsafe_allow_html=True)
        with col_ib:
            cor_b = '#00cc66' if vb > va else '#cc3333' if vb < va else '#f0c040'
            st.markdown(f"<span style='color:{cor_b}; font-weight:bold;'>{nome_b[:3]}: {vb:.0f}</span>", unsafe_allow_html=True)
        st.progress(int(va) if va > vb else int(vb), text=f"Δ {abs(va-vb):.0f}")
        st.markdown("</div>", unsafe_allow_html=True)

# --- Perfis Táticos ---
st.markdown("---")
st.subheader("🎭 Perfis Táticos")
col_perfil_a, col_perfil_b = st.columns(2)
with col_perfil_a:
    st.markdown(f"<div class='perfil-badge'>{nome_a}: {perfil_a}</div>", unsafe_allow_html=True)
with col_perfil_b:
    st.markdown(f"<div class='perfil-badge'>{nome_b}: {perfil_b}</div>", unsafe_allow_html=True)

# --- EC e Probabilidades ---
st.markdown("---")
st.subheader("🏆 EngramsCore & Probabilidades 1X2")

col_ec_a, col_ec_meio, col_ec_b = st.columns([2, 1, 2])

with col_ec_a:
    st.markdown(f"<div class='card card-destaque'>", unsafe_allow_html=True)
    st.markdown(f"### {nome_a}")
    st.metric("EC", f"{ec['EC_A']:.1f}")
    st.metric("Prob. Vitória", f"{ec['P_A']:.2%}")
    if 'EV_A' in ec and ec['EV_A'] is not None:
        ev_a = ec['EV_A']
        st.markdown(f"<div class='{'ev-positivo' if ev_a > 0 else 'ev-negativo'}'>{'✅' if ev_a > 0 else '❌'} EV: {ev_a:+.1%}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_ec_meio:
    st.markdown(f"<div class='card'>", unsafe_allow_html=True)
    st.markdown("### ⚖️ Empate")
    st.metric("Prob.", f"{ec['P_E']:.2%}")
    if 'EV_E' in ec and ec['EV_E'] is not None:
        ev_e = ec['EV_E']
        st.markdown(f"<div class='{'ev-positivo' if ev_e > 0 else 'ev-negativo'}'>{'✅' if ev_e > 0 else '❌'} EV: {ev_e:+.1%}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_ec_b:
    st.markdown(f"<div class='card card-destaque'>", unsafe_allow_html=True)
    st.markdown(f"### {nome_b}")
    st.metric("EC", f"{ec['EC_B']:.1f}")
    st.metric("Prob. Vitória", f"{ec['P_B']:.2%}")
    if 'EV_B' in ec and ec['EV_B'] is not None:
        ev_b = ec['EV_B']
        st.markdown(f"<div class='{'ev-positivo' if ev_b > 0 else 'ev-negativo'}'>{'✅' if ev_b > 0 else '❌'} EV: {ev_b:+.1%}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- Dupla Chance ---
col_dc1, col_dc2 = st.columns(2)
with col_dc1:
    st.metric(f"Dupla: {nome_a} ou Empate", f"{ec['P_A_ou_E']:.2%}")
with col_dc2:
    st.metric(f"Dupla: {nome_b} ou Empate", f"{ec['P_B_ou_E']:.2%}")

# --- Onde há valor ---
if any([ec.get('VALOR_A'), ec.get('VALOR_E'), ec.get('VALOR_B')]):
    st.markdown("### 💰 Oportunidades de Valor Detectadas")
    if ec.get('VALOR_A'):
        st.markdown(f"<div class='tag-verde'>✅ Vitória {nome_a} com EV+: {ec['EV_A']:+.1%}</div>", unsafe_allow_html=True)
    if ec.get('VALOR_E'):
        st.markdown(f"<div class='tag-verde'>✅ Empate com EV+: {ec['EV_E']:+.1%}</div>", unsafe_allow_html=True)
    if ec.get('VALOR_B'):
        st.markdown(f"<div class='tag-verde'>✅ Vitória {nome_b} com EV+: {ec['EV_B']:+.1%}</div>", unsafe_allow_html=True)

# --- Gráfico de barras dos pilares ---
st.markdown("---")
st.subheader("📈 Visualização Comparativa")

df_pilares = pd.DataFrame({
    'Pilar': pilares_nomes * 2,
    'Valor': valores_a + valores_b,
    'Time': [nome_a]*4 + [nome_b]*4
})
fig = px.bar(df_pilares, x='Pilar', y='Valor', color='Time', barmode='group',
             color_discrete_map={nome_a: '#f0c040', nome_b: '#0066cc'})
fig.update_layout(template='plotly_dark', paper_bgcolor='#0f1117', plot_bgcolor='#0f1117')
st.plotly_chart(fig, use_container_width=True)

# --- Radar FG ---
st.subheader("🎯 Força Geral (Radar)")

def calc_sub_nota(valor, media, menor_melhor=False):
    if media == 0:
        return 50.0
    return normalizar_indicador(valor, media, menor_melhor)

atq_a = calc_sub_nota(gm_a, media_gm)
def_a = calc_sub_nota(gs_a, media_gs, menor_melhor=True)
mei_a = calc_sub_nota(posse_a, media_posse)
atq_b = calc_sub_nota(gm_b, media_gm)
def_b = calc_sub_nota(gs_b, media_gs, menor_melhor=True)
mei_b = calc_sub_nota(posse_b, media_posse)

fig_radar = go.Figure()
categorias = ['Ataque', 'Defesa', 'Meio']
fig_radar.add_trace(go.Scatterpolar(
    r=[atq_a, def_a, mei_a], theta=categorias, fill='toself',
    name=nome_a, marker=dict(color='#f0c040')
))
fig_radar.add_trace(go.Scatterpolar(
    r=[atq_b, def_b, mei_b], theta=categorias, fill='toself',
    name=nome_b, marker=dict(color='#0066cc')
))
fig_radar.update_layout(
    polar=dict(radialaxis=dict(range=[0, 100])),
    template='plotly_dark', paper_bgcolor='#0f1117'
)
st.plotly_chart(fig_radar, use_container_width=True)

# --- Resumo descritivo ---
st.markdown("---")
st.subheader("📝 Resumo Descritivo")

col_desc_a, col_desc_b = st.columns(2)
with col_desc_a:
    st.markdown(f"**{nome_a}**")
    st.markdown(f"- Perfil: **{perfil_a}**")
    st.markdown(f"- FG: {fg_a:.0f} | MA: {ma_a:.0f} | Psicológico: {psic_a:.0f}")
    st.markdown(f"- Ataque: {gm_a:.1f} gols/j | Defesa: {gs_a:.1f} gols sofridos/j")
    st.markdown(f"- Posse: {posse_a:.0f}%")
with col_desc_b:
    st.markdown(f"**{nome_b}**")
    st.markdown(f"- Perfil: **{perfil_b}**")
    st.markdown(f"- FG: {fg_b:.0f} | MA: {ma_b:.0f} | Psicológico: {psic_b:.0f}")
    st.markdown(f"- Ataque: {gm_b:.1f} gols/j | Defesa: {gs_b:.1f} gols sofridos/j")
    st.markdown(f"- Posse: {posse_b:.0f}%")

# --- Rodapé ---
st.markdown("---")
st.caption("EngramsCore v2 • Método de análise esportiva diferencial • Todos os pilares revisados e corrigidos")
