import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
import pandas as pd
import numpy as np
import math
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict

# Seus módulos
from src.metricas.ma import calcular_ma
from src.metricas.fg import calcular_fg
from src.metricas.cpp import calcular_cpp
from src.metricas.estilo import calcular_estilo
from src.metricas.psicologico import (
    calcular_psicologico,
    calcular_pressao_tabela,
    classificar_prateleira,
)
from src.metricas.estilo_perfil import obter_perfil_time

# ------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ------------------------------------------------------------
st.set_page_config(page_title="MyEngramScore ⚽", page_icon="⚽", layout="wide")

# ------------------------------------------------------------
# CSS GLOBAL - TEMA EA FC + TRADING
# ------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    * { font-family: 'Inter', sans-serif; }

    .stApp {
        background: linear-gradient(135deg, #06080D 0%, #0B0F17 50%, #0D111A 100%);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0A0D14 0%, #0F1219 100%);
        border-right: 1px solid #1E2330;
    }
    [data-testid="stSidebar"] h2 {
        color: #F0C040 !important;
        font-weight: 800;
        letter-spacing: 1px;
        text-transform: uppercase;
        font-size: 14px;
        border-bottom: 2px solid #F0C040;
        padding-bottom: 8px;
        margin-bottom: 16px;
    }
    [data-testid="stSidebar"] .stNumberInput input {
        background: #111620;
        border: 1px solid #252B38;
        border-radius: 6px;
        color: #E0E0E0;
    }
    [data-testid="stSidebar"] .stNumberInput input:focus {
        border-color: #F0C040;
        box-shadow: 0 0 8px rgba(240,192,64,0.2);
    }

    /* Cards principais */
    .card-premium {
        background: linear-gradient(145deg, rgba(20,24,35,0.9) 0%, rgba(16,20,30,0.95) 100%);
        border: 1px solid #252B38;
        border-radius: 16px;
        padding: 28px 24px;
        margin: 12px 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.03);
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    .card-premium::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(240,192,64,0.3), transparent);
    }
    .card-premium:hover {
        border-color: #F0C040;
        box-shadow: 0 12px 40px rgba(0,0,0,0.6), 0 0 20px rgba(240,192,64,0.1);
        transform: translateY(-2px);
    }

    .card-header-premium {
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #8890A0;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .card-header-premium .icon {
        font-size: 18px;
    }

    /* Métricas gigantes */
    .metric-premium {
        font-size: 56px;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(180deg, #F0C040 0%, #D4A017 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -2px;
        line-height: 1;
        margin: 8px 0;
        filter: drop-shadow(0 0 12px rgba(240,192,64,0.3));
    }
    .metric-premium-blue {
        font-size: 56px;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(180deg, #4A90D9 0%, #2A5FA0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -2px;
        line-height: 1;
        margin: 8px 0;
        filter: drop-shadow(0 0 12px rgba(74,144,217,0.3));
    }

    .metric-label-premium {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 3px;
        color: #5A6070;
        text-align: center;
        font-weight: 600;
    }

    /* Barras de progresso */
    .bar-premium {
        height: 6px;
        border-radius: 3px;
        background: rgba(255,255,255,0.05);
        margin: 12px 0;
        overflow: hidden;
    }
    .bar-fill-gold {
        height: 100%;
        border-radius: 3px;
        background: linear-gradient(90deg, #F0C040, #D4A017);
        box-shadow: 0 0 12px rgba(240,192,64,0.4);
        transition: width 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    }
    .bar-fill-blue {
        height: 100%;
        border-radius: 3px;
        background: linear-gradient(90deg, #4A90D9, #2A5FA0);
        box-shadow: 0 0 12px rgba(74,144,217,0.4);
        transition: width 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    }

    /* Selos */
    .selo-dourado {
        border: 2px solid #F0C040;
        border-radius: 20px;
        padding: 6px 16px;
        background: linear-gradient(135deg, rgba(240,192,64,0.15) 0%, rgba(240,192,64,0.05) 100%);
        color: #F0C040;
        font-weight: 700;
        font-size: 12px;
        display: inline-block;
        letter-spacing: 1px;
        box-shadow: 0 0 16px rgba(240,192,64,0.2);
    }
    .selo-verde {
        border: 2px solid #00E676;
        border-radius: 20px;
        padding: 6px 16px;
        background: linear-gradient(135deg, rgba(0,230,118,0.15) 0%, rgba(0,230,118,0.05) 100%);
        color: #00E676;
        font-weight: 700;
        font-size: 12px;
        display: inline-block;
        letter-spacing: 1px;
        box-shadow: 0 0 16px rgba(0,230,118,0.2);
    }
    .selo-amarelo {
        border: 2px solid #FFB300;
        border-radius: 20px;
        padding: 6px 16px;
        background: linear-gradient(135deg, rgba(255,179,0,0.15) 0%, rgba(255,179,0,0.05) 100%);
        color: #FFB300;
        font-weight: 700;
        font-size: 12px;
        display: inline-block;
        letter-spacing: 1px;
        box-shadow: 0 0 16px rgba(255,179,0,0.2);
    }

    /* Botão principal */
    .stButton > button {
        background: linear-gradient(135deg, #F0C040 0%, #D4A017 100%);
        color: #0A0D14;
        font-weight: 800;
        font-size: 16px;
        letter-spacing: 2px;
        text-transform: uppercase;
        border: none;
        border-radius: 12px;
        padding: 16px 48px;
        box-shadow: 0 8px 24px rgba(240,192,64,0.3);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 32px rgba(240,192,64,0.5);
        background: linear-gradient(135deg, #FFD966 0%, #E0B030 100%);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(255,255,255,0.02);
        border-radius: 12px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        font-size: 13px;
        color: #5A6070;
        transition: all 0.2s;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(240,192,64,0.15) 0%, rgba(240,192,64,0.05) 100%) !important;
        color: #F0C040 !important;
        border: 1px solid rgba(240,192,64,0.3);
    }

    /* Prob boxes */
    .prob-box {
        background: linear-gradient(145deg, rgba(20,24,35,0.8) 0%, rgba(16,20,30,0.9) 100%);
        border-radius: 16px;
        padding: 24px 16px;
        text-align: center;
        border: 1px solid #252B38;
        backdrop-filter: blur(10px);
    }

    /* Subtítulos */
    h1, h2, h3 {
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }

    /* Animações para números */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .animate-in {
        animation: fadeInUp 0.6s ease forwards;
    }

    /* Tooltip de odds */
    .odd-input {
        background: #111620 !important;
        border: 1px solid #252B38 !important;
        border-radius: 8px !important;
        color: #E0E0E0 !important;
    }
    .odd-input:focus {
        border-color: #F0C040 !important;
        box-shadow: 0 0 12px rgba(240,192,64,0.15) !important;
    }

    /* Info cards */
    .info-card {
        background: rgba(240,192,64,0.03);
        border: 1px solid rgba(240,192,64,0.1);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        font-size: 13px;
        color: #8890A0;
        line-height: 1.6;
    }

    /* Separators */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #252B38, transparent);
        margin: 24px 0;
    }

    /* Estatísticas em linha */
    .stat-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid rgba(255,255,255,0.03);
        font-size: 14px;
    }
    .stat-value {
        font-weight: 700;
        color: #F0C040;
    }

    /* Select box */
    .stSelectbox > div > div {
        background: #111620 !important;
        border: 1px solid #252B38 !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# HEADER PREMIUM
# ------------------------------------------------------------
st.markdown("""
<div style="text-align:center; padding: 20px 0 30px 0;">
    <div style="font-size:12px; text-transform:uppercase; letter-spacing:4px; color:#5A6070; margin-bottom:8px;">
        Sistema de Análise Esportiva
    </div>
    <h1 style="font-size:42px; font-weight:900; margin:0; letter-spacing:-1px;">
        <span style="background:linear-gradient(180deg, #F0C040 0%, #D4A017 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            MYENGRAM
        </span>
        <span style="color:#E0E0E0; font-weight:300;">SCORE</span>
    </h1>
    <div style="font-size:11px; color:#5A6070; letter-spacing:3px; margin-top:4px;">
        ÍNDICE DE FORÇA ABSOLUTA
    </div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# BARRA LATERAL - LIGA
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🏆 Liga de Referência")
    with st.expander("⚙️ Médias da Competição", expanded=False):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            media_gm = st.number_input("Gols/jogo", 0.1, 5.0, 1.4, 0.1, key="media_gm")
            media_fa = st.number_input("Finalizações alvo/j", 0.0, 10.0, 4.0, 0.1, key="media_fa")
            media_eca = st.number_input("Escanteios a favor/j", 0.0, 20.0, 5.0, 0.1, key="media_eca")
            media_posse = st.number_input("Posse (%)", 0.0, 100.0, 50.0, 1.0, key="media_posse")
            media_gs = st.number_input("Gols sofridos/j", 0.1, 5.0, 1.4, 0.1, key="media_gs")
        with col_s2:
            media_fas = st.number_input("Finalizações alvo sofridas/j", 0.0, 10.0, 4.0, 0.1, key="media_fas")
            media_ecc = st.number_input("Escanteios contra/j", 0.0, 20.0, 5.0, 0.1, key="media_ecc")
            media_des = st.number_input("Desarmes/j", 0.0, 50.0, 15.0, 0.1, key="media_des")
            media_fc = st.number_input("Faltas/j", 0.0, 30.0, 12.0, 0.1, key="media_fc")
            media_ca = st.number_input("Cartões amarelos/j", 0.0, 10.0, 2.0, 0.1, key="media_ca")

medias_liga = {
    'GM': media_gm, 'FA': media_fa, 'ECa': media_eca,
    'GS': media_gs, 'FAS': media_fas, 'ECc': media_ecc,
    'FC': media_fc, 'CA': media_ca, 'Des': media_des, 'Posse': media_posse,
}

# ------------------------------------------------------------
# ENTRADA DE DADOS DOS TIMES
# ------------------------------------------------------------
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; margin-bottom:20px;">
    <span style="font-size:11px; text-transform:uppercase; letter-spacing:3px; color:#5A6070;">Dados do Confronto</span>
</div>
""", unsafe_allow_html=True)

colA, colB = st.columns(2)

with colA:
    with st.container():
        st.markdown("""
        <div class="card-premium">
            <div class="card-header-premium">
                <span class="icon">🏠</span> TIME DA CASA
            </div>
        """, unsafe_allow_html=True)
        nome_casa = st.text_input("Nome do Time", "Time A", key="casa")
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            n_casa = st.number_input("Jogos", 1, 38, 10, key="nj_casa")
            gm_casa = st.number_input("Gols/jogo", 0.0, 5.0, 2.0, 0.1, key="gm_casa")
            fa_casa = st.number_input("Finalizações alvo/j", 0.0, 10.0, 4.5, 0.1, key="fa_casa")
            eca_casa = st.number_input("Escanteios a favor/j", 0.0, 20.0, 5.5, 0.1, key="eca_casa")
            posse_casa = st.slider("Posse (%)", 0, 100, 55, key="posse_casa")
        with col_a2:
            gs_casa = st.number_input("Gols sofridos/j", 0.0, 5.0, 0.8, 0.1, key="gs_casa")
            fas_casa = st.number_input("Finalizações alvo sofridas/j", 0.0, 10.0, 3.0, 0.1, key="fas_casa")
            ecc_casa = st.number_input("Escanteios contra/j", 0.0, 20.0, 4.0, 0.1, key="ecc_casa")
            des_casa = st.number_input("Desarmes/j", 0.0, 50.0, 16.0, 0.1, key="des_casa")
            fc_casa = st.number_input("Faltas/j", 0.0, 30.0, 13.0, 0.1, key="fc_casa")
            ca_casa = st.number_input("Cartões amarelos/j", 0.0, 10.0, 2.2, 0.1, key="ca_casa")

        st.markdown("---")
        res_casa = st.text_input("Últ. resultados (V/E/D)", "VVEDV", key="res_casa").upper()
        pts_cpp_casa = st.number_input("Pontos contra prateleira", 0, 30, 6, key="pcpp_casa")
        jogos_cpp_casa = st.number_input("Jogos contra prateleira", 0, 10, 3, key="jcpp_casa")
        prat_casa = st.selectbox("Prateleira", ["Elite","Alta","Média","Baixa","Crítica"], key="prat_casa")
        cons_casa = st.text_input("Últ. 10 jogos (V/E/D)", "VVEDVVEDVV", key="cons_casa").upper()
        moral_casa = st.slider("Moral (pts 3j)", 0, 9, 6, key="moral_casa")
        pos_casa = st.number_input("Posição na tabela", 1, 20, 2, key="pos_casa")
        st.markdown("</div>", unsafe_allow_html=True)

with colB:
    with st.container():
        st.markdown("""
        <div class="card-premium">
            <div class="card-header-premium">
                <span class="icon">✈️</span> TIME VISITANTE
            </div>
        """, unsafe_allow_html=True)
        nome_fora = st.text_input("Nome do Time", "Time B", key="fora")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            n_fora = st.number_input("Jogos", 1, 38, 10, key="nj_fora")
            gm_fora = st.number_input("Gols/jogo", 0.0, 5.0, 1.2, 0.1, key="gm_fora")
            fa_fora = st.number_input("Finalizações alvo/j", 0.0, 10.0, 3.2, 0.1, key="fa_fora")
            eca_fora = st.number_input("Escanteios a favor/j", 0.0, 20.0, 4.5, 0.1, key="eca_fora")
            posse_fora = st.slider("Posse (%)", 0, 100, 48, key="posse_fora")
        with col_b2:
            gs_fora = st.number_input("Gols sofridos/j", 0.0, 5.0, 1.5, 0.1, key="gs_fora")
            fas_fora = st.number_input("Finalizações alvo sofridas/j", 0.0, 10.0, 3.8, 0.1, key="fas_fora")
            ecc_fora = st.number_input("Escanteios contra/j", 0.0, 20.0, 5.0, 0.1, key="ecc_fora")
            des_fora = st.number_input("Desarmes/j", 0.0, 50.0, 14.0, 0.1, key="des_fora")
            fc_fora = st.number_input("Faltas/j", 0.0, 30.0, 11.0, 0.1, key="fc_fora")
            ca_fora = st.number_input("Cartões amarelos/j", 0.0, 10.0, 1.8, 0.1, key="ca_fora")

        st.markdown("---")
        res_fora = st.text_input("Últ. resultados (V/E/D)", "DDVVE", key="res_fora").upper()
        pts_cpp_fora = st.number_input("Pontos contra prateleira", 0, 30, 4, key="pcpp_fora")
        jogos_cpp_fora = st.number_input("Jogos contra prateleira", 0, 10, 2, key="jcpp_fora")
        prat_fora = st.selectbox("Prateleira", ["Elite","Alta","Média","Baixa","Crítica"], key="prat_fora")
        cons_fora = st.text_input("Últ. 10 jogos (V/E/D)", "DDVVEDDVV", key="cons_fora").upper()
        moral_fora = st.slider("Moral (pts 3j)", 0, 9, 3, key="moral_fora")
        pos_fora = st.number_input("Posição na tabela", 1, 20, 16, key="pos_fora")
        st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------
# ODDS 1X2 (ANTES DO BOTÃO)
# ------------------------------------------------------------
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; margin-bottom:20px;">
    <span style="font-size:11px; text-transform:uppercase; letter-spacing:3px; color:#5A6070;">Odds de Mercado</span>
</div>
""", unsafe_allow_html=True)
col_odd1, col_odd2, col_odd3 = st.columns(3)
with col_odd1:
    odd_casa = st.number_input("🏠 Vitória Casa", 1.01, 10.0, 1.80, 0.01, key="odd_casa")
with col_odd2:
    odd_empate = st.number_input("🤝 Empate", 1.01, 10.0, 3.50, 0.01, key="odd_empate")
with col_odd3:
    odd_fora = st.number_input("✈️ Vitória Fora", 1.01, 10.0, 4.00, 0.01, key="odd_fora")

# ------------------------------------------------------------
# BOTÃO DE ANÁLISE
# ------------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
col_btn = st.columns([1,2,1])
with col_btn[1]:
    gerar = st.button("⚡ GERAR ANÁLISE", type="primary", use_container_width=True)

if gerar:
    # ==================== PROCESSAMENTO ====================
    def parse_seq(s):
        return [3 if c == 'V' else 1 if c == 'E' else 0 for c in s if c in 'VED']
    seq_casa = parse_seq(res_casa)
    seq_fora = parse_seq(res_fora)
    seq_cons_casa = parse_seq(cons_casa)
    seq_cons_fora = parse_seq(cons_fora)

    inv_sum = 1/odd_casa + 1/odd_empate + 1/odd_fora
    prob_v_casa = (1/odd_casa) / inv_sum
    prob_emp = (1/odd_empate) / inv_sum
    prob_v_fora = (1/odd_fora) / inv_sum

    def ma_recente(seq, pv, pe, n_total):
        if not seq: return 50.0
        recente = seq[-6:]
        return calcular_ma(sum(recente), len(recente), n_total, pv, pe)
    ma_A = ma_recente(seq_casa, prob_v_casa, prob_emp, n_casa)
    ma_B = ma_recente(seq_fora, prob_v_fora, prob_emp, n_fora)

    dados_A = {'GM': gm_casa, 'FA': fa_casa, 'ECa': eca_casa, 'Posse': posse_casa,
               'GS': gs_casa, 'FAS': fas_casa, 'ECc': ecc_casa, 'Des': des_casa,
               'FC': fc_casa, 'CA': ca_casa}
    dados_B = {'GM': gm_fora, 'FA': fa_fora, 'ECa': eca_fora, 'Posse': posse_fora,
               'GS': gs_fora, 'FAS': fas_fora, 'ECc': ecc_fora, 'Des': des_fora,
               'FC': fc_fora, 'CA': ca_fora}
    fg_A = calcular_fg(dados_A, medias_liga, n_casa)
    fg_B = calcular_fg(dados_B, medias_liga, n_fora)

    cpp_A = calcular_cpp(pts_cpp_casa, jogos_cpp_casa, prob_v_casa, prob_emp)
    cpp_B = calcular_cpp(pts_cpp_fora, jogos_cpp_fora, prob_v_fora, prob_emp)

    estilo_A = calcular_estilo(dados_A, medias_liga, n_casa)
    estilo_B = calcular_estilo(dados_B, medias_liga, n_fora)

    perfil_A = obter_perfil_time(dados_A, medias_liga)
    perfil_B = obter_perfil_time(dados_B, medias_liga)

    dif_pts = (pos_casa - pos_fora) * 3
    p_obj_A = calcular_pressao_tabela(pos_casa, 20, pos_fora, dif_pts)
    p_obj_B = calcular_pressao_tabela(pos_fora, 20, pos_casa, -dif_pts)

    psic_A = calcular_psicologico(
        consistencia_pontos=seq_cons_casa if len(seq_cons_casa)>=5 else None,
        moral_pontos=moral_casa, pressao_p_obj=p_obj_A, pressao_sensibilidade=0.3)
    psic_B = calcular_psicologico(
        consistencia_pontos=seq_cons_fora if len(seq_cons_fora)>=5 else None,
        moral_pontos=moral_fora, pressao_p_obj=p_obj_B, pressao_sensibilidade=0.3)

    PESOS = {'MA': 0.25, 'FG': 0.25, 'CPP': 0.25, 'Psicologico': 0.25}
    EC_A = (ma_A*PESOS['MA'] + fg_A*PESOS['FG'] + cpp_A*PESOS['CPP'] + psic_A*PESOS['Psicologico'])
    EC_B = (ma_B*PESOS['MA'] + fg_B*PESOS['FG'] + cpp_B*PESOS['CPP'] + psic_B*PESOS['Psicologico'])
    EC_A += 2.0
    EC_A = max(0, min(100, EC_A))
    EC_B = max(0, min(100, EC_B))

    total = EC_A + EC_B
    diff_rel = abs(EC_A - EC_B)/total if total>0 else 0
    p_emp = max(0.18, 0.40 - diff_rel*0.3)
    p_A = (1 - p_emp) * (EC_A/total) if total>0 else 0.33
    p_B = 1 - p_A - p_emp

    lambda_casa_orig = (gm_casa + gs_fora) / 2
    lambda_fora_orig = (gm_fora + gs_casa) / 2

    def ajustar_lambdas(ec_a, ec_b, lam_casa, lam_fora, fator_impacto=0.5):
        diff_ec = (ec_a - ec_b) / 100.0
        lam_casa_adj = lam_casa * (1.0 + diff_ec * fator_impacto)
        lam_fora_adj = lam_fora * (1.0 - diff_ec * fator_impacto)
        lam_casa_adj = max(0.0, lam_casa_adj)
        lam_fora_adj = max(0.0, lam_fora_adj)
        return lam_casa_adj, lam_fora_adj, diff_ec

    lambda_casa_adj, lambda_fora_adj, fator_ajuste = ajustar_lambdas(
        EC_A, EC_B, lambda_casa_orig, lambda_fora_orig
    )

    results_adj = []
    for i in range(6):
        for j in range(6):
            prob = math.exp(-lambda_casa_adj)*(lambda_casa_adj**i)/math.factorial(i) * \
                   math.exp(-lambda_fora_adj)*(lambda_fora_adj**j)/math.factorial(j)
            results_adj.append((i, j, prob))

    vitoria_casa_adj = sum(p for gA,gB,p in results_adj if gA>gB)
    empate_adj = sum(p for gA,gB,p in results_adj if gA==gB)
    vitoria_fora_adj = sum(p for gA,gB,p in results_adj if gA<gB)
    over15_adj = sum(p for gA,gB,p in results_adj if gA+gB > 1.5)
    over25_adj = sum(p for gA,gB,p in results_adj if gA+gB > 2.5)
    over35_adj = sum(p for gA,gB,p in results_adj if gA+gB > 3.5)
    btts_adj = sum(p for gA,gB,p in results_adj if gA>0 and gB>0)

    FATOR_HT = 0.44
    ajuste_estilo = 0
    if perfil_A in ["Pressão Alta", "Dominante"]:
        ajuste_estilo += 0.05
    if perfil_B in ["Pressão Alta", "Dominante"]:
        ajuste_estilo -= 0.05
    ajuste_ma = (ma_A - 50) * 0.001 + (ma_B - 50) * 0.001
    lambda_ht_adj = (lambda_casa_adj + lambda_fora_adj) * (FATOR_HT + ajuste_estilo + ajuste_ma)
    prob_gol_ht_adj = 1 - math.exp(-lambda_ht_adj)

    # ==================== FUNÇÕES AUXILIARES ====================
    def desenhar_campo_duplo(fA, fB, nome_casa, nome_fora):
        fig = go.Figure()
        fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100,
                      line=dict(color="white", width=2), fillcolor="#0A0E17")
        fig.add_shape(type="line", x0=0, y0=50, x1=100, y1=50,
                      line=dict(color="white", width=2, dash="dash"))
        zonas = ['Defesa', 'Meio', 'Ataque']
        for i, (zona, fa) in enumerate(zip(zonas, fA)):
            x0 = i * 33.33
            x1 = (i+1) * 33.33
            fig.add_shape(type="rect", x0=x0, y0=50, x1=x1, y1=100,
                          fillcolor=f"rgba(240,192,64,{fa})", line_width=0)
            fig.add_annotation(x=(x0+x1)/2, y=75, text=f"{zona}<br>{fa*100:.0f}%",
                               showarrow=False, font=dict(color="white", size=10))
        zonas_B = ['Ataque', 'Meio', 'Defesa']
        for i, (zona, fb) in enumerate(zip(zonas_B, fB)):
            x0 = i * 33.33
            x1 = (i+1) * 33.33
            fig.add_shape(type="rect", x0=x0, y0=0, x1=x1, y1=50,
                          fillcolor=f"rgba(74,144,217,{fb})", line_width=0)
            fig.add_annotation(x=(x0+x1)/2, y=25, text=f"{zona}<br>{fb*100:.0f}%",
                               showarrow=False, font=dict(color="white", size=10))
        fig.add_annotation(x=50, y=105, text=f"🏠 {nome_casa}", showarrow=False,
                           font=dict(color="#F0C040", size=14))
        fig.add_annotation(x=50, y=-5, text=f"✈️ {nome_fora}", showarrow=False,
                           font=dict(color="#4a90d9", size=14))
        fig.update_xaxes(visible=False, range=[0,100])
        fig.update_yaxes(visible=False, range=[-10,110])
        fig.update_layout(template='plotly_dark', paper_bgcolor='#0A0E17',
                          height=500, margin=dict(l=20, r=20, t=40, b=40))
        return fig

    def gerar_cenarios_justificados():
        eventos = [
            ('Vitória do ' + nome_casa + ' por 2+ gols',
             sum(p for gA,gB,p in results_adj if gA >= gB+2),
             f"Ataque eficiente do {nome_casa} ({gm_casa:.1f} gols/j) contra defesa do {nome_fora} ({gs_fora:.1f} sofridos/j)."),
            ('Empate',
             empate_adj,
             f"Equilíbrio nos ECs ({EC_A:.1f} vs {EC_B:.1f})."),
            ('Vitória do ' + nome_fora,
             vitoria_fora_adj,
             f"{nome_fora} explora espaços com seus {gm_fora:.1f} gols/j."),
            ('Over 1.5 Gols',
             over15_adj,
             f"Média de {lambda_casa_adj+lambda_fora_adj:.2f} gols esperados (ajustada)."),
            ('Over 2.5 Gols',
             over25_adj,
             f"λ ajustado total de {lambda_casa_adj+lambda_fora_adj:.2f}."),
            ('Over 3.5 Gols',
             over35_adj,
             f"Ataques podem render placar elástico."),
            ('Ambos Marcam (BTTS)',
             btts_adj,
             f"{nome_casa} marca {gm_casa:.1f} e sofre {gs_casa:.1f}; {nome_fora} marca {gm_fora:.1f} e sofre {gs_fora:.1f}."),
        ]
        eventos.sort(key=lambda x: x[1], reverse=True)
        return eventos[:5]

    def selo(prob):
        if prob >= 0.75:
            return '<span class="selo-dourado">🏅 OURO</span>'
        elif prob >= 0.60:
            return '<span class="selo-verde">✅ CONFIÁVEL</span>'
        elif prob >= 0.50:
            return '<span class="selo-amarelo">⚠️ MODERADO</span>'
        else:
            return ''

    # ==================== EXIBIÇÃO PRINCIPAL ====================
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center; margin-bottom:30px;">
        <div style="font-size:11px; text-transform:uppercase; letter-spacing:4px; color:#5A6070;">Resultado da Análise</div>
        <h2 style="font-weight:900; margin:8px 0; letter-spacing:-1px;">
            <span style="background:linear-gradient(180deg, #F0C040 0%, #D4A017 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                MYENGRAMSCORE
            </span>
        </h2>
    </div>
    """, unsafe_allow_html=True)

    col_ec1, col_ec2 = st.columns(2)
    with col_ec1:
        st.markdown(f"""
        <div class="card-premium animate-in" style="text-align:center;">
            <div style="font-size:13px; text-transform:uppercase; letter-spacing:3px; color:#8890A0; margin-bottom:12px;">🏠 {nome_casa}</div>
            <div class="metric-premium">{EC_A:.1f}</div>
            <div class="metric-label-premium">Índice de Força</div>
            <div class="bar-premium">
                <div class="bar-fill-gold" style="width:{EC_A}%;"></div>
            </div>
            <div style="font-size:10px; color:#5A6070; margin-top:4px;">MA · FG · CPP · PSICOLÓGICO</div>
        </div>
        """, unsafe_allow_html=True)

    with col_ec2:
        st.markdown(f"""
        <div class="card-premium animate-in" style="text-align:center;">
            <div style="font-size:13px; text-transform:uppercase; letter-spacing:3px; color:#8890A0; margin-bottom:12px;">✈️ {nome_fora}</div>
            <div class="metric-premium-blue">{EC_B:.1f}</div>
            <div class="metric-label-premium">Índice de Força</div>
            <div class="bar-premium">
                <div class="bar-fill-blue" style="width:{EC_B}%;"></div>
            </div>
            <div style="font-size:10px; color:#5A6070; margin-top:4px;">MA · FG · CPP · PSICOLÓGICO</div>
        </div>
        """, unsafe_allow_html=True)

    if EC_A > EC_B:
        st.markdown(f"""
        <div style="text-align:center; margin:16px 0; font-size:16px; font-weight:700; color:#F0C040;">
            🔺 {nome_casa} leva vantagem de +{EC_A - EC_B:.1f} pontos
        </div>
        """, unsafe_allow_html=True)
    elif EC_B > EC_A:
        st.markdown(f"""
        <div style="text-align:center; margin:16px 0; font-size:16px; font-weight:700; color:#4A90D9;">
            🔻 {nome_fora} leva vantagem de +{EC_B - EC_A:.1f} pontos
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="text-align:center; margin:16px 0; font-size:16px; font-weight:700; color:#F0C040;">
            ⚖️ Equilíbrio absoluto
        </div>
        """, unsafe_allow_html=True)

    # ==================== ABAS ====================
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center; margin-bottom:20px;">
        <span style="font-size:11px; text-transform:uppercase; letter-spacing:3px; color:#5A6070;">Análises Detalhadas</span>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs([
        "📊 PILARES",
        "🎭 ESTILO",
        "⚔️ CONFRONTO",
        "🗺️ HEATMAP",
        "🎲 CENÁRIOS",
        "🔧 AJUSTE EC",
        "📋 MERCADOS",
        "📝 ANÁLISE"
    ])

    # ----- ABA 1: Pilares -----
    with tabs[0]:
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">🔍 PILARES INDIVIDUAIS</div>', unsafe_allow_html=True)
        pilares_nomes = ['Momento Atual', 'Força Geral', 'Confronto', 'Psicológico']
        valores_A = [ma_A, fg_A, cpp_A, psic_A]
        valores_B = [ma_B, fg_B, cpp_B, psic_B]
        df = pd.DataFrame({'Pilar': pilares_nomes*2, 'Time': [nome_casa]*4+[nome_fora]*4,
                           'Força': valores_A+valores_B})
        fig = px.bar(df, x='Pilar', y='Força', color='Time', barmode='group', text_auto='.1f',
                     color_discrete_map={nome_casa:'#F0C040', nome_fora:'#4a90d9'})
        fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">🎯 FORÇA SETORIAL</div>', unsafe_allow_html=True)
        def norm_rad(val, media):
            if media==0: return 50
            return max(0, min(100, 50 + (val-media)/media*50))
        atq_A = (norm_rad(gm_casa, media_gm) + norm_rad(fa_casa, media_fa))/2
        def_A = (100 - norm_rad(gs_casa, media_gs) + 100 - norm_rad(fas_casa, media_fas))/2
        mei_A = norm_rad(posse_casa, media_posse)
        atq_B = (norm_rad(gm_fora, media_gm) + norm_rad(fa_fora, media_fa))/2
        def_B = (100 - norm_rad(gs_fora, media_gs) + 100 - norm_rad(fas_fora, media_fas))/2
        mei_B = norm_rad(posse_fora, media_posse)
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=[atq_A, def_A, mei_A], theta=['Ataque','Defesa','Meio'],
                                            fill='toself', name=nome_casa, marker_color='#F0C040'))
        fig_radar.add_trace(go.Scatterpolar(r=[atq_B, def_B, mei_B], theta=['Ataque','Defesa','Meio'],
                                            fill='toself', name=nome_fora, marker_color='#4a90d9'))
        fig_radar.update_layout(polar=dict(radialaxis=dict(range=[0,100])),
                                template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_radar, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ----- ABA 2: Estilo de Jogo -----
    with tabs[1]:
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">🎭 PERFIS TÁTICOS</div>', unsafe_allow_html=True)
        col_perf1, col_perf2 = st.columns(2)
        with col_perf1:
            st.markdown(f"""
            <div style="background:rgba(240,192,64,0.05); border:1px solid rgba(240,192,64,0.2); border-radius:12px; padding:20px; text-align:center;">
                <div style="font-size:18px; font-weight:700; color:#F0C040; margin-bottom:8px;">🏠 {nome_casa}</div>
                <div style="font-size:24px; font-weight:900; color:#F0C040;">{perfil_A}</div>
                <div style="font-size:12px; color:#8890A0; margin-top:8px;">Dominância: {estilo_A:.1f}/100</div>
            </div>
            """, unsafe_allow_html=True)
        with col_perf2:
            st.markdown(f"""
            <div style="background:rgba(74,144,217,0.05); border:1px solid rgba(74,144,217,0.2); border-radius:12px; padding:20px; text-align:center;">
                <div style="font-size:18px; font-weight:700; color:#4A90D9; margin-bottom:8px;">✈️ {nome_fora}</div>
                <div style="font-size:24px; font-weight:900; color:#4A90D9;">{perfil_B}</div>
                <div style="font-size:12px; color:#8890A0; margin-top:8px;">Dominância: {estilo_B:.1f}/100</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("""
        <div class="info-card" style="margin-top:16px;">
            <strong>🏆 Dominante:</strong> Controla posse, finaliza muito, pressiona.<br>
            <strong>🔥 Pressão Alta:</strong> Extremamente agressivo, muitas faltas e desarmes.<br>
            <strong>⚡ Reativo/Contra‑ataque:</strong> Pouca posse, transições rápidas e certeiras.<br>
            <strong>🛡️ Defensivo:</strong> Prioriza não sofrer gols, jogo físico, baixa posse.<br>
            <strong>⚖️ Equilibrado:</strong> Sem extremos, jogo balanceado.<br>
            <strong>🔄 Posse Estéril:</strong> Muita posse, pouca efetividade.<br>
            <strong>🎯 Efetivo:</strong> Pouca posse, alto aproveitamento.
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ----- ABA 3: Comparação Setorial -----
    with tabs[2]:
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">⚔️ CONFRONTO POR ESTATÍSTICA</div>', unsafe_allow_html=True)
        stats = [
            ('Gols Marcados', gm_casa, gm_fora, 'maior'),
            ('Finalizações Alvo', fa_casa, fa_fora, 'maior'),
            ('Posse (%)', posse_casa, posse_fora, 'maior'),
            ('Gols Sofridos', gs_casa, gs_fora, 'menor'),
            ('Finalizações Sofridas', fas_casa, fas_fora, 'menor'),
            ('Faltas Cometidas', fc_casa, fc_fora, 'menor'),
        ]
        for nome, vA, vB, tipo in stats:
            if tipo == 'maior':
                vant = nome_casa if vA>vB else nome_fora if vB>vA else "Empate"
            else:
                vant = nome_casa if vA<vB else nome_fora if vB<vA else "Empate"
            st.markdown(f"""
            <div class="stat-row">
                <span>{nome}</span>
                <span>{nome_casa} {vA:.1f} × {vB:.1f} {nome_fora}</span>
                <span class="stat-value">{vant}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ----- ABA 4: Heatmap -----
    with tabs[3]:
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">🗺️ HEATMAP TÁTICO</div>', unsafe_allow_html=True)
        fA = [def_A/100, mei_A/100, atq_A/100]
        fB = [atq_B/100, mei_B/100, def_B/100]
        fig_field = desenhar_campo_duplo(fA, fB, nome_casa, nome_fora)
        st.plotly_chart(fig_field, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ----- ABA 5: Simulação de Cenários -----
    with tabs[4]:
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">🎲 CINCO CENÁRIOS MAIS PROVÁVEIS</div>', unsafe_allow_html=True)
        cenarios = gerar_cenarios_justificados()
        for i, (titulo, prob, just) in enumerate(cenarios):
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.02); border-radius:8px; padding:12px 16px; margin:8px 0;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:700;">{i+1}. {titulo}</span>
                    <span style="font-size:20px; font-weight:900; color:#F0C040;">{prob:.1%}</span>
                </div>
                <div style="font-size:12px; color:#8890A0; margin-top:4px;">{just}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ----- ABA 6: Ajuste MyEngramScore -----
    with tabs[5]:
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">🔧 AJUSTE MYENGRAMSCORE NOS GOLS ESPERADOS</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="text-align:center; margin:16px 0;">
            <span style="font-size:13px; color:#8890A0;">Fator de Ajuste:</span>
            <span style="font-size:24px; font-weight:900; color:#F0C040; margin-left:8px;">{fator_ajuste:+.2f}</span>
        </div>
        """, unsafe_allow_html=True)
        col_orig, col_adj = st.columns(2)
        with col_orig:
            st.markdown("""
            <div style="background:rgba(255,255,255,0.02); border-radius:8px; padding:16px; text-align:center;">
                <div style="font-size:11px; color:#5A6070; text-transform:uppercase;">Lambdas Originais</div>
            """, unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:28px; font-weight:900; color:#8890A0;'>λ Casa: {lambda_casa_orig:.2f}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:28px; font-weight:900; color:#8890A0;'>λ Fora: {lambda_fora_orig:.2f}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with col_adj:
            st.markdown("""
            <div style="background:rgba(240,192,64,0.03); border:1px solid rgba(240,192,64,0.2); border-radius:8px; padding:16px; text-align:center;">
                <div style="font-size:11px; color:#F0C040; text-transform:uppercase;">Lambdas Ajustados</div>
            """, unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:28px; font-weight:900; color:#F0C040;'>λ Casa: {lambda_casa_adj:.2f}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:28px; font-weight:900; color:#F0C040;'>λ Fora: {lambda_fora_adj:.2f}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="info-card" style="margin-top:16px;">
            Se o time da casa é muito superior (EC_A > EC_B), seu λ ofensivo <strong>aumenta</strong> e o λ do visitante <strong>diminui</strong>.
            Isso reduz artificialmente a chance de o time mais fraco marcar, refletindo a superioridade medida pelo MyEngramScore.
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ----- ABA 7: Dados para os Mercados -----
    with tabs[6]:
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">📊 PROBABILIDADES 1X2</div>', unsafe_allow_html=True)
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            st.markdown(f"""
            <div class="prob-box">
                <div style="color:#00E676; font-size:13px; text-transform:uppercase; letter-spacing:1px;">Vitória {nome_casa}</div>
                <div style="font-size:42px; font-weight:900; color:#00E676;">{p_A:.1%}</div>
                <div style="margin-top:8px;">{selo(p_A)}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_p2:
            st.markdown(f"""
            <div class="prob-box">
                <div style="color:#F0C040; font-size:13px; text-transform:uppercase; letter-spacing:1px;">Empate</div>
                <div style="font-size:42px; font-weight:900; color:#F0C040;">{p_emp:.1%}</div>
                <div style="margin-top:8px;">{selo(p_emp)}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_p3:
            st.markdown(f"""
            <div class="prob-box">
                <div style="color:#4A90D9; font-size:13px; text-transform:uppercase; letter-spacing:1px;">Vitória {nome_fora}</div>
                <div style="font-size:42px; font-weight:900; color:#4A90D9;">{p_B:.1%}</div>
                <div style="margin-top:8px;">{selo(p_B)}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">⚽ PROBABILIDADES DE GOLS (AJUSTADAS)</div>', unsafe_allow_html=True)
        col_g1, col_g2, col_g3 = st.columns(3)
        col_g1.metric("Over 1.5", f"{over15_adj:.1%}")
        col_g2.metric("Over 2.5", f"{over25_adj:.1%}")
        col_g3.metric("Over 3.5", f"{over35_adj:.1%}")
        col_g4, col_g5 = st.columns(2)
        col_g4.metric("Ambos Marcam (BTTS)", f"{btts_adj:.1%}")
        col_g5.metric("BTTS Não", f"{1-btts_adj:.1%}")
        st.markdown(f"""
        <div class="info-card">
            <strong>λ original:</strong> Casa {lambda_casa_orig:.2f}, Fora {lambda_fora_orig:.2f}<br>
            <strong>λ ajustado:</strong> Casa {lambda_casa_adj:.2f}, Fora {lambda_fora_adj:.2f}
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">⏱️ GOL NO 1º TEMPO</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="text-align:center;">
            <div style="font-size:56px; font-weight:900; background:linear-gradient(180deg, #F0C040 0%, #D4A017 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                {prob_gol_ht_adj:.1%}
            </div>
            <div style="font-size:12px; color:#8890A0;">λ ajustado: {lambda_ht_adj:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ----- ABA 8: Análise Descritiva Completa -----
    with tabs[7]:
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">📝 ANÁLISE DESCRITIVA COMPLETA</div>', unsafe_allow_html=True)

        st.markdown("### 🔍 Pilares Individuais")
        st.markdown(f"""
        <div class="info-card">
            <strong>Momento Atual (MA):</strong> {nome_casa} {ma_A:.1f} × {nome_fora} {ma_B:.1f}. 
            {'O time da casa vive melhor fase.' if ma_A > ma_B else 'O visitante chega em melhor momento.' if ma_B > ma_A else 'Ambos estão em momentos semelhantes.'}<br>
            <strong>Força Geral (FG):</strong> {nome_casa} {fg_A:.1f} × {nome_fora} {fg_B:.1f}. 
            {'A casa tem um elenco mais forte estatisticamente.' if fg_A > fg_B else 'O visitante possui maior força geral.' if fg_B > fg_A else 'Força equilibrada.'}<br>
            <strong>Confronto por Prateleira (CPP):</strong> {nome_casa} {cpp_A:.1f} × {nome_fora} {cpp_B:.1f}. 
            {'Bom histórico contra times do mesmo nível.' if cpp_A > 60 else 'Histórico regular.' if cpp_A > 40 else 'Desempenho ruim contra pares.'}<br>
            <strong>Psicológico:</strong> {nome_casa} {psic_A:.1f} × {nome_fora} {psic_B:.1f}. 
            {'Time da casa mais confiante.' if psic_A > psic_B else 'Visitante com melhor preparo mental.' if psic_B > psic_A else 'Fatores psicológicos empatados.'}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### ⚡ MyEngramScore")
        st.markdown(f"""
        <div class="info-card">
            O índice final reflete a superioridade de um time sobre o outro: 
            {nome_casa} <strong>{EC_A:.1f}</strong> vs {nome_fora} <strong>{EC_B:.1f}</strong>. 
            {'A vantagem é clara para o mandante.' if EC_A > EC_B + 5 else 'O visitante é o favorito, mesmo fora de casa.' if EC_B > EC_A + 5 else 'O confronto é extremamente equilibrado.'}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🎯 Desempenho Setorial")
        st.markdown(f"""
        <div class="info-card">
            <strong>Ataque:</strong> {nome_casa} {atq_A:.1f} × {nome_fora} {atq_B:.1f} → {'O ataque da casa é mais eficiente.' if atq_A > atq_B else 'O visitante leva perigo.' if atq_B > atq_A else 'Ataques similares.'}<br>
            <strong>Defesa:</strong> {nome_casa} {def_A:.1f} × {nome_fora} {def_B:.1f} → {'A defesa mandante é mais segura.' if def_A > def_B else 'O visitante defende melhor.' if def_B > def_A else 'Defesas de mesmo nível.'}<br>
            <strong>Meio-campo:</strong> {nome_casa} {mei_A:.1f} × {nome_fora} {mei_B:.1f} → {'O controle do meio tende a ser do time da casa.' if mei_A > mei_B else 'O visitante pode dominar a posse.' if mei_B > mei_A else 'Disputa equilibrada no meio.'}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🎭 Estilos de Jogo")
        st.markdown(f"""
        <div class="info-card">
            {nome_casa} é <strong>{perfil_A}</strong> (dominância {estilo_A:.1f}), enquanto {nome_fora} é <strong>{perfil_B}</strong> (dominância {estilo_B:.1f}). 
            {'O estilo dominante da casa pode sufocar o visitante.' if 'Dominante' in perfil_A and 'Reativo' in perfil_B else 'O visitante reativo pode explorar contra-ataques.' if 'Reativo' in perfil_B else 'Ambos os estilos podem se neutralizar.'}
        </div>
        """, unsafe_allow_html=True)

        cenarios_5 = gerar_cenarios_justificados()
        st.markdown("### 🎲 Cenário mais Provável")
        st.markdown(f"""
        <div class="info-card">
            <strong>{cenarios_5[0][0]}</strong> ({cenarios_5[0][1]:.1%}): {cenarios_5[0][2]}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📌 Conclusão")
        if EC_A > EC_B + 5:
            st.markdown(f"""
            <div class="info-card" style="border-color:#00E676;">
                Diante de todos os pilares analisados, <strong>{nome_casa}</strong> é amplamente favorito para vencer a partida. Seu MyEngramScore superior reflete melhor momento, força geral e psicológico. A expectativa de gols é alta, com domínio territorial.
            </div>
            """, unsafe_allow_html=True)
        elif EC_B > EC_A + 5:
            st.markdown(f"""
            <div class="info-card" style="border-color:#4A90D9;">
                Apesar de jogar fora de casa, <strong>{nome_fora}</strong> apresenta um MyEngramScore significativamente maior, indicando que deve impor seu jogo e vencer. O time da casa precisará de uma atuação defensiva impecável para surpreender.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="info-card" style="border-color:#F0C040;">
                O confronto é <strong>extremamente equilibrado</strong>, com forças muito próximas. O empate é um resultado plausível, e os detalhes decidirão. Ambos os times devem marcar, e a partida promete ser disputada até o fim.
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Rodapé
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center; padding:20px; color:#5A6070; font-size:11px; letter-spacing:2px;">
        MYENGRAMSCORE © 2026 · ANÁLISE DIFERENCIAL DE FORÇA
    </div>
    """, unsafe_allow_html=True)
