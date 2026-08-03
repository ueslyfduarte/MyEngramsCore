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
st.set_page_config(page_title="EngramScore ⚽", page_icon="⚽", layout="wide")

# ------------------------------------------------------------
# CSS PREMIUM — LEGIBILIDADE E ESTILO EA FC
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
        letter-spacing: 2px;
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

    /* Cards premium */
    .card-premium {
        background: linear-gradient(145deg, rgba(20,24,35,0.9) 0%, rgba(16,20,30,0.95) 100%);
        border: 1px solid #252B38;
        border-radius: 14px;
        padding: 20px 16px;
        margin: 8px 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.03);
        position: relative;
        overflow: hidden;
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
    }
    .card-header-premium {
        font-size: 14px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #B0B8C0;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Métricas gigantes */
    .metric-premium {
        font-size: 52px;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(180deg, #F0C040 0%, #D4A017 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -2px;
        line-height: 1;
        margin: 6px 0;
    }
    .metric-premium-blue {
        font-size: 52px;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(180deg, #4A90D9 0%, #2A5FA0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -2px;
        line-height: 1;
        margin: 6px 0;
    }

    .high-confidence {
        background: linear-gradient(180deg, #F0C040 0%, #D4A017 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        font-weight: 900;
    }

    .metric-label-premium {
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 3px;
        color: #B0B8C0;
        text-align: center;
        font-weight: 600;
    }

    /* Barras de progresso */
    .bar-premium {
        height: 6px;
        border-radius: 3px;
        background: rgba(255,255,255,0.05);
        margin: 10px 0;
        overflow: hidden;
    }
    .bar-fill-gold {
        height: 100%;
        border-radius: 3px;
        background: linear-gradient(90deg, #F0C040, #D4A017);
    }
    .bar-fill-blue {
        height: 100%;
        border-radius: 3px;
        background: linear-gradient(90deg, #4A90D9, #2A5FA0);
    }

    /* Selos */
    .selo-dourado {
        border: 2px solid #F0C040;
        border-radius: 20px;
        padding: 5px 14px;
        background: linear-gradient(135deg, rgba(240,192,64,0.15) 0%, rgba(240,192,64,0.05) 100%);
        color: #F0C040;
        font-weight: 700;
        font-size: 12px;
        display: inline-block;
        letter-spacing: 1px;
    }
    .selo-verde {
        border: 2px solid #00E676;
        border-radius: 20px;
        padding: 5px 14px;
        background: linear-gradient(135deg, rgba(0,230,118,0.15) 0%, rgba(0,230,118,0.05) 100%);
        color: #00E676;
        font-weight: 700;
        font-size: 12px;
        display: inline-block;
        letter-spacing: 1px;
    }
    .selo-amarelo {
        border: 2px solid #FFB300;
        border-radius: 20px;
        padding: 5px 14px;
        background: linear-gradient(135deg, rgba(255,179,0,0.15) 0%, rgba(255,179,0,0.05) 100%);
        color: #FFB300;
        font-weight: 700;
        font-size: 12px;
        display: inline-block;
        letter-spacing: 1px;
    }

    /* Botão principal */
    .stButton > button {
        background: linear-gradient(135deg, #F0C040 0%, #D4A017 100%);
        color: #0A0D14;
        font-weight: 800;
        font-size: 15px;
        letter-spacing: 2px;
        text-transform: uppercase;
        border: none;
        border-radius: 12px;
        padding: 14px 40px;
        box-shadow: 0 8px 24px rgba(240,192,64,0.3);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 32px rgba(240,192,64,0.5);
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
        padding: 10px 18px;
        font-weight: 600;
        font-size: 14px;
        color: #B0B8C0;
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
        border-radius: 14px;
        padding: 20px 12px;
        text-align: center;
        border: 1px solid #252B38;
    }

    /* Info cards */
    .info-card {
        background: rgba(240,192,64,0.03);
        border: 1px solid rgba(240,192,64,0.1);
        border-radius: 12px;
        padding: 14px;
        margin: 6px 0;
        font-size: 15px;
        color: #E0E0E0;
        line-height: 1.6;
    }

    /* Divisor */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #252B38, transparent);
        margin: 20px 0;
    }

    /* Campos de input */
    .stNumberInput input, .stTextInput input {
        background: #111620 !important;
        border: 1px solid #252B38 !important;
        border-radius: 8px !important;
        color: #E0E0E0 !important;
    }
    .stSelectbox > div > div {
        background: #111620 !important;
        border: 1px solid #252B38 !important;
        border-radius: 8px !important;
    }

    /* Títulos e subtítulos */
    h2, h3 {
        font-weight: 800 !important;
        letter-spacing: -0.5px;
        color: #F0C040 !important;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# HEADER ENGRAMSCORE
# ------------------------------------------------------------
st.markdown("""
<div style="text-align:center; padding: 20px 0 30px 0;">
    <div style="font-size:13px; text-transform:uppercase; letter-spacing:4px; color:#B0B8C0; margin-bottom:8px;">
        Sistema de Análise Esportiva
    </div>
    <h1 style="font-size:44px; font-weight:900; margin:0; letter-spacing:-1px;">
        <span style="background:linear-gradient(180deg, #F0C040 0%, #D4A017 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            ENGRAM
        </span>
        <span style="color:#E0E0E0; font-weight:300;">SCORE</span>
    </h1>
    <div style="font-size:13px; color:#B0B8C0; letter-spacing:3px; margin-top:4px;">
        ÍNDICE DE FORÇA ABSOLUTA — ONDE A MEMÓRIA CONSOLIDA O PADRÃO
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
# ENTRADA DE DADOS — CARDS POR SETOR
# ------------------------------------------------------------
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; margin-bottom:20px;">
    <span style="font-size:13px; text-transform:uppercase; letter-spacing:3px; color:#B0B8C0;">Dados do Confronto</span>
</div>
""", unsafe_allow_html=True)

colA, colB = st.columns(2)

# ============= TIME A =============
with colA:
    # Card 1: Identificação
    with st.container():
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">🏠 TIME DA CASA</div>', unsafe_allow_html=True)
        nome_casa = st.text_input("Nome", "Time A", key="casa", label_visibility="collapsed", placeholder="Nome do time")
        n_casa = st.number_input("Jogos na temporada", 1, 38, 10, key="nj_casa")
        pos_casa = st.number_input("Posição na tabela", 1, 24, 2, key="pos_casa")
        prat_casa = st.selectbox(
            "Prateleira do Adversário",
            ["Elite","Alta","Média","Baixa","Crítica"],
            key="prat_casa",
            help="Classificação do próximo adversário. Ex.: se o oponente está entre os 3 primeiros, escolha 'Elite'."
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # Card 2: Ataque
    with st.container():
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">🎯 ATAQUE</div>', unsafe_allow_html=True)
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            gm_casa = st.number_input("Gols/jogo", 0.0, 5.0, 2.0, 0.1, key="gm_casa")
            fa_casa = st.number_input("Finalizações alvo/j", 0.0, 10.0, 4.5, 0.1, key="fa_casa")
        with col_a2:
            eca_casa = st.number_input("Escanteios a favor/j", 0.0, 20.0, 5.5, 0.1, key="eca_casa")
        st.markdown('</div>', unsafe_allow_html=True)

    # Card 3: Defesa
    with st.container():
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">🛡️ DEFESA</div>', unsafe_allow_html=True)
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            gs_casa = st.number_input("Gols sofridos/j", 0.0, 5.0, 0.8, 0.1, key="gs_casa")
            fas_casa = st.number_input("Finalizações alvo sofridas/j", 0.0, 10.0, 3.0, 0.1, key="fas_casa")
        with col_d2:
            ecc_casa = st.number_input("Escanteios contra/j", 0.0, 20.0, 4.0, 0.1, key="ecc_casa")
            des_casa = st.number_input("Desarmes/j", 0.0, 50.0, 16.0, 0.1, key="des_casa")
        st.markdown('</div>', unsafe_allow_html=True)

    # Card 4: Posse & Disciplina
    with st.container():
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">🎮 POSSE & DISCIPLINA</div>', unsafe_allow_html=True)
        posse_casa = st.slider("Posse (%)", 0, 100, 55, key="posse_casa")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            fc_casa = st.number_input("Faltas/j", 0.0, 30.0, 13.0, 0.1, key="fc_casa")
        with col_p2:
            ca_casa = st.number_input("Cartões amarelos/j", 0.0, 10.0, 2.2, 0.1, key="ca_casa")
        st.markdown('</div>', unsafe_allow_html=True)

    # Card 5: Momento & Confronto
    with st.container():
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">📈 MOMENTO & CONFRONTO</div>', unsafe_allow_html=True)
        res_casa = st.text_input("Últ. 5 resultados (V/E/D)", "VVEDV", key="res_casa", help="Digite exatamente 5 caracteres: V, E ou D").upper()
        cons_casa = st.text_input("Últ. 10 resultados (V/E/D)", "VVEDVVEDVV", key="cons_casa", help="Digite exatamente 10 caracteres: V, E ou D").upper()
        moral_casa = st.slider("Moral (pts 3j)", 0, 9, 6, key="moral_casa")
        pts_cpp_casa = st.number_input("Pontos contra prateleira", 0, 30, 6, key="pcpp_casa")
        jogos_cpp_casa = st.number_input("Jogos contra prateleira", 0, 10, 3, key="jcpp_casa")
        st.markdown('</div>', unsafe_allow_html=True)

# ============= TIME B =============
with colB:
    # Card 1: Identificação
    with st.container():
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">✈️ TIME VISITANTE</div>', unsafe_allow_html=True)
        nome_fora = st.text_input("Nome", "Time B", key="fora", label_visibility="collapsed", placeholder="Nome do time")
        n_fora = st.number_input("Jogos na temporada", 1, 38, 10, key="nj_fora")
        pos_fora = st.number_input("Posição na tabela", 1, 24, 16, key="pos_fora")
        prat_fora = st.selectbox(
            "Prateleira do Adversário",
            ["Elite","Alta","Média","Baixa","Crítica"],
            key="prat_fora",
            help="Classificação do próximo adversário. Ex.: se o oponente está entre os 3 primeiros, escolha 'Elite'."
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # Card 2: Ataque
    with st.container():
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">🎯 ATAQUE</div>', unsafe_allow_html=True)
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            gm_fora = st.number_input("Gols/jogo", 0.0, 5.0, 1.2, 0.1, key="gm_fora")
            fa_fora = st.number_input("Finalizações alvo/j", 0.0, 10.0, 3.2, 0.1, key="fa_fora")
        with col_a2:
            eca_fora = st.number_input("Escanteios a favor/j", 0.0, 20.0, 4.5, 0.1, key="eca_fora")
        st.markdown('</div>', unsafe_allow_html=True)

    # Card 3: Defesa
    with st.container():
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">🛡️ DEFESA</div>', unsafe_allow_html=True)
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            gs_fora = st.number_input("Gols sofridos/j", 0.0, 5.0, 1.5, 0.1, key="gs_fora")
            fas_fora = st.number_input("Finalizações alvo sofridas/j", 0.0, 10.0, 3.8, 0.1, key="fas_fora")
        with col_d2:
            ecc_fora = st.number_input("Escanteios contra/j", 0.0, 20.0, 5.0, 0.1, key="ecc_fora")
            des_fora = st.number_input("Desarmes/j", 0.0, 50.0, 14.0, 0.1, key="des_fora")
        st.markdown('</div>', unsafe_allow_html=True)

    # Card 4: Posse & Disciplina
    with st.container():
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">🎮 POSSE & DISCIPLINA</div>', unsafe_allow_html=True)
        posse_fora = st.slider("Posse (%)", 0, 100, 48, key="posse_fora")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            fc_fora = st.number_input("Faltas/j", 0.0, 30.0, 11.0, 0.1, key="fc_fora")
        with col_p2:
            ca_fora = st.number_input("Cartões amarelos/j", 0.0, 10.0, 1.8, 0.1, key="ca_fora")
        st.markdown('</div>', unsafe_allow_html=True)

    # Card 5: Momento & Confronto
    with st.container():
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">📈 MOMENTO & CONFRONTO</div>', unsafe_allow_html=True)
        res_fora = st.text_input("Últ. 5 resultados (V/E/D)", "DDVVE", key="res_fora", help="Digite exatamente 5 caracteres: V, E ou D").upper()
        cons_fora = st.text_input("Últ. 10 resultados (V/E/D)", "DDVVEDDVV", key="cons_fora", help="Digite exatamente 10 caracteres: V, E ou D").upper()
        moral_fora = st.slider("Moral (pts 3j)", 0, 9, 3, key="moral_fora")
        pts_cpp_fora = st.number_input("Pontos contra prateleira", 0, 30, 4, key="pcpp_fora")
        jogos_cpp_fora = st.number_input("Jogos contra prateleira", 0, 10, 2, key="jcpp_fora")
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------
# ODDS 1X2
# ------------------------------------------------------------
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; margin-bottom:20px;">
    <span style="font-size:13px; text-transform:uppercase; letter-spacing:3px; color:#B0B8C0;">Odds de Mercado</span>
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
    gerar = st.button("⚡ GERAR ENGRAMSCORE", type="primary", use_container_width=True)

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
    p_obj_A = calcular_pressao_tabela(pos_casa, 24, pos_fora, dif_pts)
    p_obj_B = calcular_pressao_tabela(pos_fora, 24, pos_casa, -dif_pts)

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

    # Gol 1º Tempo (mantido internamente, exibido junto com demais métricas)
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
        """Campo de futebol realista com faixas de força sem sobreposição."""
        fig = go.Figure()
        
        # Gramado
        fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100,
                      fillcolor="#1B4D1B", line=dict(color="white", width=2))
        # Linha do meio
        fig.add_shape(type="line", x0=50, y0=0, x1=50, y1=100,
                      line=dict(color="white", width=2))
        # Círculo central
        fig.add_shape(type="circle", x0=35, y0=35, x1=65, y1=65,
                      line=dict(color="white", width=2))
        # Áreas
        fig.add_shape(type="rect", x0=0, y0=20, x1=20, y1=80,
                      line=dict(color="white", width=1.5))
        fig.add_shape(type="rect", x0=80, y0=20, x1=100, y1=80,
                      line=dict(color="white", width=1.5))
        # Pequenas áreas
        fig.add_shape(type="rect", x0=0, y0=35, x1=10, y1=65,
                      line=dict(color="white", width=1))
        fig.add_shape(type="rect", x0=90, y0=35, x1=100, y1=65,
                      line=dict(color="white", width=1))
        
        # Faixas do Time A (esquerda, y=50 a 100)
        zonas = ['Defesa', 'Meio', 'Ataque']
        for i, (zona, fa) in enumerate(zip(zonas, fA)):
            x0 = i * 33.33
            x1 = (i+1) * 33.33
            fig.add_shape(type="rect", x0=x0, y0=50, x1=x1, y1=100,
                          fillcolor=f"rgba(240,192,64,{fa*0.5})", line_width=0)
            fig.add_annotation(x=(x0+x1)/2, y=75, text=f"{zona}<br>{fa*100:.0f}%",
                               showarrow=False, font=dict(color="white", size=11))
        fig.add_annotation(x=15, y=110, text=f"🏠 {nome_casa}", showarrow=False,
                           font=dict(color="#F0C040", size=14))
        
        # Faixas do Time B (direita, espelhadas, y=0 a 50)
        zonas_B = ['Ataque', 'Meio', 'Defesa']
        for i, (zona, fb) in enumerate(zip(zonas_B, fB)):
            x0 = i * 33.33
            x1 = (i+1) * 33.33
            fig.add_shape(type="rect", x0=x0, y0=0, x1=x1, y1=50,
                          fillcolor=f"rgba(74,144,217,{fb*0.5})", line_width=0)
            fig.add_annotation(x=(x0+x1)/2, y=25, text=f"{zona}<br>{fb*100:.0f}%",
                               showarrow=False, font=dict(color="white", size=11))
        fig.add_annotation(x=85, y=110, text=f"✈️ {nome_fora}", showarrow=False,
                           font=dict(color="#4a90d9", size=14))
        
        fig.update_xaxes(visible=False, range=[0,100])
        fig.update_yaxes(visible=False, range=[-10,120])
        fig.update_layout(template='plotly_dark', paper_bgcolor='#0A0E17',
                          height=500, margin=dict(l=20, r=20, t=40, b=20))
        return fig

    def gerar_cenarios_justificados():
        eventos = [
            ('Vitória do ' + nome_casa + ' por 2+ gols',
             sum(p for gA,gB,p in results_adj if gA >= gB+2),
             f"Ataque do {nome_casa} ({gm_casa:.1f} gols/j) contra defesa do {nome_fora} ({gs_fora:.1f} sofridos/j)."),
            ('Empate',
             empate_adj,
             f"Equilíbrio nos EngramScores ({EC_A:.1f} vs {EC_B:.1f})."),
            ('Vitória do ' + nome_fora,
             vitoria_fora_adj,
             f"{nome_fora} com {gm_fora:.1f} gols/j contra defesa de {gs_casa:.1f}."),
            ('Over 1.5 Gols',
             over15_adj,
             f"λ total ajustado: {lambda_casa_adj+lambda_fora_adj:.2f}."),
            ('Over 2.5 Gols',
             over25_adj,
             f"λ total ajustado: {lambda_casa_adj+lambda_fora_adj:.2f}."),
            ('Over 3.5 Gols',
             over35_adj,
             f"Possibilidade de placar elástico."),
            ('Ambos Marcam (BTTS)',
             btts_adj,
             f"{nome_casa} ({gm_casa:.1f}/{gs_casa:.1f}) x {nome_fora} ({gm_fora:.1f}/{gs_fora:.1f})."),
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

    def valor_com_destaque(valor, prob):
        """Retorna o HTML do valor com destaque dourado se >= 75%."""
        if prob >= 0.75:
            return f'<span class="high-confidence" style="font-size:42px;">{valor:.1%}</span>'
        else:
            return f'<span style="font-size:42px; font-weight:900; color:#E0E0E0;">{valor:.1%}</span>'

    # ==================== EXIBIÇÃO PRINCIPAL ====================
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center; margin-bottom:30px;">
        <div style="font-size:13px; text-transform:uppercase; letter-spacing:4px; color:#B0B8C0;">Resultado da Análise</div>
        <h2 style="font-weight:900; margin:8px 0; letter-spacing:-1px;">
            <span style="background:linear-gradient(180deg, #F0C040 0%, #D4A017 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                ENGRAMSCORE
            </span>
        </h2>
    </div>
    """, unsafe_allow_html=True)

    col_ec1, col_ec2 = st.columns(2)
    with col_ec1:
        st.markdown(f"""
        <div class="card-premium" style="text-align:center;">
            <div style="font-size:14px; text-transform:uppercase; letter-spacing:3px; color:#B0B8C0; margin-bottom:10px;">🏠 {nome_casa}</div>
            <div class="metric-premium">{EC_A:.1f}</div>
            <div class="metric-label-premium">EngramScore</div>
            <div class="bar-premium">
                <div class="bar-fill-gold" style="width:{EC_A}%;"></div>
            </div>
            <div style="font-size:12px; color:#B0B8C0; margin-top:4px;">MA · FG · CPP · PSICOLÓGICO</div>
        </div>
        """, unsafe_allow_html=True)

    with col_ec2:
        st.markdown(f"""
        <div class="card-premium" style="text-align:center;">
            <div style="font-size:14px; text-transform:uppercase; letter-spacing:3px; color:#B0B8C0; margin-bottom:10px;">✈️ {nome_fora}</div>
            <div class="metric-premium-blue">{EC_B:.1f}</div>
            <div class="metric-label-premium">EngramScore</div>
            <div class="bar-premium">
                <div class="bar-fill-blue" style="width:{EC_B}%;"></div>
            </div>
            <div style="font-size:12px; color:#B0B8C0; margin-top:4px;">MA · FG · CPP · PSICOLÓGICO</div>
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
        <span style="font-size:13px; text-transform:uppercase; letter-spacing:3px; color:#B0B8C0;">Análises Detalhadas</span>
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
        "🌟 DESTAQUES",
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
                <div style="font-size:13px; color:#B0B8C0; margin-top:8px;">Dominância: {estilo_A:.1f}/100</div>
            </div>
            """, unsafe_allow_html=True)
        with col_perf2:
            st.markdown(f"""
            <div style="background:rgba(74,144,217,0.05); border:1px solid rgba(74,144,217,0.2); border-radius:12px; padding:20px; text-align:center;">
                <div style="font-size:18px; font-weight:700; color:#4A90D9; margin-bottom:8px;">✈️ {nome_fora}</div>
                <div style="font-size:24px; font-weight:900; color:#4A90D9;">{perfil_B}</div>
                <div style="font-size:13px; color:#B0B8C0; margin-top:8px;">Dominância: {estilo_B:.1f}/100</div>
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
            <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.03); font-size:14px; color:#E0E0E0;">
                <span>{nome}</span>
                <span>{nome_casa} {vA:.1f} × {vB:.1f} {nome_fora}</span>
                <span style="font-weight:700; color:#F0C040;">{vant}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ----- ABA 4: Heatmap (CAMPO REAL) -----
    with tabs[3]:
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">🗺️ HEATMAP TÁTICO</div>', unsafe_allow_html=True)
        fA = [def_A/100, mei_A/100, atq_A/100]
        fB = [atq_B/100, mei_B/100, def_B/100]
        fig_field = desenhar_campo_duplo(fA, fB, nome_casa, nome_fora)
        st.plotly_chart(fig_field, use_container_width=True)
        st.markdown('<div style="font-size:13px; color:#B0B8C0; text-align:center;">As cores indicam a força nos setores: dourado para o mandante, azul para o visitante.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ----- ABA 5: Cenários -----
    with tabs[4]:
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">🎲 CINCO CENÁRIOS MAIS PROVÁVEIS</div>', unsafe_allow_html=True)
        cenarios = gerar_cenarios_justificados()
        for i, (titulo, prob, just) in enumerate(cenarios):
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.02); border-radius:8px; padding:12px 16px; margin:6px 0;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:700; color:#E0E0E0;">{i+1}. {titulo}</span>
                    <span style="font-size:20px; font-weight:900; color:#F0C040;">{prob:.1%}</span>
                </div>
                <div style="font-size:13px; color:#B0B8C0; margin-top:4px;">{just}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ----- ABA 6: Ajuste EC -----
    with tabs[5]:
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">🔧 AJUSTE ENGRAMSCORE NOS GOLS ESPERADOS</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="text-align:center; margin:16px 0;">
            <span style="font-size:14px; color:#B0B8C0;">Fator de Ajuste:</span>
            <span style="font-size:24px; font-weight:900; color:#F0C040; margin-left:8px;">{fator_ajuste:+.2f}</span>
        </div>
        """, unsafe_allow_html=True)
        col_orig, col_adj = st.columns(2)
        with col_orig:
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.02); border-radius:8px; padding:16px; text-align:center;">
                <div style="font-size:13px; color:#B0B8C0;">Lambdas Originais</div>
                <div style="font-size:28px; font-weight:900; color:#B0B8C0;">λ Casa: {lambda_casa_orig:.2f}</div>
                <div style="font-size:28px; font-weight:900; color:#B0B8C0;">λ Fora: {lambda_fora_orig:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_adj:
            st.markdown(f"""
            <div style="background:rgba(240,192,64,0.03); border:1px solid rgba(240,192,64,0.2); border-radius:8px; padding:16px; text-align:center;">
                <div style="font-size:13px; color:#F0C040;">Lambdas Ajustados</div>
                <div style="font-size:28px; font-weight:900; color:#F0C040;">λ Casa: {lambda_casa_adj:.2f}</div>
                <div style="font-size:28px; font-weight:900; color:#F0C040;">λ Fora: {lambda_fora_adj:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("""
        <div class="info-card" style="margin-top:16px;">
            Se o time da casa é muito superior (EC_A > EC_B), seu λ ofensivo <strong>aumenta</strong> e o λ do visitante <strong>diminui</strong>.
            Isso reduz a chance de o time mais fraco marcar, refletindo a superioridade medida pelo EngramScore.
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ----- ABA 7: Mercados (COM GOL HT INTEGRADO) -----
    with tabs[6]:
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">📊 PROBABILIDADES 1X2</div>', unsafe_allow_html=True)
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            st.markdown(f"""
            <div class="prob-box">
                <div style="color:#00E676; font-size:14px; text-transform:uppercase; letter-spacing:1px;">Vitória {nome_casa}</div>
                {valor_com_destaque(p_A, p_A)}
                <div style="margin-top:8px;">{selo(p_A)}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_p2:
            st.markdown(f"""
            <div class="prob-box">
                <div style="color:#F0C040; font-size:14px; text-transform:uppercase; letter-spacing:1px;">Empate</div>
                {valor_com_destaque(p_emp, p_emp)}
                <div style="margin-top:8px;">{selo(p_emp)}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_p3:
            st.markdown(f"""
            <div class="prob-box">
                <div style="color:#4A90D9; font-size:14px; text-transform:uppercase; letter-spacing:1px;">Vitória {nome_fora}</div>
                {valor_com_destaque(p_B, p_B)}
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
        col_g4, col_g5, col_g6 = st.columns(3)
        col_g4.metric("Ambos Marcam (BTTS)", f"{btts_adj:.1%}")
        col_g5.metric("BTTS Não", f"{1-btts_adj:.1%}")
        col_g6.metric("Gol 1º Tempo (HT)", f"{prob_gol_ht_adj:.1%}")
        st.markdown(f"""
        <div class="info-card">
            <strong>λ original:</strong> Casa {lambda_casa_orig:.2f}, Fora {lambda_fora_orig:.2f}<br>
            <strong>λ ajustado:</strong> Casa {lambda_casa_adj:.2f}, Fora {lambda_fora_adj:.2f}
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ----- ABA 8: DESTAQUES (COM GOL HT) -----
    with tabs[7]:
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">🌟 DESTAQUES (PROBABILIDADE &gt; 65%)</div>', unsafe_allow_html=True)
        
        destaques = []
        if p_A > 0.65:
            destaques.append((f"Vitória {nome_casa}", p_A))
        if p_emp > 0.65:
            destaques.append(("Empate", p_emp))
        if p_B > 0.65:
            destaques.append((f"Vitória {nome_fora}", p_B))
        if over15_adj > 0.65:
            destaques.append(("Over 1.5 Gols", over15_adj))
        if over25_adj > 0.65:
            destaques.append(("Over 2.5 Gols", over25_adj))
        if over35_adj > 0.65:
            destaques.append(("Over 3.5 Gols", over35_adj))
        if btts_adj > 0.65:
            destaques.append(("Ambos Marcam (BTTS)", btts_adj))
        if prob_gol_ht_adj > 0.65:
            destaques.append(("Gol 1º Tempo", prob_gol_ht_adj))
        
        if destaques:
            for nome, prob in destaques:
                st.markdown(f"""
                <div style="background:rgba(240,192,64,0.08); border:1px solid rgba(240,192,64,0.3); border-radius:10px; padding:14px; margin:6px 0; display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:#F0C040; font-weight:700;">{nome}</span>
                    <span style="font-size:24px; font-weight:900; background:linear-gradient(180deg, #F0C040 0%, #D4A017 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">{prob:.1%}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#B0B8C0; text-align:center;">Nenhuma probabilidade acima de 65%.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ----- ABA 9: Análise Descritiva (MAIS PRECISA) -----
    with tabs[8]:
        st.markdown('<div class="card-premium">', unsafe_allow_html=True)
        st.markdown('<div class="card-header-premium">📝 ANÁLISE DESCRITIVA COMPLETA</div>', unsafe_allow_html=True)

        st.markdown("### 🔍 Pilares Individuais")
        st.markdown(f"""
        <div class="info-card">
            <strong>Momento Atual (MA):</strong> {nome_casa} {ma_A:.1f} × {nome_fora} {ma_B:.1f}. 
            {'O time da casa vive melhor fase.' if ma_A > ma_B else 'O visitante chega em melhor momento.' if ma_B > ma_A else 'Ambos estão em momentos semelhantes.'}<br>
            <strong>Força Geral (FG):</strong> {nome_casa} {fg_A:.1f} × {nome_fora} {fg_B:.1f}. 
            {'A casa tem um elenco mais forte.' if fg_A > fg_B else 'O visitante possui maior força geral.' if fg_B > fg_A else 'Força equilibrada.'}<br>
            <strong>Confronto por Prateleira (CPP):</strong> {nome_casa} {cpp_A:.1f} × {nome_fora} {cpp_B:.1f}. 
            {'Bom histórico contra times do mesmo nível.' if cpp_A > 60 else 'Histórico regular.' if cpp_A > 40 else 'Desempenho ruim contra pares.'}<br>
            <strong>Psicológico:</strong> {nome_casa} {psic_A:.1f} × {nome_fora} {psic_B:.1f}. 
            {'Time da casa mais confiante.' if psic_A > psic_B else 'Visitante com melhor preparo mental.' if psic_B > psic_A else 'Fatores psicológicos empatados.'}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### ⚡ EngramScore")
        st.markdown(f"""
        <div class="info-card">
            O índice final: {nome_casa} <strong>{EC_A:.1f}</strong> vs {nome_fora} <strong>{EC_B:.1f}</strong>. 
            {'Vantagem clara para o mandante.' if EC_A > EC_B + 5 else 'O visitante é o favorito.' if EC_B > EC_A + 5 else 'Confronto extremamente equilibrado.'}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🎯 Desempenho Setorial")
        st.markdown(f"""
        <div class="info-card">
            <strong>Ataque:</strong> {nome_casa} {atq_A:.1f} × {nome_fora} {atq_B:.1f} → {'Ataque da casa mais eficiente.' if atq_A > atq_B else 'Visitante leva perigo.' if atq_B > atq_A else 'Ataques similares.'}<br>
            <strong>Defesa:</strong> {nome_casa} {def_A:.1f} × {nome_fora} {def_B:.1f} → {'Defesa mandante mais segura.' if def_A > def_B else 'Visitante defende melhor.' if def_B > def_A else 'Defesas equivalentes.'}<br>
            <strong>Meio-campo:</strong> {nome_casa} {mei_A:.1f} × {nome_fora} {mei_B:.1f} → {'Casa controla o meio.' if mei_A > mei_B else 'Visitante pode dominar a posse.' if mei_B > mei_A else 'Disputa equilibrada.'}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🎭 Estilos de Jogo")
        st.markdown(f"""
        <div class="info-card">
            {nome_casa} é <strong>{perfil_A}</strong> (dominância {estilo_A:.1f}), {nome_fora} é <strong>{perfil_B}</strong> (dominância {estilo_B:.1f}). 
            {'O estilo dominante da casa pode sufocar o visitante.' if 'Dominante' in perfil_A and 'Reativo' in perfil_B else 'O visitante reativo pode explorar contra-ataques.' if 'Reativo' in perfil_B else 'Ambos os estilos podem se neutralizar.'}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📊 Expectativa de Gols (λ ajustados)")
        st.markdown(f"""
        <div class="info-card">
            Com base nos lambdas ajustados, a expectativa de gols é de <strong>{lambda_casa_adj+lambda_fora_adj:.2f}</strong> no total.
            Isso resulta em Over 1.5 com <strong>{over15_adj:.1%}</strong>, Over 2.5 com <strong>{over25_adj:.1%}</strong> e Over 3.5 com <strong>{over35_adj:.1%}</strong>.
            Ambos marcarem (BTTS) tem probabilidade de <strong>{btts_adj:.1%}</strong>. Gol no 1º tempo: <strong>{prob_gol_ht_adj:.1%}</strong>.
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
        # Combina EC com probabilidades para uma conclusão mais precisa
        if p_A >= 0.65:
            st.markdown(f"""
            <div class="info-card" style="border-color:#00E676;">
                Com <strong>{p_A:.1%}</strong> de chance, <strong>{nome_casa}</strong> é o grande favorito. Seu EngramScore de {EC_A:.1f} contra {EC_B:.1f} do adversário indica superioridade em todos os pilares. 
                A expectativa de gols é de {lambda_casa_adj+lambda_fora_adj:.2f}, com Over 1.5 em {over15_adj:.1%}. 
                Um cenário de vitória confortável se desenha.
            </div>
            """, unsafe_allow_html=True)
        elif p_B >= 0.65:
            st.markdown(f"""
            <div class="info-card" style="border-color:#00E676;">
                Apesar de visitante, <strong>{nome_fora}</strong> tem <strong>{p_B:.1%}</strong> de vencer, com EngramScore de {EC_B:.1f} contra {EC_A:.1f}. 
                O time da casa precisará superar a desvantagem nos pilares. 
                Espera-se um jogo com {lambda_casa_adj+lambda_fora_adj:.2f} gols em média, e o visitante deve impor seu ritmo.
            </div>
            """, unsafe_allow_html=True)
        elif abs(EC_A - EC_B) <= 5 and p_emp > 0.3:
            st.markdown(f"""
            <div class="info-card" style="border-color:#F0C040;">
                Confronto equilibrado: EngramScores próximos ({EC_A:.1f} vs {EC_B:.1f}) e empate com {p_emp:.1%} de probabilidade. 
                A partida deve ser disputada, com {lambda_casa_adj+lambda_fora_adj:.2f} gols esperados. 
                Ambos os times têm chances reais, e o empate é um resultado plausível.
            </div>
            """, unsafe_allow_html=True)
        else:
            if EC_A > EC_B:
                st.markdown(f"""
                <div class="info-card" style="border-color:#F0C040;">
                    <strong>{nome_casa}</strong> parte com ligeira vantagem (EngramScore {EC_A:.1f} vs {EC_B:.1f}), 
                    mas o visitante não pode ser subestimado. A probabilidade de vitória da casa é de {p_A:.1%}, 
                    com empate em {p_emp:.1%}. A expectativa de gols é de {lambda_casa_adj+lambda_fora_adj:.2f}.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="info-card" style="border-color:#F0C040;">
                    <strong>{nome_fora}</strong> tem um EngramScore superior ({EC_B:.1f} vs {EC_A:.1f}), 
                    sugerindo que pode surpreender fora de casa. Probabilidade de vitória visitante: {p_B:.1%}. 
                    Espera-se um jogo com {lambda_casa_adj+lambda_fora_adj:.2f} gols em média.
                </div>
                """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Rodapé
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center; padding:20px; color:#B0B8C0; font-size:13px; letter-spacing:2px;">
        ENGRAMSCORE © 2026 · ANÁLISE DIFERENCIAL DE FORÇA
    </div>
    """, unsafe_allow_html=True)
