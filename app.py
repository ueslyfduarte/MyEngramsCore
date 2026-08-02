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
    }
    .prob-value { font-size: 2.5em; font-weight: bold; color: #F0C040; }
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
if st.button("🔍 GERAR MyEngramScore", type="primary", use_container_width=True):
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

    # Estilo (nota de dominância)
    estilo_A = calcular_estilo(dados_A, medias_liga, n_casa)
    estilo_B = calcular_estilo(dados_B, medias_liga, n_fora)

    # Perfil tático
    perfil_A = obter_perfil_time(dados_A, medias_liga)
    perfil_B = obter_perfil_time(dados_B, medias_liga)

    # Pressão
    dif_pts = (pos_casa - pos_fora) * 3  # simplificação
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
    # bônus casa
    EC_A += 2.0
    EC_A = max(0, min(100, EC_A))
    EC_B = max(0, min(100, EC_B))

    # Probabilidades 1X2
    total = EC_A + EC_B
    diff_rel = abs(EC_A - EC_B)/total if total>0 else 0
    p_emp = max(0.18, 0.40 - diff_rel*0.3)
    p_A = (1 - p_emp) * (EC_A/total) if total>0 else 0.33
    p_B = 1 - p_A - p_emp

    # -------------------------------
    # EXIBIÇÃO PRINCIPAL: MyEngramScore
    # -------------------------------
    st.markdown("---")
    st.markdown("<h2 style='text-align:center;'>⚡ MyEngramScore</h2>", unsafe_allow_html=True)
    col_ec1, col_ec2, col_ec3 = st.columns(3)
    with col_ec1:
        st.markdown(f"<div class='card'><div class='card-header'>🏠 {nome_casa}</div>"
                    f"<div class='big-number'>{EC_A:.1f}</div><div style='text-align:center;'>Índice Final</div></div>",
                    unsafe_allow_html=True)
    with col_ec2:
        st.markdown(f"<div class='card'><div class='card-header'>🤝 Empate</div>"
                    f"<div class='big-number'>{p_emp:.1%}</div><div style='text-align:center;'>Probabilidade</div></div>",
                    unsafe_allow_html=True)
    with col_ec3:
        st.markdown(f"<div class='card'><div class='card-header'>✈️ {nome_fora}</div>"
                    f"<div class='big-number'>{EC_B:.1f}</div><div style='text-align:center;'>Índice Final</div></div>",
                    unsafe_allow_html=True)

    # Probabilidades 1X2 detalhadas
    st.markdown("### 📊 Probabilidades 1X2")
    col_p1, col_p2, col_p3 = st.columns(3)
    col_p1.markdown(f"<div class='prob-box'><span style='color:#00cc66;'>Vitória {nome_casa}</span><br>"
                    f"<span class='prob-value'>{p_A:.1%}</span></div>", unsafe_allow_html=True)
    col_p2.markdown(f"<div class='prob-box'><span style='color:#F0C040;'>Empate</span><br>"
                    f"<span class='prob-value'>{p_emp:.1%}</span></div>", unsafe_allow_html=True)
    col_p3.markdown(f"<div class='prob-box'><span style='color:#4a90d9;'>Vitória {nome_fora}</span><br>"
                    f"<span class='prob-value'>{p_B:.1%}</span></div>", unsafe_allow_html=True)

    # -------------------------------
    # ABAS DE ANÁLISE DETALHADA
    # -------------------------------
    tabs = st.tabs([
        "📈 Força & Pilares",
        "⚔️ Comparação Setorial",
        "🧠 Análise Tática (Heatmap)",
        "🎲 Simulação de Cenários",
        "💰 Ajuste de Mercados (Edge)"
    ])

    # ----- ABA 1: Força & Pilares -----
    with tabs[0]:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'>🔍 Pilares Individuais</div>", unsafe_allow_html=True)
        pilares_nomes = ['Momento Atual', 'Força Geral', 'Confronto', 'Psicológico']
        valores_A = [ma_A, fg_A, cpp_A, psic_A]
        valores_B = [ma_B, fg_B, cpp_B, psic_B]
        df = pd.DataFrame({'Pilar': pilares_nomes*2, 'Time': [nome_casa]*4+[nome_fora]*4,
                           'Força': valores_A+valores_B})
        fig = px.bar(df, x='Pilar', y='Força', color='Time', barmode='group', text_auto='.1f',
                     color_discrete_map={nome_casa:'#F0C040', nome_fora:'#4a90d9'})
        fig.update_layout(template='plotly_dark', paper_bgcolor='#0A0E17')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Radar
        st.markdown("<div class='card'><div class='card-header'>🎯 Força Setorial (Radar)</div>", unsafe_allow_html=True)
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
        st.plotly_chart(fig_radar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ----- ABA 2: Comparação Setorial -----
    with tabs[1]:
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

    # ----- ABA 3: Heatmap de Campo -----
    with tabs[2]:
        st.markdown("<div class='card'><div class='card-header'>🗺️ Heatmap Tático (Força por Zona)</div>", unsafe_allow_html=True)
        # Dividir o campo em 3 zonas verticais: defesa, meio, ataque
        zonas = ['Defesa', 'Meio', 'Ataque']
        # Normalizar forças para 0-1 (usando os radares normalizados)
        fA = [def_A/100, mei_A/100, atq_A/100]
        fB = [def_B/100, mei_B/100, atq_B/100]
        # Criar gráfico de campo com retângulos coloridos
        fig_field = go.Figure()
        # Adicionar campo de futebol básico (linhas)
        fig_field.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100, line=dict(color="#2A2F3B"), fillcolor="#0A0E17")
        fig_field.add_shape(type="rect", x0=0, y0=30, x1=100, y1=70, line=dict(color="#F0C040", width=2), fillcolor="rgba(0,0,0,0)")
        # Adicionar zonas (3 faixas horizontais: defesa embaixo, meio, ataque em cima)
        for i, (zona, fa, fb) in enumerate(zip(zonas, fA, fB)):
            y0 = i * 33.33
            y1 = (i+1) * 33.33
            # Time A (esquerda? vamos fazer lado a lado em cada zona)
            # Esquerda: time A, Direita: time B
            fig_field.add_shape(type="rect", x0=0, y0=y0, x1=50, y1=y1, fillcolor=f"rgba(240,192,64,{fa})", line_width=0)
            fig_field.add_shape(type="rect", x0=50, y0=y0, x1=100, y1=y1, fillcolor=f"rgba(74,144,217,{fb})", line_width=0)
            fig_field.add_annotation(x=25, y=(y0+y1)/2, text=f"{nome_casa}<br>{fa*100:.0f}%", showarrow=False, font=dict(color="white"))
            fig_field.add_annotation(x=75, y=(y0+y1)/2, text=f"{nome_fora}<br>{fb*100:.0f}%", showarrow=False, font=dict(color="white"))
        fig_field.update_xaxes(visible=False, range=[0,100])
        fig_field.update_yaxes(visible=False, range=[0,100])
        fig_field.update_layout(template='plotly_dark', paper_bgcolor='#0A0E17', height=400)
        st.plotly_chart(fig_field, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ----- ABA 4: Simulação de Cenários -----
    with tabs[3]:
        st.markdown("<div class='card'><div class='card-header'>🎲 Cenários Prováveis (Poisson)</div>", unsafe_allow_html=True)
        # Estimar lambda para cada time usando gols marcados/sofridos
        lambda_casa = (gm_casa + gs_fora) / 2
        lambda_fora = (gm_fora + gs_casa) / 2
        # Gerar probabilidades de placares (0-0 a 5-5)
        results = []
        for i in range(6):
            for j in range(6):
                prob = math.exp(-lambda_casa)*(lambda_casa**i)/math.factorial(i) * \
                       math.exp(-lambda_fora)*(lambda_fora**j)/math.factorial(j)
                results.append((i, j, prob))
        results.sort(key=lambda x: x[2], reverse=True)
        top5 = results[:5]
        st.markdown("**Os 5 placares mais prováveis:**")
        for i, (gA, gB, prob) in enumerate(top5):
            st.markdown(f"{i+1}. {nome_casa} {gA} x {gB} {nome_fora} — {prob*100:.1f}%")
        # Cenários agregados
        # 1X2
        vitoria_casa = sum(p for gA,gB,p in results if gA>gB)
        empate = sum(p for gA,gB,p in results if gA==gB)
        vitoria_fora = sum(p for gA,gB,p in results if gA<gB)
        # Over/Under
        over15 = sum(p for gA,gB,p in results if gA+gB > 1.5)
        over25 = sum(p for gA,gB,p in results if gA+gB > 2.5)
        over35 = sum(p for gA,gB,p in results if gA+gB > 3.5)
        btts = sum(p for gA,gB,p in results if gA>0 and gB>0)
        st.markdown("---")
        st.markdown("**Probabilidades Agregadas:**")
        st.markdown(f"Vitória {nome_casa}: {vitoria_casa*100:.1f}% | Empate: {empate*100:.1f}% | Vitória {nome_fora}: {vitoria_fora*100:.1f}%")
        st.markdown(f"Over 1.5: {over15*100:.1f}% | Over 2.5: {over25*100:.1f}% | Over 3.5: {over35*100:.1f}%")
        st.markdown(f"Ambos Marcam (BTTS): {btts*100:.1f}%")
        st.markdown("</div>", unsafe_allow_html=True)

    # ----- ABA 5: Ajuste de Mercados (Edge) -----
    with tabs[4]:
        st.markdown("<div class='card'><div class='card-header'>💰 Comparação Modelo vs Mercado</div>", unsafe_allow_html=True)
        # Calcular odds justas do modelo
        odds_modelo = {
            f"Vitória {nome_casa}": 1/p_A if p_A>0 else 999,
            "Empate": 1/p_emp if p_emp>0 else 999,
            f"Vitória {nome_fora}": 1/p_B if p_B>0 else 999,
            "Over 2.5 Gols": 1/over25 if over25>0 else 999,
            "BTTS Sim": 1/btts if btts>0 else 999,
        }
        # Odds reais inseridas (pegar as odds reais que estão nos inputs)
        odds_reais = {
            f"Vitória {nome_casa}": odd_casa,
            "Empate": odd_empate,
            f"Vitória {nome_fora}": odd_fora,
            # Over/BTTS não temos odds inseridas, podemos pedir ou pular. Vou pular e mostrar só 1X2.
        }
        linhas = []
        for mercado, odd_mod in odds_modelo.items():
            if mercado in odds_reais:
                odd_real = odds_reais[mercado]
                edge = (1/odd_real) - (1/odd_mod)  # edge positivo = valor a favor
                linhas.append((mercado, f"{odd_mod:.2f}", f"{odd_real:.2f}", f"{edge*100:+.1f}%", "💚 Valor" if edge>0 else "🔴 Sem Valor"))
        df_edge = pd.DataFrame(linhas, columns=["Mercado", "Odd Modelo", "Odd Real", "Edge", "Indicação"])
        st.dataframe(df_edge, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='quote'>\"A análise separa a emoção da decisão.\"</div>", unsafe_allow_html=True)
