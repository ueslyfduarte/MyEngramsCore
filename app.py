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
import os

# Seus módulos
from src.metricas.ma import calcular_ma, calcular_ma_simples
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
# CSS PREMIUM
# ------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(135deg, #06080D 0%, #0B0F17 50%, #0D111A 100%); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0A0D14 0%, #0F1219 100%); border-right: 1px solid #1E2330; }
    [data-testid="stSidebar"] h2 { color: #F0C040 !important; font-weight:800; letter-spacing:2px; text-transform:uppercase; font-size:14px; border-bottom:2px solid #F0C040; padding-bottom:8px; margin-bottom:16px; }
    .card-premium { background: linear-gradient(145deg, rgba(20,24,35,0.9) 0%, rgba(16,20,30,0.95) 100%); border:1px solid #252B38; border-radius:14px; padding:20px 16px; margin:8px 0; backdrop-filter:blur(10px); box-shadow:0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.03); position:relative; overflow:hidden; }
    .card-premium::before { content:''; position:absolute; top:0; left:0; right:0; height:1px; background:linear-gradient(90deg, transparent, rgba(240,192,64,0.3), transparent); }
    .card-premium:hover { border-color:#F0C040; box-shadow:0 12px 40px rgba(0,0,0,0.6), 0 0 20px rgba(240,192,64,0.1); }
    .card-header-premium { font-size:14px; font-weight:700; text-transform:uppercase; letter-spacing:2px; color:#B0B8C0; margin-bottom:14px; display:flex; align-items:center; gap:8px; }
    .metric-premium { font-size:52px; font-weight:900; text-align:center; background:linear-gradient(180deg, #F0C040 0%, #D4A017 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; letter-spacing:-2px; line-height:1; margin:6px 0; }
    .metric-premium-blue { font-size:52px; font-weight:900; text-align:center; background:linear-gradient(180deg, #4A90D9 0%, #2A5FA0 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; letter-spacing:-2px; line-height:1; margin:6px 0; }
    .high-confidence { background:linear-gradient(180deg, #F0C040 0%, #D4A017 100%) !important; -webkit-background-clip:text !important; -webkit-text-fill-color:transparent !important; background-clip:text !important; font-weight:900; }
    .metric-label-premium { font-size:13px; text-transform:uppercase; letter-spacing:3px; color:#B0B8C0; text-align:center; font-weight:600; }
    .bar-premium { height:6px; border-radius:3px; background:rgba(255,255,255,0.05); margin:10px 0; overflow:hidden; }
    .bar-fill-gold { height:100%; border-radius:3px; background:linear-gradient(90deg, #F0C040, #D4A017); }
    .bar-fill-blue { height:100%; border-radius:3px; background:linear-gradient(90deg, #4A90D9, #2A5FA0); }
    .selo-dourado { border:2px solid #F0C040; border-radius:20px; padding:5px 14px; background:linear-gradient(135deg, rgba(240,192,64,0.15) 0%, rgba(240,192,64,0.05) 100%); color:#F0C040; font-weight:700; font-size:12px; display:inline-block; letter-spacing:1px; }
    .selo-verde { border:2px solid #00E676; border-radius:20px; padding:5px 14px; background:linear-gradient(135deg, rgba(0,230,118,0.15) 0%, rgba(0,230,118,0.05) 100%); color:#00E676; font-weight:700; font-size:12px; display:inline-block; letter-spacing:1px; }
    .selo-amarelo { border:2px solid #FFB300; border-radius:20px; padding:5px 14px; background:linear-gradient(135deg, rgba(255,179,0,0.15) 0%, rgba(255,179,0,0.05) 100%); color:#FFB300; font-weight:700; font-size:12px; display:inline-block; letter-spacing:1px; }
    .stButton > button { background:linear-gradient(135deg, #F0C040 0%, #D4A017 100%); color:#0A0D14; font-weight:800; font-size:15px; letter-spacing:2px; text-transform:uppercase; border:none; border-radius:12px; padding:14px 40px; box-shadow:0 8px 24px rgba(240,192,64,0.3); transition:all 0.3s ease; }
    .stButton > button:hover { transform:translateY(-2px); box-shadow:0 12px 32px rgba(240,192,64,0.5); }
    .stTabs [data-baseweb="tab-list"] { gap:4px; background:rgba(255,255,255,0.02); border-radius:12px; padding:4px; }
    .stTabs [data-baseweb="tab"] { border-radius:8px; padding:10px 18px; font-weight:600; font-size:14px; color:#B0B8C0; transition:all 0.2s; }
    .stTabs [aria-selected="true"] { background:linear-gradient(135deg, rgba(240,192,64,0.15) 0%, rgba(240,192,64,0.05) 100%) !important; color:#F0C040 !important; border:1px solid rgba(240,192,64,0.3); }
    .prob-box { background:linear-gradient(145deg, rgba(20,24,35,0.8) 0%, rgba(16,20,30,0.9) 100%); border-radius:14px; padding:20px 12px; text-align:center; border:1px solid #252B38; }
    .info-card { background:rgba(240,192,64,0.03); border:1px solid rgba(240,192,64,0.1); border-radius:12px; padding:14px; margin:6px 0; font-size:15px; color:#E0E0E0; line-height:1.6; }
    .divider { height:1px; background:linear-gradient(90deg, transparent, #252B38, transparent); margin:20px 0; }
    .stNumberInput input, .stTextInput input { background:#111620 !important; border:1px solid #252B38 !important; border-radius:8px !important; color:#E0E0E0 !important; }
    .stSelectbox > div > div { background:#111620 !important; border:1px solid #252B38 !important; border-radius:8px !important; }
    h2, h3 { font-weight:800 !important; letter-spacing:-0.5px; color:#F0C040 !important; }
    .stTextArea textarea { background:#111620 !important; border:1px solid #252B38 !important; border-radius:8px !important; color:#E0E0E0 !important; font-size:13px !important; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
st.markdown("""
<div style="text-align:center; padding: 20px 0 30px 0;">
    <div style="font-size:13px; text-transform:uppercase; letter-spacing:4px; color:#B0B8C0; margin-bottom:8px;">Sistema de Análise Esportiva</div>
    <h1 style="font-size:44px; font-weight:900; margin:0; letter-spacing:-1px;">
        <span style="background:linear-gradient(180deg, #F0C040 0%, #D4A017 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">ENGRAM</span>
        <span style="color:#E0E0E0; font-weight:300;">SCORE</span>
    </h1>
    <div style="font-size:13px; color:#B0B8C0; letter-spacing:3px; margin-top:4px;">ÍNDICE DE FORÇA ABSOLUTA — ONDE A MEMÓRIA CONSOLIDA O PADRÃO</div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# BARRA LATERAL - JOGOS PENDENTES + ANÁLISES
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📋 Jogos Pendentes")
    st.markdown("*Adicione jogos para análise futura.*")

    arquivo_pendentes = "dados/jogos_pendentes.csv"
    if os.path.exists(arquivo_pendentes):
        df_pendentes = pd.read_csv(arquivo_pendentes)
    else:
        df_pendentes = pd.DataFrame(columns=["casa", "fora", "liga"])

    col_add1, col_add2 = st.columns(2)
    with col_add1:
        novo_casa = st.text_input("Casa", key="pend_casa", placeholder="Palmeiras")
    with col_add2:
        novo_fora = st.text_input("Fora", key="pend_fora", placeholder="Vasco")

    nova_liga = st.selectbox("Liga", [
        "brasileirao_serie_a", "brasileirao_serie_b", "premier_league",
        "la_liga", "bundesliga", "serie_a", "ligue_1", "mls", "liga_mx",
        "primera_division_argentina"
    ], key="pend_liga")

    if st.button("➕ Adicionar"):
        if novo_casa and novo_fora:
            novo = pd.DataFrame({"casa": [novo_casa], "fora": [novo_fora], "liga": [nova_liga]})
            df_pendentes = pd.concat([df_pendentes, novo], ignore_index=True)
            df_pendentes.to_csv(arquivo_pendentes, index=False)
            st.success(f"{novo_casa} x {novo_fora} adicionado!")
            st.rerun()

    if not df_pendentes.empty:
        st.markdown("---")
        for idx, row in df_pendentes.iterrows():
            col_j, col_r = st.columns([4, 1])
            with col_j:
                st.markdown(f"• {row['casa']} x {row['fora']}")
            with col_r:
                if st.button("🗑️", key=f"rem_{idx}"):
                    df_pendentes = df_pendentes.drop(idx).reset_index(drop=True)
                    df_pendentes.to_csv(arquivo_pendentes, index=False)
                    st.rerun()

    st.markdown("---")
    st.markdown("## 📊 Análises do Dia")
    arquivo_analises = "dados/analises_prontas.csv"
    if os.path.exists(arquivo_analises):
        df_analises = pd.read_csv(arquivo_analises)
        st.success(f"✅ {len(df_analises)} análises disponíveis")
        for idx, row in df_analises.iterrows():
            if st.button(f"📊 {row['casa']} x {row['fora']}", key=f"ana_{idx}"):
                st.session_state["jogo_selecionado"] = {
                    "casa": row["casa"], "fora": row["fora"],
                    "EC_A": row["EC_A"], "EC_B": row["EC_B"],
                    "p_A": row["p_A"], "p_emp": row["p_emp"], "p_B": row["p_B"],
                    "resultado_previsto": row["resultado_previsto"],
                }
                st.rerun()
    else:
        st.info("Nenhuma análise pronta ainda.")
        # ------------------------------------------------------------
# ÁREA PRINCIPAL
# ------------------------------------------------------------
if "jogo_selecionado" in st.session_state:
    jogo = st.session_state["jogo_selecionado"]
    st.markdown(f"""
    <div style="text-align:center; margin:20px 0;">
        <h2>{jogo['casa']} vs {jogo['fora']}</h2>
        <div style="font-size:18px; color:#F0C040;">{jogo.get('resultado_previsto', '')}</div>
        <div style="font-size:14px; color:#B0B8C0;">EC Casa: {jogo['EC_A']} | EC Fora: {jogo['EC_B']}</div>
    </div>
    """, unsafe_allow_html=True)
    st.info("📊 A análise completa com gráficos e heatmap será carregada na próxima atualização do sistema.")

else:
    # ============= MODO DE ENTRADA =============
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("""<div style="text-align:center; margin-bottom:20px;"><span style="font-size:13px; text-transform:uppercase; letter-spacing:3px; color:#B0B8C0;">Dados do Confronto</span></div>""", unsafe_allow_html=True)

    modo_entrada = st.radio("Modo de entrada:", ["📋 Colar do FBref", "✏️ Manual"], horizontal=True)

    # ============= MODO FBREF =============
    if modo_entrada == "📋 Colar do FBref":
        st.markdown("### 📋 Cole a tabela do FBref")
        st.markdown("*Acesse [fbref.com](https://fbref.com), escolha a liga, selecione a tabela inteira (Ctrl+A) e cole abaixo.*")

        texto_colado = st.text_area(
            "Cole aqui a tabela do FBref",
            height=200,
            placeholder="Squad\tMP\tGls\tAst\t...\nPalmeiras\t10\t21\t15\t...\nVasco\t10\t12\t8\t...",
            help="Selecione a tabela 'Standard Stats' inteira no FBref e cole aqui."
        )

        if texto_colado:
            try:
                linhas = texto_colado.strip().split('\n')
                cabecalho = linhas[0].split('\t')
                dados_times = {}
                for linha in linhas[1:]:
                    partes = linha.split('\t')
                    if len(partes) >= 3:
                        nome_time = partes[0].strip()
                        if nome_time and nome_time not in ['Squad', '']:
                            dados_times[nome_time] = partes

                if dados_times:
                    st.success(f"✅ {len(dados_times)} times encontrados!")

                    col_t1, col_t2 = st.columns(2)
                    with col_t1:
                        nome_casa = st.selectbox("🏠 Time da Casa", list(dados_times.keys()), key="fb_casa")
                    with col_t2:
                        nome_fora = st.selectbox("✈️ Time Visitante", list(dados_times.keys()), key="fb_fora")

                    # Função para extrair valores
                    def extrair_valor(partes, cabecalho, padroes):
                        for padrao in padroes:
                            for i, col in enumerate(cabecalho):
                                if padrao.lower() in col.lower() and i < len(partes):
                                    try:
                                        return float(partes[i])
                                    except:
                                        continue
                        return 0.0

                    partes_casa = dados_times[nome_casa]
                    partes_fora = dados_times[nome_fora]

                    gm_casa = extrair_valor(partes_casa, cabecalho, ['Gls', 'Goals'])
                    fa_casa = extrair_valor(partes_casa, cabecalho, ['SoT'])
                    eca_casa = extrair_valor(partes_casa, cabecalho, ['CK'])
                    posse_casa = extrair_valor(partes_casa, cabecalho, ['Poss'])
                    gs_casa = extrair_valor(partes_casa, cabecalho, ['GA', 'Goals Against'])
                    fas_casa = extrair_valor(partes_casa, cabecalho, ['SoTA'])
                    des_casa = extrair_valor(partes_casa, cabecalho, ['Tkl'])
                    fc_casa = extrair_valor(partes_casa, cabecalho, ['Fls'])
                    ca_casa = extrair_valor(partes_casa, cabecalho, ['CrdY'])

                    gm_fora = extrair_valor(partes_fora, cabecalho, ['Gls', 'Goals'])
                    fa_fora = extrair_valor(partes_fora, cabecalho, ['SoT'])
                    eca_fora = extrair_valor(partes_fora, cabecalho, ['CK'])
                    posse_fora = extrair_valor(partes_fora, cabecalho, ['Poss'])
                    gs_fora = extrair_valor(partes_fora, cabecalho, ['GA', 'Goals Against'])
                    fas_fora = extrair_valor(partes_fora, cabecalho, ['SoTA'])
                    des_fora = extrair_valor(partes_fora, cabecalho, ['Tkl'])
                    fc_fora = extrair_valor(partes_fora, cabecalho, ['Fls'])
                    ca_fora = extrair_valor(partes_fora, cabecalho, ['CrdY'])

                    # Calcular médias da liga
                    def media_liga(padroes, cabecalho, dados):
                        valores = []
                        for nome, partes in dados.items():
                            val = extrair_valor(partes, cabecalho, padroes)
                            if val > 0:
                                valores.append(val)
                        return sum(valores) / len(valores) if valores else 0.0

                    medias_liga = {
                        'GM': media_liga(['Gls', 'Goals'], cabecalho, dados_times),
                        'FA': media_liga(['SoT'], cabecalho, dados_times),
                        'ECa': media_liga(['CK'], cabecalho, dados_times),
                        'Posse': media_liga(['Poss'], cabecalho, dados_times),
                        'GS': media_liga(['GA', 'Goals Against'], cabecalho, dados_times),
                        'FAS': media_liga(['SoTA'], cabecalho, dados_times),
                        'ECc': media_liga(['CK'], cabecalho, dados_times),
                        'Des': media_liga(['Tkl'], cabecalho, dados_times),
                        'FC': media_liga(['Fls'], cabecalho, dados_times),
                        'CA': media_liga(['CrdY'], cabecalho, dados_times),
                    }

                    st.markdown("### 📊 Médias da Liga (auto-calculadas)")
                    col_m1, col_m2, col_m3 = st.columns(3)
                    with col_m1:
                        st.metric("Gols/jogo", f"{medias_liga['GM']:.2f}")
                        st.metric("Posse", f"{medias_liga['Posse']:.1f}%")
                    with col_m2:
                        st.metric("Finalizações alvo/j", f"{medias_liga['FA']:.2f}")
                        st.metric("Desarmes/j", f"{medias_liga['Des']:.1f}")
                    with col_m3:
                        st.metric("Escanteios/j", f"{medias_liga['ECa']:.2f}")
                        st.metric("Faltas/j", f"{medias_liga['FC']:.1f}")

                    # Campos manuais restantes
                    st.markdown("### 📝 Dados Complementares")
                    st.markdown("*Preencha os resultados recentes e dados de confronto.*")
                    col_extra1, col_extra2 = st.columns(2)
                    with col_extra1:
                        res_casa = st.text_input("Últ. 5 resultados Casa (V/E/D)", "VVEDV", key="fb_res_casa").upper()
                        cons_casa = st.text_input("Últ. 10 resultados Casa (V/E/D)", "VVEDVVEDVV", key="fb_cons_casa").upper()
                        moral_casa = st.slider("Moral Casa (pts 3j)", 0, 9, 6, key="fb_moral_casa")
                        pos_casa = st.number_input("Posição Casa", 1, 24, 2, key="fb_pos_casa")
                        prat_casa = st.selectbox("Prateleira Adv. Casa", ["Elite","Alta","Média","Baixa","Crítica"], key="fb_prat_casa")
                        pts_cpp_casa = st.number_input("Pontos CPP Casa", 0, 30, 6, key="fb_cpp_casa")
                        jogos_cpp_casa = st.number_input("Jogos CPP Casa", 0, 10, 3, key="fb_jcpp_casa")
                    with col_extra2:
                        res_fora = st.text_input("Últ. 5 resultados Fora (V/E/D)", "DDVVE", key="fb_res_fora").upper()
                        cons_fora = st.text_input("Últ. 10 resultados Fora (V/E/D)", "DDVVEDDVV", key="fb_cons_fora").upper()
                        moral_fora = st.slider("Moral Fora (pts 3j)", 0, 9, 3, key="fb_moral_fora")
                        pos_fora = st.number_input("Posição Fora", 1, 24, 16, key="fb_pos_fora")
                        prat_fora = st.selectbox("Prateleira Adv. Fora", ["Elite","Alta","Média","Baixa","Crítica"], key="fb_prat_fora")
                        pts_cpp_fora = st.number_input("Pontos CPP Fora", 0, 30, 4, key="fb_cpp_fora")
                        jogos_cpp_fora = st.number_input("Jogos CPP Fora", 0, 10, 2, key="fb_jcpp_fora")

                    n_casa = n_fora = 10
                    dados_A = {'GM': gm_casa, 'FA': fa_casa, 'ECa': eca_casa, 'Posse': posse_casa, 'GS': gs_casa, 'FAS': fas_casa, 'ECc': 0, 'Des': des_casa, 'FC': fc_casa, 'CA': ca_casa}
                    dados_B = {'GM': gm_fora, 'FA': fa_fora, 'ECa': eca_fora, 'Posse': posse_fora, 'GS': gs_fora, 'FAS': fas_fora, 'ECc': 0, 'Des': des_fora, 'FC': fc_fora, 'CA': ca_fora}

            except Exception as e:
                st.error(f"❌ Erro ao processar tabela. Verifique se o formato está correto (copie do FBref).")

    # ============= MODO MANUAL =============
    else:
        colA, colB = st.columns(2)

        with colA:
            with st.container():
                st.markdown('<div class="card-premium"><div class="card-header-premium">🏠 TIME DA CASA</div>', unsafe_allow_html=True)
                nome_casa = st.text_input("Nome", "Time A", key="casa", label_visibility="collapsed")
                n_casa = st.number_input("Jogos", 1, 38, 10, key="nj_casa")
                gm_casa = st.number_input("Gols/jogo", 0.0, 5.0, 2.0, 0.1, key="gm_casa")
                fa_casa = st.number_input("Finalizações alvo/j", 0.0, 10.0, 4.5, 0.1, key="fa_casa")
                eca_casa = st.number_input("Escanteios a favor/j", 0.0, 20.0, 5.5, 0.1, key="eca_casa")
                posse_casa = st.slider("Posse (%)", 0, 100, 55, key="posse_casa")
                gs_casa = st.number_input("Gols sofridos/j", 0.0, 5.0, 0.8, 0.1, key="gs_casa")
                fas_casa = st.number_input("Finalizações alvo sofridas/j", 0.0, 10.0, 3.0, 0.1, key="fas_casa")
                des_casa = st.number_input("Desarmes/j", 0.0, 50.0, 16.0, 0.1, key="des_casa")
                fc_casa = st.number_input("Faltas/j", 0.0, 30.0, 13.0, 0.1, key="fc_casa")
                ca_casa = st.number_input("Cartões amarelos/j", 0.0, 10.0, 2.2, 0.1, key="ca_casa")
                res_casa = st.text_input("Últ. 5 resultados (V/E/D)", "VVEDV", key="res_casa").upper()
                cons_casa = st.text_input("Últ. 10 resultados (V/E/D)", "VVEDVVEDVV", key="cons_casa").upper()
                moral_casa = st.slider("Moral (pts 3j)", 0, 9, 6, key="moral_casa")
                pts_cpp_casa = st.number_input("Pontos contra prateleira", 0, 30, 6, key="pcpp_casa")
                jogos_cpp_casa = st.number_input("Jogos contra prateleira", 0, 10, 3, key="jcpp_casa")
                prat_casa = st.selectbox("Prateleira do Adversário", ["Elite","Alta","Média","Baixa","Crítica"], key="prat_casa")
                pos_casa = st.number_input("Posição na tabela", 1, 24, 2, key="pos_casa")
                st.markdown('</div>', unsafe_allow_html=True)

        with colB:
            with st.container():
                st.markdown('<div class="card-premium"><div class="card-header-premium">✈️ TIME VISITANTE</div>', unsafe_allow_html=True)
                nome_fora = st.text_input("Nome", "Time B", key="fora", label_visibility="collapsed")
                n_fora = st.number_input("Jogos", 1, 38, 10, key="nj_fora")
                gm_fora = st.number_input("Gols/jogo", 0.0, 5.0, 1.2, 0.1, key="gm_fora")
                fa_fora = st.number_input("Finalizações alvo/j", 0.0, 10.0, 3.2, 0.1, key="fa_fora")
                eca_fora = st.number_input("Escanteios a favor/j", 0.0, 20.0, 4.5, 0.1, key="eca_fora")
                posse_fora = st.slider("Posse (%)", 0, 100, 48, key="posse_fora")
                gs_fora = st.number_input("Gols sofridos/j", 0.0, 5.0, 1.5, 0.1, key="gs_fora")
                fas_fora = st.number_input("Finalizações alvo sofridas/j", 0.0, 10.0, 3.8, 0.1, key="fas_fora")
                des_fora = st.number_input("Desarmes/j", 0.0, 50.0, 14.0, 0.1, key="des_fora")
                fc_fora = st.number_input("Faltas/j", 0.0, 30.0, 11.0, 0.1, key="fc_fora")
                ca_fora = st.number_input("Cartões amarelos/j", 0.0, 10.0, 1.8, 0.1, key="ca_fora")
                res_fora = st.text_input("Últ. 5 resultados (V/E/D)", "DDVVE", key="res_fora").upper()
                cons_fora = st.text_input("Últ. 10 resultados (V/E/D)", "DDVVEDDVV", key="cons_fora").upper()
                moral_fora = st.slider("Moral (pts 3j)", 0, 9, 3, key="moral_fora")
                pts_cpp_fora = st.number_input("Pontos contra prateleira", 0, 30, 4, key="pcpp_fora")
                jogos_cpp_fora = st.number_input("Jogos contra prateleira", 0, 10, 2, key="jcpp_fora")
                prat_fora = st.selectbox("Prateleira do Adversário", ["Elite","Alta","Média","Baixa","Crítica"], key="prat_fora")
                pos_fora = st.number_input("Posição na tabela", 1, 24, 16, key="pos_fora")
                st.markdown('</div>', unsafe_allow_html=True)

        # Médias da liga (manual)
        with st.expander("⚙️ Médias da Liga (Manual)", expanded=False):
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

        dados_A = {'GM': gm_casa, 'FA': fa_casa, 'ECa': eca_casa, 'Posse': posse_casa, 'GS': gs_casa, 'FAS': fas_casa, 'ECc': 0, 'Des': des_casa, 'FC': fc_casa, 'CA': ca_casa}
        dados_B = {'GM': gm_fora, 'FA': fa_fora, 'ECa': eca_fora, 'Posse': posse_fora, 'GS': gs_fora, 'FAS': fas_fora, 'ECc': 0, 'Des': des_fora, 'FC': fc_fora, 'CA': ca_fora}

    # ============= ODDS (COMUM AOS DOIS MODOS) =============
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("### 💰 Odds de Mercado")
    st.markdown("**1X2**")
    col_odd1, col_odd2, col_odd3 = st.columns(3)
    with col_odd1:
        odd_casa = st.number_input("🏠 Vitória Casa", 1.01, 10.0, 1.80, 0.01, key="odd_casa")
    with col_odd2:
        odd_empate = st.number_input("🤝 Empate", 1.01, 10.0, 3.50, 0.01, key="odd_empate")
    with col_odd3:
        odd_fora = st.number_input("✈️ Vitória Fora", 1.01, 10.0, 4.00, 0.01, key="odd_fora")

    st.markdown("**Gols Totais**")
    col_g1, col_g2, col_g3 = st.columns(3)
    with col_g1:
        odd_over15 = st.number_input("Over 1.5", 1.01, 20.0, value=None, step=0.01, format="%.2f", key="odd_over15")
    with col_g2:
        odd_over25 = st.number_input("Over 2.5", 1.01, 20.0, value=None, step=0.01, format="%.2f", key="odd_over25")
    with col_g3:
        odd_over35 = st.number_input("Over 3.5", 1.01, 20.0, value=None, step=0.01, format="%.2f", key="odd_over35")

    st.markdown("**Ambos Marcam (BTTS)**")
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        odd_btts_sim = st.number_input("BTTS Sim", 1.01, 20.0, value=None, step=0.01, format="%.2f", key="odd_btts_sim")
    with col_b2:
        odd_btts_nao = st.number_input("BTTS Não", 1.01, 20.0, value=None, step=0.01, format="%.2f", key="odd_btts_nao")

    st.markdown("**Gol 1º Tempo**")
    odd_ht = st.number_input("Gol 1º Tempo (Sim)", 1.01, 20.0, value=None, step=0.01, format="%.2f", key="odd_ht")
    # ============= BOTÃO DE ANÁLISE =============
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
            return calcular_ma_simples(sum(recente), len(recente), n_total, pv, pe)
        ma_A = ma_recente(seq_casa, prob_v_casa, prob_emp, n_casa)
        ma_B = ma_recente(seq_fora, prob_v_fora, prob_emp, n_fora)

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
            moral_pontos=moral_casa, pressao_p_obj=p_obj_A, pressao_sensibilidade=0.3
        )
        psic_B = calcular_psicologico(
            consistencia_pontos=seq_cons_fora if len(seq_cons_fora)>=5 else None,
            moral_pontos=moral_fora, pressao_p_obj=p_obj_B, pressao_sensibilidade=0.3
        )

        PESOS = {'MA': 0.25, 'FG': 0.25, 'CPP': 0.25, 'Psicologico': 0.25}
        EC_A = (ma_A*0.25 + fg_A*0.25 + cpp_A*0.25 + psic_A*0.25) + 2.0
        EC_B = (ma_B*0.25 + fg_B*0.25 + cpp_B*0.25 + psic_B*0.25)
        EC_A = max(0, min(100, EC_A))
        EC_B = max(0, min(100, EC_B))

        diff_ec = abs(EC_A - EC_B)
        LIMIAR_EMPATE = 5.0
        BONUS_MAX = 0.06
        P_EMP_BASE = 0.29
        P_EMP_MIN = 0.18

        if diff_ec < LIMIAR_EMPATE:
            p_emp = P_EMP_BASE + (1 - diff_ec / LIMIAR_EMPATE) * BONUS_MAX
        else:
            p_emp = max(P_EMP_MIN, P_EMP_BASE - (diff_ec / 100) * 0.15)

        total = EC_A + EC_B
        p_A = (1 - p_emp) * (EC_A / total) if total > 0 else 0.33
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

        under15_adj = 1 - over15_adj
        under25_adj = 1 - over25_adj
        under35_adj = 1 - over35_adj

        FATOR_HT = 0.44
        ajuste_estilo = 0
        if perfil_A in ["Pressão Alta", "Dominante"]:
            ajuste_estilo += 0.05
        if perfil_B in ["Pressão Alta", "Dominante"]:
            ajuste_estilo -= 0.05
        ajuste_ma = (ma_A - 50) * 0.001 + (ma_B - 50) * 0.001
        lambda_ht_adj = (lambda_casa_adj + lambda_fora_adj) * (FATOR_HT + ajuste_estilo + ajuste_ma)
        prob_gol_ht_adj = 1 - math.exp(-lambda_ht_adj)

        def prob_team_over(lam, k):
            return 1 - sum(math.exp(-lam)*(lam**i)/math.factorial(i) for i in range(k+1))
        casa_over05 = prob_team_over(lambda_casa_adj, 0)
        casa_over15 = prob_team_over(lambda_casa_adj, 1)
        casa_over25 = prob_team_over(lambda_casa_adj, 2)
        fora_over05 = prob_team_over(lambda_fora_adj, 0)
        fora_over15 = prob_team_over(lambda_fora_adj, 1)
        fora_over25 = prob_team_over(lambda_fora_adj, 2)

        # ==================== FUNÇÕES AUXILIARES ====================
        def desenhar_campo_duplo(fA, fB, nome_casa, nome_fora):
            fig = go.Figure()
            fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100,
                          fillcolor="#1B4D1B", line=dict(color="white", width=2))
            fig.add_shape(type="line", x0=50, y0=0, x1=50, y1=100,
                          line=dict(color="white", width=2))
            fig.add_shape(type="circle", x0=35, y0=35, x1=65, y1=65,
                          line=dict(color="white", width=2))
            fig.add_shape(type="rect", x0=0, y0=20, x1=20, y1=80,
                          line=dict(color="white", width=1.5))
            fig.add_shape(type="rect", x0=80, y0=20, x1=100, y1=80,
                          line=dict(color="white", width=1.5))
            fig.add_shape(type="rect", x0=0, y0=35, x1=10, y1=65,
                          line=dict(color="white", width=1))
            fig.add_shape(type="rect", x0=90, y0=35, x1=100, y1=65,
                          line=dict(color="white", width=1))
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
            st.markdown(f"""<div style="text-align:center; margin:16px 0; font-size:16px; font-weight:700; color:#F0C040;">🔺 {nome_casa} leva vantagem de +{EC_A - EC_B:.1f} pontos</div>""", unsafe_allow_html=True)
        elif EC_B > EC_A:
            st.markdown(f"""<div style="text-align:center; margin:16px 0; font-size:16px; font-weight:700; color:#4A90D9;">🔻 {nome_fora} leva vantagem de +{EC_B - EC_A:.1f} pontos</div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div style="text-align:center; margin:16px 0; font-size:16px; font-weight:700; color:#F0C040;">⚖️ Equilíbrio absoluto</div>""", unsafe_allow_html=True)

        # ==================== ABAS ====================
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("""<div style="text-align:center; margin-bottom:20px;"><span style="font-size:13px; text-transform:uppercase; letter-spacing:3px; color:#B0B8C0;">Análises Detalhadas</span></div>""", unsafe_allow_html=True)

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
            st.markdown('<div class="card-premium"><div class="card-header-premium">
                        # ----- ABA 3: Comparação Setorial -----
        with tabs[2]:
            st.markdown('<div class="card-premium"><div class="card-header-premium">⚔️ CONFRONTO POR ESTATÍSTICA</div>', unsafe_allow_html=True)
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
                st.markdown(f"""<div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.03); font-size:14px; color:#E0E0E0;"><span>{nome}</span><span>{nome_casa} {vA:.1f} × {vB:.1f} {nome_fora}</span><span style="font-weight:700; color:#F0C040;">{vant}</span></div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ----- ABA 4: Heatmap -----
        with tabs[3]:
            st.markdown('<div class="card-premium"><div class="card-header-premium">🗺️ HEATMAP TÁTICO</div>', unsafe_allow_html=True)
            fA = [def_A/100, mei_A/100, atq_A/100]
            fB = [atq_B/100, mei_B/100, def_B/100]
            fig_field = desenhar_campo_duplo(fA, fB, nome_casa, nome_fora)
            st.plotly_chart(fig_field, use_container_width=True)
            st.markdown('<div style="font-size:13px; color:#B0B8C0; text-align:center;">Dourado = Casa, Azul = Visitante.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ----- ABA 5: Cenários -----
        with tabs[4]:
            st.markdown('<div class="card-premium"><div class="card-header-premium">🎲 CINCO CENÁRIOS MAIS PROVÁVEIS</div>', unsafe_allow_html=True)
            for i, (tit, prob, just) in enumerate(gerar_cenarios_justificados()):
                st.markdown(f"""<div style="background:rgba(255,255,255,0.02); border-radius:8px; padding:12px 16px; margin:6px 0;"><div style="display:flex; justify-content:space-between; align-items:center;"><span style="font-weight:700; color:#E0E0E0;">{i+1}. {tit}</span><span style="font-size:20px; font-weight:900; color:#F0C040;">{prob:.1%}</span></div><div style="font-size:13px; color:#B0B8C0; margin-top:4px;">{just}</div></div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ----- ABA 6: Ajuste EC -----
        with tabs[5]:
            st.markdown('<div class="card-premium"><div class="card-header-premium">🔧 AJUSTE ENGRAMSCORE NOS GOLS ESPERADOS</div>', unsafe_allow_html=True)
            st.markdown(f"""<div style="text-align:center; margin:16px 0;"><span style="font-size:14px; color:#B0B8C0;">Fator de Ajuste:</span><span style="font-size:24px; font-weight:900; color:#F0C040; margin-left:8px;">{fator_ajuste:+.2f}</span></div>""", unsafe_allow_html=True)
            col_orig, col_adj = st.columns(2)
            with col_orig:
                st.markdown(f"""<div style="background:rgba(255,255,255,0.02); border-radius:8px; padding:16px; text-align:center;"><div style="font-size:13px; color:#B0B8C0;">Lambdas Originais</div><div style="font-size:28px; font-weight:900; color:#B0B8C0;">λ Casa: {lambda_casa_orig:.2f}</div><div style="font-size:28px; font-weight:900; color:#B0B8C0;">λ Fora: {lambda_fora_orig:.2f}</div></div>""", unsafe_allow_html=True)
            with col_adj:
                st.markdown(f"""<div style="background:rgba(240,192,64,0.03); border:1px solid rgba(240,192,64,0.2); border-radius:8px; padding:16px; text-align:center;"><div style="font-size:13px; color:#F0C040;">Lambdas Ajustados</div><div style="font-size:28px; font-weight:900; color:#F0C040;">λ Casa: {lambda_casa_adj:.2f}</div><div style="font-size:28px; font-weight:900; color:#F0C040;">λ Fora: {lambda_fora_adj:.2f}</div></div>""", unsafe_allow_html=True)
            st.markdown("""<div class="info-card" style="margin-top:16px;">Se o time da casa é muito superior (EC_A > EC_B), seu λ ofensivo <strong>aumenta</strong> e o λ do visitante <strong>diminui</strong>. Isso reduz a chance de o time mais fraco marcar, refletindo a superioridade medida pelo EngramScore.</div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ----- ABA 7: MERCADOS -----
        with tabs[6]:
            st.markdown('<div class="card-premium"><div class="card-header-premium">📊 PROBABILIDADES 1X2</div>', unsafe_allow_html=True)
            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                st.markdown(f"""<div class="prob-box"><div style="color:#00E676; font-size:14px; text-transform:uppercase; letter-spacing:1px;">Vitória {nome_casa}</div>{valor_com_destaque(p_A, p_A)}<div style="margin-top:8px;">{selo(p_A)}</div></div>""", unsafe_allow_html=True)
            with col_p2:
                st.markdown(f"""<div class="prob-box"><div style="color:#F0C040; font-size:14px; text-transform:uppercase; letter-spacing:1px;">Empate</div>{valor_com_destaque(p_emp, p_emp)}<div style="margin-top:8px;">{selo(p_emp)}</div></div>""", unsafe_allow_html=True)
            with col_p3:
                st.markdown(f"""<div class="prob-box"><div style="color:#4A90D9; font-size:14px; text-transform:uppercase; letter-spacing:1px;">Vitória {nome_fora}</div>{valor_com_destaque(p_B, p_B)}<div style="margin-top:8px;">{selo(p_B)}</div></div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="card-premium"><div class="card-header-premium">⚽ PROBABILIDADES DE GOLS (TOTAIS)</div>', unsafe_allow_html=True)
            col_g1, col_g2, col_g3 = st.columns(3)
            col_g1.metric("Over 1.5", f"{over15_adj:.1%}")
            col_g2.metric("Over 2.5", f"{over25_adj:.1%}")
            col_g3.metric("Over 3.5", f"{over35_adj:.1%}")
            col_g4, col_g5, col_g6 = st.columns(3)
            col_g4.metric("Under 1.5", f"{under15_adj:.1%}")
            col_g5.metric("Under 2.5", f"{under25_adj:.1%}")
            col_g6.metric("Under 3.5", f"{under35_adj:.1%}")
            col_b1, col_b2, col_b3 = st.columns(3)
            col_b1.metric("BTTS Sim", f"{btts_adj:.1%}")
            col_b2.metric("BTTS Não", f"{1-btts_adj:.1%}")
            col_b3.metric("Gol 1º Tempo", f"{prob_gol_ht_adj:.1%}")
            st.markdown(f"""<div class="info-card"><strong>λ original:</strong> Casa {lambda_casa_orig:.2f}, Fora {lambda_fora_orig:.2f}<br><strong>λ ajustado:</strong> Casa {lambda_casa_adj:.2f}, Fora {lambda_fora_adj:.2f}</div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="card-premium"><div class="card-header-premium">🎯 PROBABILIDADES INDIVIDUAIS DE GOLS</div>', unsafe_allow_html=True)
            col_i1, col_i2 = st.columns(2)
            with col_i1:
                st.markdown(f"**{nome_casa}**")
                st.metric("Over 0.5", f"{casa_over05:.1%}")
                st.metric("Over 1.5", f"{casa_over15:.1%}")
                st.metric("Over 2.5", f"{casa_over25:.1%}")
            with col_i2:
                st.markdown(f"**{nome_fora}**")
                st.metric("Over 0.5", f"{fora_over05:.1%}")
                st.metric("Over 1.5", f"{fora_over15:.1%}")
                st.metric("Over 2.5", f"{fora_over25:.1%}")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="card-premium"><div class="card-header-premium">📈 COMPARAÇÃO MODELO vs MERCADO (EDGE)</div>', unsafe_allow_html=True)
            probs_modelo = {
                f"Vitória {nome_casa}": p_A, "Empate": p_emp, f"Vitória {nome_fora}": p_B,
                "Over 1.5": over15_adj, "Over 2.5": over25_adj, "Over 3.5": over35_adj,
                "BTTS Sim": btts_adj, "BTTS Não": 1-btts_adj, "Gol 1º Tempo": prob_gol_ht_adj,
            }
            odds_reais = {
                f"Vitória {nome_casa}": odd_casa, "Empate": odd_empate, f"Vitória {nome_fora}": odd_fora,
                "Over 1.5": odd_over15, "Over 2.5": odd_over25, "Over 3.5": odd_over35,
                "BTTS Sim": odd_btts_sim, "BTTS Não": odd_btts_nao, "Gol 1º Tempo": odd_ht,
            }
            linhas = []
            for mercado, prob in probs_modelo.items():
                odd_mod = 1/prob if prob>0 else 999
                odd_real = odds_reais.get(mercado)
                if odd_real and odd_real > 1.0:
                    ev = (prob * odd_real - 1) * 100
                    linhas.append((mercado, f"{prob:.1%}", f"{odd_mod:.2f}", f"{odd_real:.2f}", f"{ev:+.1f}%", "💚 Valor" if ev>0 else "🔴 Sem Valor"))
                else:
                    linhas.append((mercado, f"{prob:.1%}", f"{odd_mod:.2f}", "-", "-", "⚪ Sem odd"))
            df_edge = pd.DataFrame(linhas, columns=["Mercado", "Prob. Modelo", "Odd Justa", "Odd Real", "EV%", "Indicação"])
            st.dataframe(df_edge, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ----- ABA 8: Destaques -----
        with tabs[7]:
            st.markdown('<div class="card-premium"><div class="card-header-premium">🌟 DESTAQUES (PROBABILIDADE > 65%)</div>', unsafe_allow_html=True)
            destaques = []
            if p_A > 0.65: destaques.append((f"Vitória {nome_casa}", p_A))
            if p_emp > 0.65: destaques.append(("Empate", p_emp))
            if p_B > 0.65: destaques.append((f"Vitória {nome_fora}", p_B))
            for nome, prob in [("Over 1.5", over15_adj), ("Over 2.5", over25_adj), ("Over 3.5", over35_adj), ("BTTS Sim", btts_adj), ("Gol 1º Tempo", prob_gol_ht_adj)]:
                if prob > 0.65: destaques.append((nome, prob))
            if destaques:
                for nome, prob in destaques:
                    st.markdown(f"""<div style="background:rgba(240,192,64,0.08); border:1px solid rgba(240,192,64,0.3); border-radius:10px; padding:14px; margin:6px 0; display:flex; justify-content:space-between; align-items:center;"><span style="color:#F0C040; font-weight:700;">{nome}</span><span style="font-size:24px; font-weight:900; background:linear-gradient(180deg, #F0C040 0%, #D4A017 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">{prob:.1%}</span></div>""", unsafe_allow_html=True)
            else:
                st.markdown('<div style="color:#B0B8C0; text-align:center;">Nenhuma probabilidade acima de 65%.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ----- ABA 9: ANÁLISE DESCRITIVA -----
        with tabs[8]:
            st.markdown('<div class="card-premium"><div class="card-header-premium">📝 ANÁLISE DESCRITIVA COMPLETA</div>', unsafe_allow_html=True)

            st.markdown("### 🔍 Pilares Individuais")
            st.markdown(f"""<div class="info-card"><strong>Momento Atual:</strong> {nome_casa} {ma_A:.1f} × {nome_fora} {ma_B:.1f}.<br><strong>Força Geral:</strong> {nome_casa} {fg_A:.1f} × {nome_fora} {fg_B:.1f}.<br><strong>Confronto:</strong> {nome_casa} {cpp_A:.1f} × {nome_fora} {cpp_B:.1f}.<br><strong>Psicológico:</strong> {nome_casa} {psic_A:.1f} × {nome_fora} {psic_B:.1f}.</div>""", unsafe_allow_html=True)

            st.markdown("### ⚔️ Diferenciais por Pilar")
            dif_ma = ma_A - ma_B
            dif_fg = fg_A - fg_B
            dif_cpp = cpp_A - cpp_B
            dif_psic = psic_A - psic_B
            vantagens_A = []
            vantagens_B = []
            if dif_ma > 0: vantagens_A.append("Momento Atual (MA)")
            elif dif_ma < 0: vantagens_B.append("Momento Atual (MA)")
            if dif_fg > 0: vantagens_A.append("Força Geral (FG)")
            elif dif_fg < 0: vantagens_B.append("Força Geral (FG)")
            if dif_cpp > 0: vantagens_A.append("Confronto (CPP)")
            elif dif_cpp < 0: vantagens_B.append("Confronto (CPP)")
            if dif_psic > 0: vantagens_A.append("Psicológico")
            elif dif_psic < 0: vantagens_B.append("Psicológico")
            if vantagens_A: st.markdown(f"<div class='info-card'><strong>{nome_casa}</strong> leva vantagem em: {', '.join(vantagens_A)}.</div>", unsafe_allow_html=True)
            if vantagens_B: st.markdown(f"<div class='info-card'><strong>{nome_fora}</strong> leva vantagem em: {', '.join(vantagens_B)}.</div>", unsafe_allow_html=True)

            st.markdown("### ⚡ EngramScore")
            st.markdown(f"""<div class="info-card">{nome_casa} <strong>{EC_A:.1f}</strong> vs {nome_fora} <strong>{EC_B:.1f}</strong>.</div>""", unsafe_allow_html=True)

            st.markdown("### 🎯 Desempenho Setorial")
            st.markdown(f"""<div class="info-card"><strong>Ataque:</strong> {nome_casa} {atq_A:.1f} × {nome_fora} {atq_B:.1f}.<br><strong>Defesa:</strong> {nome_casa} {def_A:.1f} × {nome_fora} {def_B:.1f}.<br><strong>Meio:</strong> {nome_casa} {mei_A:.1f} × {nome_fora} {mei_B:.1f}.</div>""", unsafe_allow_html=True)

            st.markdown(f"""<div class="info-card">{nome_casa} é <strong>{perfil_A}</strong>, {nome_fora} é <strong>{perfil_B}</strong>.</div>""", unsafe_allow_html=True)

            st.markdown("### 📊 Expectativa de Gols")
            st.markdown(f"""<div class="info-card">Total esperado: <strong>{lambda_casa_adj+lambda_fora_adj:.2f}</strong> gols. Over 1.5: <strong>{over15_adj:.1%}</strong>, Over 2.5: <strong>{over25_adj:.1%}</strong>, BTTS: <strong>{btts_adj:.1%}</strong>, Gol 1ºT: <strong>{prob_gol_ht_adj:.1%}</strong>.</div>""", unsafe_allow_html=True)

            cen = gerar_cenarios_justificados()
            st.markdown(f"""<div class="info-card"><strong>Cenário mais provável:</strong> {cen[0][0]} ({cen[0][1]:.1%})</div>""", unsafe_allow_html=True)

            # 8. Recomendação Final
            st.markdown("### 📌 Recomendação Final")
            resultados = [
                (f"Vitória do {nome_casa}", p_A, vantagens_A, "mandante"),
                ("Empate", p_emp, [], "empate"),
                (f"Vitória do {nome_fora}", p_B, vantagens_B, "visitante")
            ]
            resultado_final = max(resultados, key=lambda x: x[1])
            nome_res, prob_res, vantagens_res, tipo_res = resultado_final

            if tipo_res == "empate":
                justificativa = "O equilíbrio nos pilares indica uma partida disputada, com pouca margem para desequilíbrio."
                if diff_ec < 5:
                    justificativa += " A diferença de EngramScore é mínima, reforçando a tendência de igualdade."
                cor_borda = "#F0C040"
            else:
                if vantagens_res:
                    justificativa = f"As vantagens nos pilares {', '.join(vantagens_res)} dão a {nome_res.split()[-1]} a superioridade necessária."
                else:
                    if tipo_res == "mandante":
                        justificativa = "Apesar do equilíbrio nos pilares individuais, o fator casa e a ligeira superioridade no EngramScore inclinam a balança para o mandante."
                    else:
                        justificativa = "Mesmo sem dominar amplamente os pilares, o visitante apresenta um EngramScore superior, o que justifica o favoritismo."
                cor_borda = "#00E676" if tipo_res == "mandante" else "#4A90D9"

            st.markdown(f"""<div class="info-card" style="border-color:{cor_borda};"><strong>{nome_res}</strong> é o resultado mais provável, com <strong>{prob_res:.1%}</strong> de chance.<br>{justificativa}</div>""", unsafe_allow_html=True)

            if tipo_res != "empate" and p_emp > 0.25:
                st.markdown(f"""<div class="info-card" style="border-color:#F0C040; margin-top:8px;">⚠️ O empate também merece atenção, com <strong>{p_emp:.1%}</strong> de probabilidade.</div>""", unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

    # Rodapé
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("""<div style="text-align:center; padding:20px; color:#B0B8C0; font-size:13px; letter-spacing:2px;">ENGRAMSCORE © 2026 · ANÁLISE DIFERENCIAL DE FORÇA</div>""", unsafe_allow_html=True)
