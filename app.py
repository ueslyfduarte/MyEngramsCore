import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from src.metricas.ma import calcular_ma, calcular_pontos_e_resultados
from src.metricas.fg import calcular_fg
from src.metricas.cpp import calcular_cpp
from src.metricas.estilo import calcular_vetor_estilo, calcular_estilo
from src.metricas.psicologico import calcular_psicologico
from src.metricas.engramscore import calcular_engramscore
from src.mercados.gols import calcular_mercado_gols

# ==================== CONFIGURAÇÃO VISUAL ====================
st.set_page_config(page_title="EngramsCore ⚽", page_icon="⚽", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0a0a0a; color: #FFD700; }
    .css-1d391kg, .st-bb, .st-at, .st-af, .st-ae, .st-ag, .st-ah, .st-ai, .st-aj { background-color: #0a0a0a; }
    h1, h2, h3, h4, h5, h6 { color: #FFD700 !important; }
    .stExpander, div[data-testid="stExpander"] {
        background-color: #1a1a1a; border: 1px solid #FFD700;
        border-radius: 10px; padding: 15px; margin-bottom: 15px;
        box-shadow: 0px 0px 15px rgba(255,215,0,0.3);
    }
    .stProgress > div > div { background-color: #FFD700; }
    .stMetric label, .stMetric [data-testid="stMetricValue"] { color: #FFD700 !important; }
    .stButton>button, .stTextInput>div>input, .stNumberInput>div>input {
        background-color: #2a2a2a; color: #FFD700;
        border: 1px solid #FFD700; border-radius: 5px;
    }
    .stSlider>div>div>div { background-color: #FFD700; }
    section[data-testid="stSidebar"] { background-color: #111; border-right: 2px solid #FFD700; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ ENGRAMS CORE")
st.markdown("<p style='color:#FFD700; font-size:1.2em;'>Análise Comparativa de Equipes para um Confronto</p>", unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("📊 Médias da Liga (Referência)")
    media_gm = st.number_input("Gols marcados/jogo", 0.1, 5.0, 1.4, 0.1)
    media_gs = st.number_input("Gols sofridos/jogo", 0.1, 5.0, 1.4, 0.1)
    media_posse = st.number_input("Posse de bola (%)", 0.0, 100.0, 50.0, 1.0)
    medias_liga = {'GM': media_gm, 'GS': media_gs, 'Posse': media_posse}
    st.markdown("---")
    st.info("⚙️ Ajuste conforme a liga analisada.")

# ==================== ENTRADA DE DADOS ====================
# Função para criar um bloco de pilar dentro de um expander
def criar_bloco_ma(equipe, prefixo):
    st.markdown("**📈 Momento Atual**")
    c1, c2, c3 = st.columns(3)
    with c1:
        odd = st.number_input("Odd vitória", min_value=1.01, value=1.80, step=0.01, key=f"{prefixo}_odd")
    with c2:
        res = st.text_input("Últimos resultados (V/E/D)", "VVEDV", key=f"{prefixo}_res").upper()
    pontos, v, d = calcular_pontos_e_resultados(list(res))
    ma = calcular_ma(pontos, v, d, odd)
    with c3:
        st.metric("MA", f"{ma:.1f}")
    st.progress(int(ma))
    st.caption(f"Vitórias: {v} | Empates: {len(res)-v-d} | Derrotas: {d}")
    return ma

def criar_bloco_fg(equipe, prefixo):
    st.markdown("**💪 Força Geral**")
    c1, c2, c3 = st.columns(3)
    with c1:
        gm = st.number_input("Gols/jogo", 0.0, 5.0, 2.0, 0.1, key=f"{prefixo}_gm")
        fa = st.number_input("Finalizações/jogo", 0.0, 10.0, 4.5, 0.1, key=f"{prefixo}_fa")
    with c2:
        gs = st.number_input("Gols sofridos/jogo", 0.0, 5.0, 0.8, 0.1, key=f"{prefixo}_gs")
        xga = st.number_input("xG contra", 0.0, 5.0, 0.9, 0.1, key=f"{prefixo}_xga")
    with c3:
        posse = st.slider("Posse (%)", 0, 100, 55, key=f"{prefixo}_posse")
    dados_fg = {'GM': gm, 'FA': fa, 'GS': gs, 'xGA': xga, 'Posse': posse}
    dados_fg = {k: v for k, v in dados_fg.items() if v != 0.0}
    n_jogos = st.number_input("Jogos na temporada", 1, 38, 10, key=f"{prefixo}_njogos")
    fg = calcular_fg(dados_fg, medias_liga, n_jogos)
    st.metric("FG", f"{fg:.1f}")
    st.progress(int(fg))
    return fg, dados_fg, n_jogos

def criar_bloco_cpp(equipe, prefixo):
    st.markdown("**🏆 Confronto por Prateleira**")
    c1, c2 = st.columns(2)
    with c1:
        pts = st.number_input("Pontos conquistados", 0, 30, 6, key=f"{prefixo}_pcpp")
    with c2:
        jogos = st.number_input("Nº de jogos", 0, 10, 3, key=f"{prefixo}_jcpp")
    odd = st.number_input("Odd vitória", min_value=1.01, value=1.80, step=0.01, key=f"{prefixo}_odd_cpp")
    cpp = calcular_cpp(pts, jogos, odd)
    st.metric("CPP", f"{cpp:.1f}")
    return cpp

def criar_bloco_estilo(equipe, prefixo):
    st.markdown("**🎨 Estilo de Jogo**")
    c1, c2 = st.columns(2)
    with c1:
        posse_est = st.slider("Posse (%)", 0, 100, 55, key=f"{prefixo}_posse_est")
        ppda = st.number_input("PPDA (menos é mais)", 0.0, 20.0, 0.0, key=f"{prefixo}_ppda")
    with c2:
        trans = st.number_input("Chutes transição/jogo", 0.0, 10.0, 0.0, key=f"{prefixo}_trans")
    dados_estilo = {}
    if posse_est > 0: dados_estilo['posse'] = posse_est
    if ppda > 0: dados_estilo['ppda'] = ppda
    if trans > 0: dados_estilo['chutes_trans'] = trans
    n_jogos = st.number_input("Jogos", 1, 38, 10, key=f"{prefixo}_njogos_est")
    vetor = calcular_vetor_estilo(dados_estilo, medias_liga, n_jogos)
    st.write("Vetor:", vetor)
    return dados_estilo, vetor, n_jogos

def criar_bloco_psicologico(equipe, prefixo):
    st.markdown("**🧠 Psicológico**")
    cons = st.text_input("Últimos 10 resultados", "VVEDVVEDVV", key=f"{prefixo}_cons").upper()
    pts_cons, _, _ = calcular_pontos_e_resultados(list(cons))
    moral = st.slider("Moral (pts 3 jogos)", 0, 9, 6, key=f"{prefixo}_moral")
    p_obj = st.slider("Pressão objetiva (0-100)", 0, 100, 40, key=f"{prefixo}_pobj")
    sens = st.slider("Sensibilidade (-1 a +1)", -1.0, 1.0, 0.0, 0.1, key=f"{prefixo}_sens")
    psic = calcular_psicologico(
        consistencia_pontos=pts_cons,
        moral_pontos=moral,
        pressao_p_obj=p_obj,
        pressao_sensibilidade=sens
    )
    st.metric("Psicológico", f"{psic:.1f}")
    return psic

# Layout principal: dois tabs (Time A e Time B)
tab_a, tab_b = st.tabs(["🏠 Time A (Mandante)", "✈️ Time B (Visitante)"])

with tab_a:
    st.header("Time A - Mandante")
    nome_a = st.text_input("Nome do time", "Time A", key="nome_a")
    with st.expander("MA - Momento Atual", expanded=True):
        ma_a = criar_bloco_ma("A", "a")
    with st.expander("FG - Força Geral", expanded=True):
        fg_a, dados_fg_a, n_a = criar_bloco_fg("A", "a")
    with st.expander("CPP - Confronto por Prateleira", expanded=True):
        cpp_a = criar_bloco_cpp("A", "a")
    with st.expander("Estilo de Jogo", expanded=True):
        dados_estilo_a, vetor_estilo_a, n_est_a = criar_bloco_estilo("A", "a")
    with st.expander("Psicológico", expanded=True):
        psic_a = criar_bloco_psicologico("A", "a")
    prateleira_a = st.selectbox("Prateleira", ["Elite", "Alta", "Média", "Baixa", "Crítico"], key="prat_a")
    prat_map = {"Elite": 0, "Alta": 1, "Média": 2, "Baixa": 3, "Crítico": 4}
    prat_a_num = prat_map[prateleira_a]

with tab_b:
    st.header("Time B - Visitante")
    nome_b = st.text_input("Nome do time", "Time B", key="nome_b")
    with st.expander("MA - Momento Atual", expanded=True):
        ma_b = criar_bloco_ma("B", "b")
    with st.expander("FG - Força Geral", expanded=True):
        fg_b, dados_fg_b, n_b = criar_bloco_fg("B", "b")
    with st.expander("CPP - Confronto por Prateleira", expanded=True):
        cpp_b = criar_bloco_cpp("B", "b")
    with st.expander("Estilo de Jogo", expanded=True):
        dados_estilo_b, vetor_estilo_b, n_est_b = criar_bloco_estilo("B", "b")
    with st.expander("Psicológico", expanded=True):
        psic_b = criar_bloco_psicologico("B", "b")
    prateleira_b = st.selectbox("Prateleira", ["Elite", "Alta", "Média", "Baixa", "Crítico"], key="prat_b")
    prat_b_num = prat_map[prateleira_b]

# ==================== CÁLCULO DO ESTILO CRUZADO ====================
estilo_a = calcular_estilo(dados_estilo_a, medias_liga, n_est_a, vetor_estilo_b) if vetor_estilo_b else 50.0
estilo_b = calcular_estilo(dados_estilo_b, medias_liga, n_est_b, vetor_estilo_a) if vetor_estilo_a else 50.0

# ==================== RESULTADOS ====================
st.header("📊 Comparativo dos Pilares")
pilares = ['MA', 'FG', 'CPP', 'Estilo', 'Psicológico']
valores_a = [ma_a, fg_a, cpp_a, estilo_a, psic_a]
valores_b = [ma_b, fg_b, cpp_b, estilo_b, psic_b]

# Gráfico de radar
fig_radar = go.Figure()
fig_radar.add_trace(go.Scatterpolar(r=valores_a, theta=pilares, fill='toself', name=nome_a, marker=dict(color='#FFD700')))
fig_radar.add_trace(go.Scatterpolar(r=valores_b, theta=pilares, fill='toself', name=nome_b, marker=dict(color='#B8860B')))
fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True, template='plotly_dark')
st.plotly_chart(fig_radar, use_container_width=True)

# Tabela comparativa
df_comp = pd.DataFrame({'Pilar': pilares, nome_a: valores_a, nome_b: valores_b, 'Diferença': [a - b for a, b in zip(valores_a, valores_b)]})
st.dataframe(df_comp.style.format({nome_a: "{:.1f}", nome_b: "{:.1f}", 'Diferença': "{:.1f}"}), use_container_width=True)

# ==================== ENGRAMS CORE ====================
st.header("⚡ EngramsCore")
ec = calcular_engramscore(
    ma_a=ma_a, fg_a=fg_a, cpp_a=cpp_a, estilo_a=estilo_a, psicologico_a=psic_a,
    ma_b=ma_b, fg_b=fg_b, cpp_b=cpp_b, estilo_b=estilo_b, psicologico_b=psic_b,
    time_mandante='A'
)

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"<h2 style='text-align:center; color:#FFD700;'>{nome_a}</h2>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center; color:#FFD700;'>{ec['EC_A']:.1f}</h1>", unsafe_allow_html=True)
    st.progress(int(ec['EC_A']))
with col2:
    st.markdown(f"<h2 style='text-align:center; color:#FFD700;'>{nome_b}</h2>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center; color:#FFD700;'>{ec['EC_B']:.1f}</h1>", unsafe_allow_html=True)
    st.progress(int(ec['EC_B']))

st.subheader("Probabilidades 1X2")
probs = {'Resultado': [f'Vitória {nome_a}', 'Empate', f'Vitória {nome_b}'], 'Probabilidade': [ec['P_A'], ec['P_E'], ec['P_B']]}
fig_barras = px.bar(probs, x='Resultado', y='Probabilidade', color='Resultado', color_discrete_sequence=['#FFD700', '#B8860B', '#8B7500'])
st.plotly_chart(fig_barras, use_container_width=True)

st.write(f"Dupla chance {nome_a} ou Empate: {ec['P_A_ou_E']:.2%}")
st.write(f"Dupla chance {nome_b} ou Empate: {ec['P_B_ou_E']:.2%}")

# ==================== MERCADO DE GOLS ====================
st.header("⚽ Mercado de Gols")
odd_over25 = st.number_input("Odd Over 2.5", 1.01, 10.0, 1.90, 0.01, key="odd_over")
n_jogos_mercado = st.number_input("Jogos temporada (para peso dinâmico)", 1, 38, max(n_a, n_b), key="n_mercado")

fg_dict_a = {'ataque': fg_a, 'defesa': fg_a, 'meio': fg_a}
fg_dict_b = {'ataque': fg_b, 'defesa': fg_b, 'meio': fg_b}
psic_dict_a = {'moral': 60, 'pressao_obj': 40, 'sensibilidade': 0.0}  # valores padrão
psic_dict_b = {'moral': 60, 'pressao_obj': 40, 'sensibilidade': 0.0}

gols = calcular_mercado_gols(
    gols_marcados_a=dados_fg_a.get('GM', 1.0), gols_sofridos_a=dados_fg_a.get('GS', 1.0),
    gols_marcados_b=dados_fg_b.get('GM', 1.0), gols_sofridos_b=dados_fg_b.get('GS', 1.0),
    n_jogos=n_jogos_mercado,
    ma_a=ma_a, ma_b=ma_b,
    fg_a=fg_dict_a, fg_b=fg_dict_b,
    cpp_a=cpp_a, cpp_b=cpp_b,
    estilo_a=vetor_estilo_a, estilo_b=vetor_estilo_b,
    psic_a=psic_dict_a, psic_b=psic_dict_b,
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

st.caption(f"λ modelo: {gols['lambda_modelo']:.3f} | λ mercado: {gols['lambda_mercado']:.3f} | λ final: {gols['lambda_final']:.3f}")
