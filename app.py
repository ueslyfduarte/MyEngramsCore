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

# Estilo CSS personalizado (azul escuro, dourado, bordô)
st.markdown("""
<style>
    .stApp { background-color: #0A0E17; color: #E0E0E0; }
    h1, h2, h3 { color: #F0C040; }
    .card {
        background: #1A1F2B; border: 1px solid #2A2F3B;
        border-radius: 16px; padding: 24px; margin: 16px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }
    .card:hover { border-color: #F0C040; box-shadow: 0 0 16px rgba(240,192,64,0.3); }
    .big-number {
        font-size: 3em; font-weight: bold; text-align: center; color: #F0C040;
    }
    .quote {
        font-style: italic; color: #F0C040; text-align: center;
        font-size: 1.2em; margin: 16px 0; padding: 12px;
        border-left: 4px solid #F0C040; background: rgba(240,192,64,0.05);
    }
    .stButton>button {
        background: linear-gradient(135deg, #F0C040, #C89B20);
        color: #0B0F19; font-weight: bold; border: none;
        border-radius: 8px; padding: 12px 32px; font-size: 1.1em;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #FFD966, #E0B030);
        box-shadow: 0 0 12px rgba(240,192,64,0.6);
    }
    .prob-box {
        background: #141824; border-radius: 16px; padding: 20px;
        text-align: center; border: 1px solid #2A2F3B;
        position: relative;
    }
    .prob-value { font-size: 2.5em; font-weight: bold; color: #F0C040; }
    .selo-dourado {
        border: 3px solid #F0C040; border-radius: 12px;
        padding: 4px 12px; background: #F0C040; color: #000;
        font-weight: bold; font-size: 0.8em; display: inline-block;
        margin-top: 8px;
    }
    .selo-verde {
        border: 2px solid #00cc66; border-radius: 10px;
        padding: 4px 12px; background: #0A0E17; color: #00cc66;
        font-weight: bold; font-size: 0.8em; display: inline-block;
        margin-top: 8px;
    }
    .selo-amarelo {
        border: 2px solid #F0C040; border-radius: 10px;
        padding: 4px 12px; background: #0A0E17; color: #F0C040;
        font-weight: bold; font-size: 0.8em; display: inline-block;
        margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Frase motivacional
st.markdown("<div class='quote'>\"A vitória pertence ao mais perseverante.\" — Napoleão Bonaparte</div>", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;'>⚽ MyEngramScore</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#A0A0A0;'>A Soma de Todos os Pilares</p>", unsafe_allow_html=True)

# ------------------------------------------------------------
# BARRA LATERAL - LIGA
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🏆 Liga de Referência")
    with st.expander("Médias da Liga", expanded=False):
        media_gm = st.number_input("Gols/jogo", 0.1, 5.0, 1.4, 0.1)
        media_fa = st.number_input("Finalizações alvo/j", 0.0, 10.0, 4.0, 0.1)
        media_eca = st.number_input("Escanteios a favor/j", 0.0, 20.0, 5.0, 0.1)
        media_posse = st.number_input("Posse (%)", 0.0, 100.0, 50.0, 1.0)
        media_gs = st.number_input("Gols sofridos/j", 0.1, 5.0, 1.4, 0.1)
        media_fas = st.number_input("Finalizações alvo sofridas/j", 0.0, 10.0, 4.0, 0.1)
        media_ecc = st.number_input("Escanteios contra/j", 0.0, 20.0, 5.0, 0.1)
        media_des = st.number_input("Desarmes/j", 0.0, 50.0, 15.0, 0.1)
        media_fc = st.number_input("Faltas/j", 0.0, 30.0, 12.0, 0.1)
        media_ca = st.number_input("Cartões amarelos/j", 0.0, 10.0, 2.0, 0.1)

medias_liga = {
    'GM': media_gm, 'FA': media_fa, 'ECa': media_eca,
    'GS': media_gs, 'FAS': media_fas, 'ECc': media_ecc,
    'FC': media_fc, 'CA': media_ca, 'Des': media_des, 'Posse': media_posse,
}

# ------------------------------------------------------------
# ENTRADA DE DADOS DOS TIMES
# ------------------------------------------------------------
colA, colB = st.columns(2)

with colA:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>🏠 Time da Casa</div>", unsafe_allow_html=True)
        nome_casa = st.text_input("Nome", "Time A", key="casa")
        n_casa = st.number_input("Jogos na temporada", 1, 38, 10, key="nj_casa")
        res_casa = st.text_input("Últ. resultados (V/E/D)", "VVEDV", key="res_casa").upper()
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
# ODDS 1X2 (ANTES DO BOTÃO)
# ------------------------------------------------------------
st.markdown("---")
st.markdown("### 💰 Odds do Mercado (1X2)")
col_odd1, col_odd2, col_odd3 = st.columns(3)
with col_odd1:
    odd_casa = st.number_input("Vitória Casa", 1.01, 10.0, 1.80, 0.01, key="odd_casa")
with col_odd2:
    odd_empate = st.number_input("Empate", 1.01, 10.0, 3.50, 0.01, key="odd_empate")
with col_odd3:
    odd_fora = st.number_input("Vitória Fora", 1.01, 10.0, 4.00, 0.01, key="odd_fora")

# ------------------------------------------------------------
# BOTÃO DE ANÁLISE
# ------------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
if st.button("🔍 GERAR MyEngramScore", type="primary", width='stretch'):
    # -------------------------------
    # PROCESSAMENTO DOS DADOS
    # -------------------------------
    def parse_seq(s):
        return [3 if c == 'V' else 1 if c == 'E' else 0 for c in s if c in 'VED']
    seq_casa = parse_seq(res_casa)
    seq_fora = parse_seq(res_fora)
    seq_cons_casa = parse_seq(cons_casa)
    seq_cons_fora = parse_seq(cons_fora)

    # Probabilidades justas (removendo margem)
    inv_sum = 1/odd_casa + 1/odd_empate + 1/odd_fora
    prob_v_casa = (1/odd_casa) / inv_sum
    prob_emp = (1/odd_empate) / inv_sum
    prob_v_fora = (1/odd_fora) / inv_sum

    # MA
    def ma_recente(seq, pv, pe, n_total):
        if not seq: return 50.0
        recente = seq[-6:]
        return calcular_ma(sum(recente), len(recente), n_total, pv, pe)
    ma_A = ma_recente(seq_casa, prob_v_casa, prob_emp, n_casa)
    ma_B = ma_recente(seq_fora, prob_v_fora, prob_emp, n_fora)

    # FG
    dados_A = {'GM': gm_casa, 'FA': fa_casa, 'ECa': eca_casa, 'Posse': posse_casa,
               'GS': gs_casa, 'FAS': fas_casa, 'ECc': ecc_casa, 'Des': des_casa,
               'FC': fc_casa, 'CA': ca_casa}
    dados_B = {'GM': gm_fora, 'FA': fa_fora, 'ECa': eca_fora, 'Posse': posse_fora,
               'GS': gs_fora, 'FAS': fas_fora, 'ECc': ecc_fora, 'Des': des_fora,
               'FC': fc_fora, 'CA': ca_fora}
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
    dif_pts = (pos_casa - pos_fora) * 3
    p_obj_A = calcular_pressao_tabela(pos_casa, 20, pos_fora, dif_pts)
    p_obj_B = calcular_pressao_tabela(pos_fora, 20, pos_casa, -dif_pts)

    # Psicológico
    psic_A = calcular_psicologico(
        consistencia_pontos=seq_cons_casa if len(seq_cons_casa)>=5 else None,
        moral_pontos=moral_casa, pressao_p_obj=p_obj_A, pressao_sensibilidade=0.3)
    psic_B = calcular_psicologico(
        consistencia_pontos=seq_cons_fora if len(seq_cons_fora)>=5 else None,
        moral_pontos=moral_fora, pressao_p_obj=p_obj_B, pressao_sensibilidade=0.3)

    # -------------------------------
    # ENGRAMS CORE (MyEngramScore)
    # -------------------------------
    PESOS = {'MA': 0.25, 'FG': 0.25, 'CPP': 0.25, 'Psicologico': 0.25}
    EC_A = (ma_A*PESOS['MA'] + fg_A*PESOS['FG'] + cpp_A*PESOS['CPP'] + psic_A*PESOS['Psicologico'])
    EC_B = (ma_B*PESOS['MA'] + fg_B*PESOS['FG'] + cpp_B*PESOS['CPP'] + psic_B*PESOS['Psicologico'])
    EC_A += 2.0  # bônus casa
    EC_A = max(0, min(100, EC_A))
    EC_B = max(0, min(100, EC_B))

    # Probabilidades 1X2 (não mudam)
    total = EC_A + EC_B
    diff_rel = abs(EC_A - EC_B)/total if total>0 else 0
    p_emp = max(0.18, 0.40 - diff_rel*0.3)
    p_A = (1 - p_emp) * (EC_A/total) if total>0 else 0.33
    p_B = 1 - p_A - p_emp

    # -------------------------------
    # LAMBDAS ORIGINAIS (para referência)
    # -------------------------------
    lambda_casa_orig = (gm_casa + gs_fora) / 2
    lambda_fora_orig = (gm_fora + gs_casa) / 2

    # -------------------------------
    # AJUSTE DOS LAMBDAS PELO MYENGRAMSCORE
    # -------------------------------
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

    # Recalcular todas as probabilidades de gols com lambdas ajustados
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

    # Gol no 1º Tempo (modelo próprio, ajustado)
    FATOR_HT = 0.44
    ajuste_estilo = 0
    if perfil_A in ["Pressão Alta", "Dominante"]:
        ajuste_estilo += 0.05
    if perfil_B in ["Pressão Alta", "Dominante"]:
        ajuste_estilo -= 0.05
    ajuste_ma = (ma_A - 50) * 0.001 + (ma_B - 50) * 0.001
    lambda_ht_adj = (lambda_casa_adj + lambda_fora_adj) * (FATOR_HT + ajuste_estilo + ajuste_ma)
    prob_gol_ht_adj = 1 - math.exp(-lambda_ht_adj)

    # -------------------------------
    # FUNÇÕES AUXILIARES (VISUALIZAÇÃO)
    # -------------------------------
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
             f"Ataque eficiente do {nome_casa} ({gm_casa:.1f} gols/j) contra defesa do {nome_fora} ({gs_fora:.1f} sofridos/j). MyEngramScore {EC_A:.1f} vs {EC_B:.1f}."),
            ('Empate',
             empate_adj,
             f"Equilíbrio nos ECs ({EC_A:.1f} vs {EC_B:.1f}) e histórico de confrontos parelhos."),
            ('Vitória do ' + nome_fora,
             vitoria_fora_adj,
             f"{nome_fora} explora os espaços deixados pelo {nome_casa} ({gs_casa:.1f} sofridos/j) com seus {gm_fora:.1f} gols/j."),
            ('Over 1.5 Gols',
             over15_adj,
             f"Média de {lambda_casa_adj+lambda_fora_adj:.2f} gols esperados (já ajustada pelo MyEngramScore)."),
            ('Over 2.5 Gols',
             over25_adj,
             f"Com λ ajustado total de {lambda_casa_adj+lambda_fora_adj:.2f}, probabilidade de 3+ gols."),
            ('Over 3.5 Gols',
             over35_adj,
             f"Ataques podem render um placar mais elástico, especialmente se a defesa falhar."),
            ('Ambos Marcam (BTTS)',
             btts_adj,
             f"{nome_casa} marca {gm_casa:.1f} e sofre {gs_casa:.1f}; {nome_fora} marca {gm_fora:.1f} e sofre {gs_fora:.1f}. Ajuste EC reduziu λ_fora para {lambda_fora_adj:.2f}."),
        ]
        eventos.sort(key=lambda x: x[1], reverse=True)
        return eventos[:5]

    def selo(prob):
        if prob >= 0.75:
            return '<span class="selo-dourado">🏅 MyEngramScore Ouro</span>'
        elif prob >= 0.60:
            return '<span class="selo-verde">✅ Confiável</span>'
        elif prob >= 0.50:
            return '<span class="selo-amarelo">⚠️ Moderado</span>'
        else:
            return ''

    # -------------------------------
    # MY ENGRAM SCORE (APENAS OS DOIS ÍNDICES)
    # -------------------------------
    st.markdown("---")
    st.markdown("<h2 style='text-align:center;'>⚡ MyEngramScore</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#A0A0A0;'>Índice de Força Absoluta — como o rating de um videogame</p>", unsafe_allow_html=True)

    col_ec1, col_ec2 = st.columns(2)
    with col_ec1:
        st.markdown(f"""
        <div class='card' style='text-align:center;'>
            <div class='card-header'>🏠 {nome_casa}</div>
            <div class='big-number'>{EC_A:.1f}</div>
            <div class='force-bar' style='width:100%; background:#2A2F3B; border-radius:8px; margin-top:12px;'>
                <div style='width:{EC_A}%; height:12px; background:linear-gradient(90deg, #F0C040, #D4A017); border-radius:8px;'></div>
            </div>
            <small style='color:#A0A0A0;'>Força bruta baseada em MA, FG, CPP e Psicológico</small>
        </div>
        """, unsafe_allow_html=True)

    with col_ec2:
        st.markdown(f"""
        <div class='card' style='text-align:center;'>
            <div class='card-header'>✈️ {nome_fora}</div>
            <div class='big-number'>{EC_B:.1f}</div>
            <div class='force-bar' style='width:100%; background:#2A2F3B; border-radius:8px; margin-top:12px;'>
                <div style='width:{EC_B}%; height:12px; background:linear-gradient(90deg, #4a90d9, #2a5fa0); border-radius:8px;'></div>
            </div>
            <small style='color:#A0A0A0;'>Força bruta baseada em MA, FG, CPP e Psicológico</small>
        </div>
        """, unsafe_allow_html=True)

    if EC_A > EC_B:
        st.markdown(f"<p style='text-align:center; color:#F0C040; font-size:1.2em;'>🔺 {nome_casa} tem um índice +{EC_A - EC_B:.1f} pontos superior</p>", unsafe_allow_html=True)
    elif EC_B > EC_A:
        st.markdown(f"<p style='text-align:center; color:#F0C040; font-size:1.2em;'>🔻 {nome_fora} tem um índice +{EC_B - EC_A:.1f} pontos superior</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"<p style='text-align:center; color:#F0C040; font-size:1.2em;'>⚖️ Equilíbrio absoluto (EC idênticos)</p>", unsafe_allow_html=True)

    # -------------------------------
    # ABAS DE ANÁLISE DETALHADA
    # -------------------------------
    st.markdown("---")
    st.markdown("### 🔍 Análises Complementares")
    tabs = st.tabs([
        "📊 Pilares & Força",
        "🎭 Estilo de Jogo",
        "⚔️ Comparação Setorial",
        "🗺️ Heatmap Tático",
        "🎲 Simulação de Cenários",
        "🔧 Ajuste MyEngramScore",
        "📋 Dados para os Mercados",
        "📝 Análise Descritiva Completa"
    ])

    # ----- ABA 1: Pilares (sem 1X2) -----
    with tabs[0]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>🔍 Pilares Individuais (componentes do MyEngramScore)</div>", unsafe_allow_html=True)
        pilares_nomes = ['Momento Atual', 'Força Geral', 'Confronto', 'Psicológico']
        valores_A = [ma_A, fg_A, cpp_A, psic_A]
        valores_B = [ma_B, fg_B, cpp_B, psic_B]
        df = pd.DataFrame({'Pilar': pilares_nomes*2, 'Time': [nome_casa]*4+[nome_fora]*4,
                           'Força': valores_A+valores_B})
        fig = px.bar(df, x='Pilar', y='Força', color='Time', barmode='group', text_auto='.1f',
                     color_discrete_map={nome_casa:'#F0C040', nome_fora:'#4a90d9'})
        fig.update_layout(template='plotly_dark', paper_bgcolor='#0A0E17')
        st.plotly_chart(fig, width='stretch')
        st.markdown("<small>Barras mais altas = melhor desempenho no pilar. A soma ponderada gera o MyEngramScore.</small>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'><div class='card-header'>🎯 Força Setorial (Ataque / Defesa / Meio)</div>", unsafe_allow_html=True)
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
                                template='plotly_dark', paper_bgcolor='#0A0E17')
        st.plotly_chart(fig_radar, width='stretch')
        st.markdown("<small>Quanto mais próximo da borda, melhor o setor.</small>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ----- ABA 2: Estilo de Jogo (PERFIS) -----
    with tabs[1]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>🎭 Perfis Táticos dos Times</div>", unsafe_allow_html=True)
        col_perf1, col_perf2 = st.columns(2)
        with col_perf1:
            st.markdown(f"**{nome_casa}**")
            st.markdown(f"**Perfil:** {perfil_A}")
            st.markdown(f"**Nota de Dominância (Estilo):** {estilo_A:.1f}/100")
        with col_perf2:
            st.markdown(f"**{nome_fora}**")
            st.markdown(f"**Perfil:** {perfil_B}")
            st.markdown(f"**Nota de Dominância (Estilo):** {estilo_B:.1f}/100")
        st.markdown("""
        **Significado dos Perfis:**
        - **Dominante** 🏆: Controla a posse de bola, finaliza bastante e pressiona no campo adversário.
        - **Pressão Alta** 🔥: Além de dominante, é extremamente agressivo sem a bola (muitas faltas, cartões, desarmes).
        - **Reativo / Contra‑ataque** ⚡: Pouca posse, mas transições rápidas e finalizações certeiras.
        - **Defensivo** 🛡️: Prioriza não sofrer gols, jogo físico, muitas faltas e pouca posse.
        - **Equilibrado** ⚖️: Não apresenta extremos; jogo balanceado.
        - **Posse Estéril** 🔄: Troca muitos passes, mas finaliza pouco (posse sem efetividade).
        - **Efetivo** 🎯: Pouca posse, mas alto aproveitamento das finalizações.
        """)
        st.markdown("</div>", unsafe_allow_html=True)

    # ----- ABA 3: Comparação Setorial -----
    with tabs[2]:
        st.markdown("<div class='card'><div class='card-header'>⚔️ Confronto por Estatística</div>", unsafe_allow_html=True)
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
            st.markdown(f"**{nome}**: {nome_casa} {vA:.1f} vs {nome_fora} {vB:.1f} → Vantagem: **{vant}**")
        st.markdown("</div>", unsafe_allow_html=True)

    # ----- ABA 4: Heatmap (campo duplo empilhado) -----
    with tabs[3]:
        st.markdown("<div class='card'><div class='card-header'>🗺️ Heatmap Tático (Força por Zona)</div>", unsafe_allow_html=True)
        fA = [def_A/100, mei_A/100, atq_A/100]  # Defesa, Meio, Ataque
        fB = [atq_B/100, mei_B/100, def_B/100]  # Ataque, Meio, Defesa (espelhado)
        fig_field = desenhar_campo_duplo(fA, fB, nome_casa, nome_fora)
        st.plotly_chart(fig_field, width='stretch')
        st.markdown("<small>Dourado = Casa, Azul = Visitante. Ataques se encontram no centro do campo.</small>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ----- ABA 5: Simulação de Cenários (5 cenários justificados) -----
    with tabs[4]:
        st.markdown("<div class='card'><div class='card-header'>🎲 Cinco Cenários Mais Prováveis</div>", unsafe_allow_html=True)
        cenarios = gerar_cenarios_justificados()
        for i, (titulo, prob, just) in enumerate(cenarios):
            st.markdown(f"**{i+1}. {titulo}** — {prob:.1%}")
            st.markdown(f"> {just}")
            st.markdown("---")
        st.markdown("</div>", unsafe_allow_html=True)

    # ----- ABA 6: Ajuste MyEngramScore (explicação do impacto nos lambdas) -----
    with tabs[5]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>🔧 Ajuste MyEngramScore nos Gols Esperados</div>", unsafe_allow_html=True)
        st.markdown(f"""
        **Fator de ajuste:** {fator_ajuste:+.2f}  
        (Diferença entre ECs / 100, multiplicado por 0.5)
        """)
        col_orig, col_adj = st.columns(2)
        with col_orig:
            st.markdown("**Lambdas Originais** (média simples de gols marcados/sofridos)")
            st.markdown(f"λ Casa: {lambda_casa_orig:.2f}")
            st.markdown(f"λ Fora: {lambda_fora_orig:.2f}")
        with col_adj:
            st.markdown("**Lambdas Ajustados** (modulados pelo MyEngramScore)")
            st.markdown(f"λ Casa: {lambda_casa_adj:.2f}")
            st.markdown(f"λ Fora: {lambda_fora_adj:.2f}")
        st.markdown("""
        **Como funciona:**  
        - Se o time da casa é muito superior (EC_A > EC_B), seu λ ofensivo **aumenta** e o λ do visitante **diminui**.  
        - Isso reduz artificialmente a chance de o time mais fraco marcar, refletindo a superioridade geral medida pelo MyEngramScore.  
        - As probabilidades de gols (Over, BTTS, Gol HT) exibidas nas abas seguintes **já incluem esse ajuste**.
        """)
        st.markdown("</div>", unsafe_allow_html=True)

    # ----- ABA 7: DADOS PARA OS MERCADOS (com lambdas ajustados) -----
    with tabs[6]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>📊 Probabilidades 1X2 (Modelo)</div>", unsafe_allow_html=True)
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            st.markdown(f"<div class='prob-box'><span style='color:#00cc66;'>Vitória {nome_casa}</span><br>"
                        f"<span class='prob-value'>{p_A:.1%}</span><br>{selo(p_A)}<br>"
                        f"<small>MyEngramScore: {EC_A:.1f} vs {EC_B:.1f}</small></div>", unsafe_allow_html=True)
        with col_p2:
            st.markdown(f"<div class='prob-box'><span style='color:#F0C040;'>Empate</span><br>"
                        f"<span class='prob-value'>{p_emp:.1%}</span><br>{selo(p_emp)}<br>"
                        f"<small>Equilíbrio: {1-diff_rel:.1%}</small></div>", unsafe_allow_html=True)
        with col_p3:
            st.markdown(f"<div class='prob-box'><span style='color:#4a90d9;'>Vitória {nome_fora}</span><br>"
                        f"<span class='prob-value'>{p_B:.1%}</span><br>{selo(p_B)}<br>"
                        f"<small>MyEngramScore: {EC_B:.1f} vs {EC_A:.1f}</small></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>⚽ Probabilidades de Gols (Modelo Ajustado pelo MyEngramScore)</div>", unsafe_allow_html=True)
        col_g1, col_g2, col_g3 = st.columns(3)
        col_g1.metric("Over 1.5", f"{over15_adj:.1%}")
        col_g2.metric("Over 2.5", f"{over25_adj:.1%}")
        col_g3.metric("Over 3.5", f"{over35_adj:.1%}")
        col_g4, col_g5 = st.columns(2)
        col_g4.metric("Ambos Marcam (BTTS)", f"{btts_adj:.1%}")
        col_g5.metric("BTTS Não", f"{1-btts_adj:.1%}")
        st.markdown(f"""
        **Como o ajuste do MyEngramScore influenciou:**  
        - λ original: Casa {lambda_casa_orig:.2f}, Fora {lambda_fora_orig:.2f}  
        - λ ajustado: Casa {lambda_casa_adj:.2f}, Fora {lambda_fora_adj:.2f}  
        Um time com EC muito maior reduz a expectativa de gol adversária.
        """)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>⏱️ Gol no 1º Tempo (Modelo Proprietário, Ajustado)</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='big-number'>{prob_gol_ht_adj:.1%}</div>", unsafe_allow_html=True)
        st.markdown(f"""
        **Explicação:** Probabilidade de gol no 1º tempo baseada em λ ajustado total={lambda_ht_adj:.2f},
        incluindo ajustes de estilo e momento.
        """)
        st.markdown("</div>", unsafe_allow_html=True)

    # ----- ABA 8: ANÁLISE DESCRITIVA COMPLETA -----
    with tabs[7]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>📝 Análise Descritiva do Confronto</div>", unsafe_allow_html=True)

        # 1. Análise dos pilares
        st.markdown("### 🔍 Pilares Individuais")
        st.markdown(f"**Momento Atual (MA):** {nome_casa} {ma_A:.1f} × {nome_fora} {ma_B:.1f}. "
                     f"{'O time da casa vive melhor fase.' if ma_A > ma_B else 'O visitante chega em melhor momento.' if ma_B > ma_A else 'Ambos estão em momentos semelhantes.'}")
        st.markdown(f"**Força Geral (FG):** {nome_casa} {fg_A:.1f} × {nome_fora} {fg_B:.1f}. "
                     f"{'A casa tem um elenco mais forte estatisticamente.' if fg_A > fg_B else 'O visitante possui maior força geral.' if fg_B > fg_A else 'Força equilibrada.'}")
        st.markdown(f"**Confronto por Prateleira (CPP):** {nome_casa} {cpp_A:.1f} × {nome_fora} {cpp_B:.1f}. "
                     f"{'Bom histórico contra times do mesmo nível.' if cpp_A > 60 else 'Histórico regular.' if cpp_A > 40 else 'Desempenho ruim contra pares.'}")
        st.markdown(f"**Psicológico:** {nome_casa} {psic_A:.1f} × {nome_fora} {psic_B:.1f}. "
                     f"{'Time da casa mais confiante.' if psic_A > psic_B else 'Visitante com melhor preparo mental.' if psic_B > psic_A else 'Fatores psicológicos empatados.'}")

        # 2. Comparação dos ECs
        st.markdown("### ⚡ MyEngramScore (Força Absoluta)")
        st.markdown(f"O índice final reflete a superioridade de um time sobre o outro: "
                     f"{nome_casa} **{EC_A:.1f}** vs {nome_fora} **{EC_B:.1f}**. "
                     f"{'A vantagem é clara para o mandante.' if EC_A > EC_B + 5 else 'O visitante é o favorito, mesmo fora de casa.' if EC_B > EC_A + 5 else 'O confronto é extremamente equilibrado.'}")

        # 3. Setores do campo
        st.markdown("### 🎯 Desempenho Setorial")
        st.markdown(f"- **Ataque:** {nome_casa} {atq_A:.1f} × {nome_fora} {atq_B:.1f} → "
                     f"{'O ataque da casa é mais eficiente.' if atq_A > atq_B else 'O visitante leva perigo.' if atq_B > atq_A else 'Ataques similares.'}")
        st.markdown(f"- **Defesa:** {nome_casa} {def_A:.1f} × {nome_fora} {def_B:.1f} → "
                     f"{'A defesa mandante é mais segura.' if def_A > def_B else 'O visitante defende melhor.' if def_B > def_A else 'Defesas de mesmo nível.'}")
        st.markdown(f"- **Meio-campo:** {nome_casa} {mei_A:.1f} × {nome_fora} {mei_B:.1f} → "
                     f"{'O controle do meio tende a ser do time da casa.' if mei_A > mei_B else 'O visitante pode dominar a posse.' if mei_B > mei_A else 'Disputa equilibrada no meio.'}")

        # 4. Estilos e perfil tático
        st.markdown("### 🎭 Estilos de Jogo")
        st.markdown(f"{nome_casa} é **{perfil_A}** (dominância {estilo_A:.1f}), enquanto {nome_fora} é **{perfil_B}** (dominância {estilo_B:.1f}). "
                     f"{'O estilo dominante da casa pode sufocar o visitante.' if 'Dominante' in perfil_A and 'Reativo' in perfil_B else 'O visitante reativo pode explorar contra-ataques.' if 'Reativo' in perfil_B else 'Ambos os estilos podem se neutralizar.'}")

        # 5. Cenário mais provável
        cenarios_5 = gerar_cenarios_justificados()
        st.markdown("### 🎲 Cenário mais Provável")
        st.markdown(f"**{cenarios_5[0][0]}** ({cenarios_5[0][1]:.1%}): {cenarios_5[0][2]}")

        # 6. Conclusão
        st.markdown("### 📌 Conclusão")
        if EC_A > EC_B + 5:
            st.markdown(f"Diante de todos os pilares analisados, **{nome_casa}** é amplamente favorito para vencer a partida. Seu MyEngramScore superior reflete melhor momento, força geral e psicológico. A expectativa de gols é alta, com domínio territorial.")
        elif EC_B > EC_A + 5:
            st.markdown(f"Apesar de jogar fora de casa, **{nome_fora}** apresenta um MyEngramScore significativamente maior, indicando que deve impor seu jogo e vencer. O time da casa precisará de uma atuação defensiva impecável para surpreender.")
        else:
            st.markdown(f"O confronto é **extremamente equilibrado**, com forças muito próximas. O empate é um resultado plausível, e os detalhes decidirão. Ambos os times devem marcar, e a partida promete ser disputada até o fim.")

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='quote'>\"A análise separa a emoção da decisão.\"</div>", unsafe_allow_html=True)
