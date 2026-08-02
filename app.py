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
# CONFIGURAÇÃO INICIAL DA PÁGINA
# ------------------------------------------------------------
st.set_page_config(
    page_title="EngramsCore ⚽",
    page_icon="⚽",
    layout="wide",
)

# ------------------------------------------------------------
# ESTILO CSS PERSONALIZADO
# ------------------------------------------------------------
st.markdown("""
<style>
    /* Fundo geral */
    .stApp {
        background-color: #0B0F19;
        color: #E0E0E0;
    }
    /* Cabeçalhos */
    h1, h2, h3, h4 {
        color: #F0C040 !important;
        font-family: 'Segoe UI', sans-serif;
    }
    /* Cartões */
    .card {
        background: #1A1F2B;
        border: 1px solid #2A2F3B;
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }
    .card:hover {
        border-color: #F0C040;
        box-shadow: 0 0 16px rgba(240,192,64,0.3);
    }
    .card-header {
        color: #F0C040;
        font-size: 1.2em;
        font-weight: bold;
        margin-bottom: 16px;
    }
    /* Botões */
    .stButton>button {
        background: linear-gradient(135deg, #F0C040, #C89B20);
        color: #0B0F19;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 12px 32px;
        font-size: 1.1em;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #FFD966, #E0B030);
        box-shadow: 0 0 12px rgba(240,192,64,0.6);
    }
    /* Números grandes */
    .big-number {
        font-size: 3em;
        font-weight: bold;
        text-align: center;
        color: #F0C040;
    }
    .big-number-label {
        font-size: 1em;
        text-align: center;
        color: #A0A0A0;
    }
    /* Probabilidades */
    .prob-box {
        background: #141824;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        border: 1px solid #2A2F3B;
    }
    .prob-value {
        font-size: 2.5em;
        font-weight: bold;
        color: #F0C040;
    }
    /* Barra de força */
    .force-bar {
        height: 16px;
        border-radius: 8px;
        background: linear-gradient(90deg, #6B2737, #F0C040);
        margin: 8px 0;
    }
    .force-label {
        display: flex;
        justify-content: space-between;
        font-size: 0.9em;
    }
    /* Frases motivacionais */
    .quote {
        font-style: italic;
        color: #F0C040;
        text-align: center;
        font-size: 1.2em;
        margin: 16px 0;
        padding: 12px;
        border-left: 4px solid #F0C040;
        background: rgba(240,192,64,0.05);
    }
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background: #1A1F2B;
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        color: #A0A0A0;
    }
    .stTabs [aria-selected="true"] {
        background: #F0C040 !important;
        color: #0B0F19 !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# FRASE MOTIVACIONAL
# ------------------------------------------------------------
st.markdown("<div class='quote'>\"O conhecimento é o único caminho para a vitória constante.\"</div>", unsafe_allow_html=True)

# ------------------------------------------------------------
# CABEÇALHO
# ------------------------------------------------------------
st.markdown("<h1 style='text-align:center;'>⚽ ENGRAMS CORE</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#A0A0A0; font-size:1.1em;'>Sistema de Análise Esportiva Diferencial</p>", unsafe_allow_html=True)

# ------------------------------------------------------------
# BARRA LATERAL - CONFIGURAÇÃO DA LIGA
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🏆 Liga de Referência")
    st.markdown("Configure as médias da competição para calibrar as métricas.")
    with st.expander("⚙️ Médias da Liga", expanded=False):
        media_gm = st.number_input("Gols/jogo", 0.1, 5.0, 1.4, 0.1)
        media_fa = st.number_input("Finalizações alvo/jogo", 0.0, 10.0, 4.0, 0.1)
        media_eca = st.number_input("Escanteios a favor/jogo", 0.0, 20.0, 5.0, 0.1)
        media_posse = st.number_input("Posse (%)", 0.0, 100.0, 50.0, 1.0)
        media_gs = st.number_input("Gols sofridos/jogo", 0.1, 5.0, 1.4, 0.1)
        media_fas = st.number_input("Finalizações alvo sofridas/jogo", 0.0, 10.0, 4.0, 0.1)
        media_ecc = st.number_input("Escanteios contra/jogo", 0.0, 20.0, 5.0, 0.1)
        media_des = st.number_input("Desarmes/jogo", 0.0, 50.0, 15.0, 0.1)
        media_fc = st.number_input("Faltas/jogo", 0.0, 30.0, 12.0, 0.1)
        media_ca = st.number_input("Cartões amarelos/jogo", 0.0, 10.0, 2.0, 0.1)

    medias_liga = {
        'GM': media_gm, 'FA': media_fa, 'ECa': media_eca,
        'GS': media_gs, 'FAS': media_fas, 'ECc': media_ecc,
        'FC': media_fc, 'CA': media_ca, 'Des': media_des,
        'Posse': media_posse,
    }

# ------------------------------------------------------------
# DADOS DOS TIMES - DOIS CARDS LADO A LADO
# ------------------------------------------------------------
colA, colB = st.columns(2)

with colA:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>🏠 Time da Casa</div>", unsafe_allow_html=True)
        nome_casa = st.text_input("Nome", "Time A", key="casa")
        n_casa = st.number_input("Jogos na temporada", 1, 38, 10, key="nj_casa")
        res_casa = st.text_input("Últ. resultados (V/E/D)", "VVEDV", key="res_casa").upper()
        odd_casa = st.number_input("Odd Vitória", 1.01, 10.0, 1.80, 0.01, key="odd_casa")
        gm_casa = st.number_input("Gols/jogo", 0.0, 5.0, 2.0, 0.1, key="gm_casa")
        fa_casa = st.number_input("Finalizações alvo/j", 0.0, 10.0, 4.5, 0.1, key="fa_casa")
        eca_casa = st.number_input("Escanteios a favor/j", 0.0, 20.0, 5.5, 0.1, key="eca_casa")
        posse_casa = st.slider("Posse (%)", 0, 100, 55, key="posse_casa")
        gs_casa = st.number_input("Gols sofridos/j", 0.0, 5.0, 0.8, 0.1, key="gs_casa")
        fas_casa = st.number_input("Finalizações alvo sofridas/j", 0.0, 10.0, 3.0, 0.1, key="fas_casa")
        ecc_casa = st.number_input("Escanteios contra/j", 0.0, 20.0, 4.0, 0.1, key="ecc_casa")
        des_casa = st.number_input("Desarmes/j", 0.0, 50.0, 16.0, 0.1, key="des_casa")
        fc_casa = st.number_input("Faltas/j", 0.0, 30.0, 13.0, 0.1, key="fc_casa")
        ca_casa = st.number_input("Cartões amarelos/j", 0.0, 10.0, 2.2, 0.1, key="ca_casa")
        pts_cpp_casa = st.number_input("Pontos contra prateleira", 0, 30, 6, key="pcpp_casa")
        jogos_cpp_casa = st.number_input("Jogos contra prateleira", 0, 10, 3, key="jcpp_casa")
        prat_casa = st.selectbox("Prateleira", ["Elite","Alta","Média","Baixa","Crítica"], key="prat_casa")
        cons_casa = st.text_input("Últ. 10 jogos (V/E/D)", "VVEDVVEDVV", key="cons_casa").upper()
        moral_casa = st.slider("Moral (pts 3j)", 0, 9, 6, key="moral_casa")
        pos_casa = st.number_input("Posição na tabela", 1, 20, 2, key="pos_casa")
        st.markdown("</div>", unsafe_allow_html=True)

with colB:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>✈️ Time Visitante</div>", unsafe_allow_html=True)
        nome_fora = st.text_input("Nome", "Time B", key="fora")
        n_fora = st.number_input("Jogos na temporada", 1, 38, 10, key="nj_fora")
        res_fora = st.text_input("Últ. resultados (V/E/D)", "DDVVE", key="res_fora").upper()
        odd_fora = st.number_input("Odd Vitória", 1.01, 10.0, 4.00, 0.01, key="odd_fora")
        gm_fora = st.number_input("Gols/jogo", 0.0, 5.0, 1.2, 0.1, key="gm_fora")
        fa_fora = st.number_input("Finalizações alvo/j", 0.0, 10.0, 3.2, 0.1, key="fa_fora")
        eca_fora = st.number_input("Escanteios a favor/j", 0.0, 20.0, 4.5, 0.1, key="eca_fora")
        posse_fora = st.slider("Posse (%)", 0, 100, 48, key="posse_fora")
        gs_fora = st.number_input("Gols sofridos/j", 0.0, 5.0, 1.5, 0.1, key="gs_fora")
        fas_fora = st.number_input("Finalizações alvo sofridas/j", 0.0, 10.0, 3.8, 0.1, key="fas_fora")
        ecc_fora = st.number_input("Escanteios contra/j", 0.0, 20.0, 5.0, 0.1, key="ecc_fora")
        des_fora = st.number_input("Desarmes/j", 0.0, 50.0, 14.0, 0.1, key="des_fora")
        fc_fora = st.number_input("Faltas/j", 0.0, 30.0, 11.0, 0.1, key="fc_fora")
        ca_fora = st.number_input("Cartões amarelos/j", 0.0, 10.0, 1.8, 0.1, key="ca_fora")
        pts_cpp_fora = st.number_input("Pontos contra prateleira", 0, 30, 4, key="pcpp_fora")
        jogos_cpp_fora = st.number_input("Jogos contra prateleira", 0, 10, 2, key="jcpp_fora")
        prat_fora = st.selectbox("Prateleira", ["Elite","Alta","Média","Baixa","Crítica"], key="prat_fora")
        cons_fora = st.text_input("Últ. 10 jogos (V/E/D)", "DDVVEDDVV", key="cons_fora").upper()
        moral_fora = st.slider("Moral (pts 3j)", 0, 9, 3, key="moral_fora")
        pos_fora = st.number_input("Posição na tabela", 1, 20, 16, key="pos_fora")
        st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------
# BOTÃO DE ANÁLISE
# ------------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
analisar = st.button("🔍 GERAR ANÁLISE COMPLETA", type="primary", use_container_width=True)

if analisar:
    # --------------------------------------------------------
    # PROCESSAMENTO DOS DADOS
    # --------------------------------------------------------
    def parse_seq(s):
        return [3 if c == 'V' else 1 if c == 'E' else 0 for c in s if c in 'VED']

    seq_casa = parse_seq(res_casa)
    seq_fora = parse_seq(res_fora)
    seq_cons_casa = parse_seq(cons_casa)
    seq_cons_fora = parse_seq(cons_fora)

    odd_emp = st.number_input("Odd Empate", 1.01, 10.0, 3.50, key="odd_emp_global")

    # Probabilidades justas
    inv_sum = 1/odd_casa + 1/odd_emp + 1/odd_fora
    prob_v_casa = (1/odd_casa) / inv_sum
    prob_emp = (1/odd_emp) / inv_sum
    prob_v_fora = (1/odd_fora) / inv_sum

    # MA
    def ma_recente(seq, prob_v, prob_e, n_total):
        if not seq:
            return 50.0
        recente = seq[-6:]
        pts = sum(recente)
        jogos = len(recente)
        return calcular_ma(pts, jogos, n_total, prob_v, prob_e)

    ma_A = ma_recente(seq_casa, prob_v_casa, prob_emp, n_casa)
    ma_B = ma_recente(seq_fora, prob_v_fora, prob_emp, n_fora)

    # FG
    dados_A = {
        'GM': gm_casa, 'FA': fa_casa, 'ECa': eca_casa, 'Posse': posse_casa,
        'GS': gs_casa, 'FAS': fas_casa, 'ECc': ecc_casa, 'Des': des_casa,
        'FC': fc_casa, 'CA': ca_casa,
    }
    dados_B = {
        'GM': gm_fora, 'FA': fa_fora, 'ECa': eca_fora, 'Posse': posse_fora,
        'GS': gs_fora, 'FAS': fas_fora, 'ECc': ecc_fora, 'Des': des_fora,
        'FC': fc_fora, 'CA': ca_fora,
    }
    fg_A = calcular_fg(dados_A, medias_liga, n_casa)
    fg_B = calcular_fg(dados_B, medias_liga, n_fora)

    # CPP
    cpp_A = calcular_cpp(pts_cpp_casa, jogos_cpp_casa, prob_v_casa, prob_emp)
    cpp_B = calcular_cpp(pts_cpp_fora, jogos_cpp_fora, prob_v_fora, prob_emp)

    # Estilo
    estilo_A = calcular_estilo(dados_A, medias_liga, n_casa)
    estilo_B = calcular_estilo(dados_B, medias_liga, n_fora)

    # Perfil tático
    perfil_A = obter_perfil_time(dados_A, medias_liga)
    perfil_B = obter_perfil_time(dados_B, medias_liga)

    # Pressão
    dif_pts = (pos_casa - pos_fora) * 3  # estimativa
    p_obj_A = calcular_pressao_tabela(pos_casa, 20, pos_fora, dif_pts)
    p_obj_B = calcular_pressao_tabela(pos_fora, 20, pos_casa, -dif_pts)

    # Psicológico
    psic_A = calcular_psicologico(
        consistencia_pontos=seq_cons_casa if len(seq_cons_casa)>=5 else None,
        moral_pontos=moral_casa,
        pressao_p_obj=p_obj_A,
        pressao_sensibilidade=0.3,
    )
    psic_B = calcular_psicologico(
        consistencia_pontos=seq_cons_fora if len(seq_cons_fora)>=5 else None,
        moral_pontos=moral_fora,
        pressao_p_obj=p_obj_B,
        pressao_sensibilidade=0.3,
    )

    # --------------------------------------------------------
    # ENGRAMS CORE (cálculo do EC e probabilidades)
    # --------------------------------------------------------
    pesos = {'MA': 0.25, 'FG': 0.25, 'CPP': 0.25, 'Psicologico': 0.25}
    ec_A = (ma_A * pesos['MA'] + fg_A * pesos['FG'] + cpp_A * pesos['CPP'] + psic_A * pesos['Psicologico'])
    ec_B = (ma_B * pesos['MA'] + fg_B * pesos['FG'] + cpp_B * pesos['CPP'] + psic_B * pesos['Psicologico'])
    # Bônus casa
    ec_A += 2.0
    ec_A = max(0, min(100, ec_A))
    ec_B = max(0, min(100, ec_B))

    total = ec_A + ec_B
    diff_rel = abs(ec_A - ec_B) / total if total > 0 else 0
    p_emp = max(0.18, 0.40 - diff_rel * 0.3)
    p_A = (1 - p_emp) * (ec_A / total) if total > 0 else 0.33
    p_B = 1 - p_A - p_emp

    # --------------------------------------------------------
    # EXIBIÇÃO DOS RESULTADOS
    # --------------------------------------------------------
    st.markdown("---")
    st.markdown("<h2 style='text-align:center;'>📊 Resultado da Análise</h2>", unsafe_allow_html=True)

    # Cards principais com EC
    col_ec1, col_ec2, col_ec3 = st.columns(3)
    with col_ec1:
        st.markdown(f"<div class='card'><div class='card-header'>🏠 {nome_casa}</div><div class='big-number'>{ec_A:.1f}</div><div class='big-number-label'>Índice de Força</div></div>", unsafe_allow_html=True)
    with col_ec2:
        st.markdown(f"<div class='card'><div class='card-header'>🤝 Empate</div><div class='big-number'>{p_emp:.1%}</div><div class='big-number-label'>Probabilidade</div></div>", unsafe_allow_html=True)
    with col_ec3:
        st.markdown(f"<div class='card'><div class='card-header'>✈️ {nome_fora}</div><div class='big-number'>{ec_B:.1f}</div><div class='big-number-label'>Índice de Força</div></div>", unsafe_allow_html=True)

    # Probabilidades 1X2 detalhadas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='prob-box'>", unsafe_allow_html=True)
        st.markdown(f"<span style='color:#00cc66;'>Vitória {nome_casa}</span>", unsafe_allow_html=True)
        st.markdown(f"<div class='prob-value'>{p_A:.1%}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='prob-box'>", unsafe_allow_html=True)
        st.markdown("<span style='color:#F0C040;'>Empate</span>", unsafe_allow_html=True)
        st.markdown(f"<div class='prob-value'>{p_emp:.1%}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='prob-box'>", unsafe_allow_html=True)
        st.markdown(f"<span style='color:#4a90d9;'>Vitória {nome_fora}</span>", unsafe_allow_html=True)
        st.markdown(f"<div class='prob-value'>{p_B:.1%}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # ABAS DE ANÁLISE DETALHADA
    # --------------------------------------------------------
    tabs = st.tabs(["📈 Força & Pilares", "⚔️ Comparação Setorial", "🧠 Análise Técnica", "💰 Mercados"])

    # ----- ABA 1: Força & Pilares -----
    with tabs[0]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>🔍 Comparativo de Pilares</div>", unsafe_allow_html=True)
        pilares_nomes = ['Momento Atual', 'Força Geral', 'Confronto', 'Psicológico']
        valores_A = [ma_A, fg_A, cpp_A, psic_A]
        valores_B = [ma_B, fg_B, cpp_B, psic_B]
        df_pilares = pd.DataFrame({
            'Pilar': pilares_nomes * 2,
            'Time': [nome_casa]*4 + [nome_fora]*4,
            'Força': valores_A + valores_B
        })
        fig_pilares = px.bar(df_pilares, x='Pilar', y='Força', color='Time',
                             barmode='group', text_auto='.1f',
                             color_discrete_map={nome_casa: '#F0C040', nome_fora: '#4a90d9'})
        fig_pilares.update_layout(template='plotly_dark', paper_bgcolor='#0B0F19', plot_bgcolor='#0B0F19')
        st.plotly_chart(fig_pilares, use_container_width=True)
        st.markdown("<p style='color:#A0A0A0;'>Barras mais altas indicam maior força no pilar. O dourado representa o time da casa.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Radar de Força Geral
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>🎯 Força Geral (Estilo FIFA)</div>", unsafe_allow_html=True)
        def norm_rad(val, media):
            if media == 0: return 50
            return max(0, min(100, 50 + (val - media)/media * 50))
        atq_A = (norm_rad(gm_casa, media_gm) + norm_rad(fa_casa, media_fa)) / 2
        def_A = (100 - norm_rad(gs_casa, media_gs) + 100 - norm_rad(fas_casa, media_fas)) / 2
        mei_A = norm_rad(posse_casa, media_posse)
        atq_B = (norm_rad(gm_fora, media_gm) + norm_rad(fa_fora, media_fa)) / 2
        def_B = (100 - norm_rad(gs_fora, media_gs) + 100 - norm_rad(fas_fora, media_fas)) / 2
        mei_B = norm_rad(posse_fora, media_posse)

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=[atq_A, def_A, mei_A], theta=['Ataque','Defesa','Meio'],
            fill='toself', name=nome_casa, marker=dict(color='#F0C040')
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=[atq_B, def_B, mei_B], theta=['Ataque','Defesa','Meio'],
            fill='toself', name=nome_fora, marker=dict(color='#4a90d9')
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(range=[0,100])),
            template='plotly_dark', paper_bgcolor='#0B0F19'
        )
        st.plotly_chart(fig_radar, use_container_width=True)
        st.markdown("<p style='color:#A0A0A0;'>Quanto mais próximo da borda, melhor o setor. Compare as áreas coloridas.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Perfil tático
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>🎭 Perfis Táticos</div>", unsafe_allow_html=True)
        col_perf1, col_perf2 = st.columns(2)
        col_perf1.markdown(f"<h3>{nome_casa}</h3><p style='font-size:1.5em; color:#F0C040;'>{perfil_A}</p>", unsafe_allow_html=True)
        col_perf2.markdown(f"<h3>{nome_fora}</h3><p style='font-size:1.5em; color:#F0C040;'>{perfil_B}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Sequência de resultados
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>📈 Sequência Recente</div>", unsafe_allow_html=True)
        def plot_seq(seq, nome):
            cores = ['#00cc66' if c=='V' else '#F0C040' if c=='E' else '#cc3333' for c in seq]
            fig = go.Figure(data=go.Scatter(
                x=list(range(len(seq))), y=[1]*len(seq),
                mode='markers', marker=dict(color=cores, size=20),
                text=seq, hoverinfo='text'
            ))
            fig.update_layout(title=nome, yaxis_visible=False, template='plotly_dark', height=150)
            return fig
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.plotly_chart(plot_seq(list(res_casa), nome_casa), use_container_width=True)
        with col_s2:
            st.plotly_chart(plot_seq(list(res_fora), nome_fora), use_container_width=True)
        st.markdown("<p style='color:#A0A0A0;'>Verde = Vitória, Amarelo = Empate, Vermelho = Derrota.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ----- ABA 2: Comparação Setorial -----
    with tabs[1]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>⚔️ Confronto Direto por Setor</div>", unsafe_allow_html=True)
        setores = {
            'Ataque (Gols)': (gm_casa, gm_fora, 'maior melhor'),
            'Finalizações Alvo': (fa_casa, fa_fora, 'maior melhor'),
            'Posse de Bola (%)': (posse_casa, posse_fora, 'maior melhor'),
            'Defesa (Gols Sofridos)': (gs_casa, gs_fora, 'menor melhor'),
            'Finalizações Sofridas': (fas_casa, fas_fora, 'menor melhor'),
            'Disciplina (Faltas)': (fc_casa, fc_fora, 'menor melhor'),
        }
        for setor, (vA, vB, tipo) in setores.items():
            if tipo == 'maior melhor':
                vantagem = nome_casa if vA > vB else nome_fora if vB > vA else "Empate"
            else:
                vantagem = nome_casa if vA < vB else nome_fora if vB < vA else "Empate"
            st.markdown(f"**{setor}**: {nome_casa} {vA:.1f} vs {nome_fora} {vB:.1f} → Vantagem: **{vantagem}**")
        st.markdown("</div>", unsafe_allow_html=True)

    # ----- ABA 3: Análise Técnica -----
    with tabs[2]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>🧠 Análise Descritiva</div>", unsafe_allow_html=True)
        def descrever(nome, ma, fg, cpp, psi, perfil):
            texto = f"**{nome}** apresenta "
            if fg >= 65:
                texto += "uma Força Geral alta, indicando um time muito competitivo. "
            elif fg >= 50:
                texto += "uma Força Geral equilibrada. "
            else:
                texto += "uma Força Geral abaixo da média, mostrando fragilidades. "
            if ma >= 65:
                texto += "Seu Momento Atual é excelente, com ótimos resultados recentes. "
            elif ma >= 50:
                texto += "O Momento Atual é estável. "
            else:
                texto += "Vive um momento ruim, com resultados abaixo do esperado. "
            texto += f"O perfil tático identificado é **{perfil}**. "
            return texto
        desc_A = descrever(nome_casa, ma_A, fg_A, cpp_A, psic_A, perfil_A)
        desc_B = descrever(nome_fora, ma_B, fg_B, cpp_B, psic_B, perfil_B)
        st.markdown(desc_A)
        st.markdown(desc_B)

        if ec_A > ec_B:
            st.markdown(f"**Conclusão**: O modelo aponta uma ligeira vantagem para o **{nome_casa}**, mas o jogo promete ser equilibrado." if ec_A - ec_B < 10 else f"**Conclusão**: O **{nome_casa}** é claramente o favorito, com um Índice de Força bem superior.")
        else:
            st.markdown(f"**Conclusão**: O modelo aponta uma ligeira vantagem para o **{nome_fora}**, mas o jogo promete ser equilibrado." if ec_B - ec_A < 10 else f"**Conclusão**: O **{nome_fora}** é claramente o favorito, com um Índice de Força bem superior.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ----- ABA 4: Mercados -----
    with tabs[3]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>💰 Probabilidades de Gols</div>", unsafe_allow_html=True)
        # Cálculo rápido de over/under baseado nas médias de gols
        lambda_total = (gm_casa + gs_casa + gm_fora + gs_fora) / 2  # proxy
        def prob_over(lmbda, linha):
            prob = 0
            for k in range(int(linha)+1, 15):
                prob += math.exp(-lmbda) * lmbda**k / math.factorial(k)
            return 1 - sum(math.exp(-lmbda) * lmbda**k / math.factorial(k) for k in range(int(linha)+1))
        over15 = prob_over(lambda_total, 1.5)
        over25 = prob_over(lambda_total, 2.5)
        over35 = prob_over(lambda_total, 3.5)
        btts = (gm_casa * gs_fora + gm_fora * gs_casa) / (2 * lambda_total) if lambda_total > 0 else 0.5

        col_g1, col_g2, col_g3 = st.columns(3)
        col_g1.metric("Over 1.5 Gols", f"{over15:.1%}")
        col_g2.metric("Over 2.5 Gols", f"{over25:.1%}")
        col_g3.metric("Over 3.5 Gols", f"{over35:.1%}")
        col_g4, col_g5 = st.columns(2)
        col_g4.metric("BTTS (Ambos Marcam)", f"{btts:.1%}")
        col_g5.metric("BTTS Não", f"{1-btts:.1%}")
        st.markdown("</div>", unsafe_allow_html=True)

    # Frase motivacional final
    st.markdown("<div class='quote'>\"A sorte favorece a mente preparada.\" — Louis Pasteur</div>", unsafe_allow_html=True)
