import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

from src.metricas.ma import calcular_ma, calcular_pontos_e_resultados
from src.metricas.fg import calcular_fg
from src.metricas.cpp import calcular_cpp
from src.metricas.estilo import calcular_vetor_estilo, calcular_estilo
from src.metricas.psicologico import calcular_psicologico
from src.metricas.engramscore import calcular_engramscore
from src.mercados.gols import calcular_mercado_gols

# ==================== CONFIGURAÇÃO VISUAL ====================
st.set_page_config(page_title="EngramsCore", page_icon="⚽", layout="wide")

st.markdown("""
<style>
    .stApp {
        background-color: #0a0a0a;
        color: #FFD700;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #FFD700 !important;
        text-shadow: 1px 1px 3px #000;
    }
    .stExpander, .stMetric, div[data-testid="stExpander"] {
        background-color: #1a1a1a;
        border: 1px solid #FFD700;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 15px;
        box-shadow: 0px 0px 15px rgba(255, 215, 0, 0.3);
    }
    .stProgress > div > div {
        background-color: #FFD700;
    }
    .stMetric label, .stMetric [data-testid="stMetricValue"] {
        color: #FFD700 !important;
    }
    .stButton>button, .stTextInput>div>input, .stNumberInput>div>input {
        background-color: #2a2a2a;
        color: #FFD700;
        border: 1px solid #FFD700;
        border-radius: 5px;
    }
    .stSlider>div>div>div {
        background-color: #FFD700;
    }
    section[data-testid="stSidebar"] {
        background-color: #111;
        border-right: 2px solid #FFD700;
    }
    .stAlert {
        background-color: #2a2a2a;
        color: #FFD700;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚽ ENGRAMS CORE")
st.markdown("<p style='color:#FFD700; font-size:1.3em;'>Sistema de Análise Esportiva Diferencial</p>", unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("📊 Médias da Liga")
    media_gm = st.number_input("Gols marcados/jogo", 0.1, 5.0, 1.4, 0.1)
    media_gs = st.number_input("Gols sofridos/jogo", 0.1, 5.0, 1.4, 0.1)
    media_posse = st.number_input("Posse de bola (%)", 0.0, 100.0, 50.0, 1.0)
    medias_liga = {
        'GM': media_gm,
        'GS': media_gs,
        'Posse': media_posse,
    }
    st.markdown("---")
    st.info("⚙️ Ajuste as médias conforme a liga.")

# ==================== TIMES (COLUNAS) ====================
col1, col2 = st.columns(2, gap="large")

# ---- TIME A ----
with col1:
    st.header("🏠 Time A (Mandante)")
    nome_a = st.text_input("Nome", "Time A", key="nome_a")

    with st.expander("📈 MA - Momento Atual", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            odd_a = st.number_input("Odd vitória", min_value=1.01, value=1.80, step=0.01, key="odd_a")
        with c2:
            res_a = st.text_input("Últimos resultados (V/E/D)", "VVEDV", key="res_a").upper()
        pontos_a, v_a, d_a = calcular_pontos_e_resultados(list(res_a))
        ma_a = calcular_ma(pontos_a, v_a, d_a, odd_a)
        with c3:
            st.metric("MA", f"{ma_a:.1f}")
        st.progress(int(ma_a))
        st.caption(f"Vitórias: {v_a} | Empates: {len(res_a)-v_a-d_a} | Derrotas: {d_a}")

    with st.expander("💪 FG - Força Geral", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            gm_a = st.number_input("Gols/jogo", 0.0, 5.0, 2.0, 0.1, key="gm_a")
            fa_a = st.number_input("Finalizações/jogo", 0.0, 10.0, 4.5, 0.1, key="fa_a")
        with c2:
            gs_a = st.number_input("Gols sofridos/jogo", 0.0, 5.0, 0.8, 0.1, key="gs_a")
            xga_a = st.number_input("xG contra", 0.0, 5.0, 0.9, 0.1, key="xga_a")
        with c3:
            posse_a = st.slider("Posse (%)", 0, 100, 55, key="posse_a")
        dados_fg_a = {'GM': gm_a, 'FA': fa_a, 'GS': gs_a, 'xGA': xga_a, 'Posse': posse_a}
        dados_fg_a = {k: v for k, v in dados_fg_a.items() if v != 0.0}
        n_jogos_a = st.number_input("Jogos temporada", 1, 38, 10, key="n_a")
        fg_a = calcular_fg(dados_fg_a, medias_liga, n_jogos_a)
        st.metric("FG", f"{fg_a:.1f}")
        st.progress(int(fg_a))

    with st.expander("🏆 CPP", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            pts_cpp_a = st.number_input("Pontos", 0, 30, 6, key="pcpp_a")
        with c2:
            jogos_cpp_a = st.number_input("Jogos", 0, 10, 3, key="jcpp_a")
        cpp_a = calcular_cpp(pts_cpp_a, jogos_cpp_a, odd_a)
        st.metric("CPP", f"{cpp_a:.1f}")

    with st.expander("🎨 Estilo", expanded=False):
        st.markdown("**Indicadores (deixe 0 se não disponível)**")
        c1, c2 = st.columns(2)
        with c1:
            posse_est_a = st.slider("Posse (%)", 0, 100, 55, key="posse_est_a")
            ppda_a = st.number_input("PPDA", 0.0, 20.0, 0.0, key="ppda_a")
        with c2:
            trans_a = st.number_input("Chutes transição", 0.0, 10.0, 0.0, key="trans_a")
        dados_estilo_a = {}
        if posse_est_a > 0: dados_estilo_a['posse'] = posse_est_a
        if ppda_a > 0: dados_estilo_a['ppda'] = ppda_a
        if trans_a > 0: dados_estilo_a['chutes_trans'] = trans_a
        vetor_estilo_a = calcular_vetor_estilo(dados_estilo_a, medias_liga, n_jogos_a)
        st.write(vetor_estilo_a)

    with st.expander("🧠 Psicológico", expanded=False):
        cons_a = st.text_input("Últimos 10 resultados", "VVEDVVEDVV", key="cons_a").upper()
        pts_cons_a, _, _ = calcular_pontos_e_resultados(list(cons_a))
        moral_a = st.slider("Moral (pts 3 jogos)", 0, 9, 6, key="moral_a")
        p_obj_a = st.slider("Pressão", 0, 100, 40, key="pobj_a")
        sens_a = st.slider("Sensibilidade", -1.0, 1.0, 0.0, 0.1, key="sens_a")
        psic_a = calcular_psicologico(consistencia_pontos=pts_cons_a, moral_pontos=moral_a,
                                      pressao_p_obj=p_obj_a, pressao_sensibilidade=sens_a)
        st.metric("Psicológico", f"{psic_a:.1f}")

    prateleira_a = st.selectbox("Prateleira", ["Elite", "Alta", "Média", "Baixa", "Crítico"], key="prat_a")
    prat_map = {"Elite": 0, "Alta": 1, "Média": 2, "Baixa": 3, "Crítico": 4}
    prat_a_num = prat_map[prateleira_a]

# ---- TIME B ----
with col2:
    st.header("✈️ Time B (Visitante)")
    nome_b = st.text_input("Nome", "Time B", key="nome_b")

    with st.expander("📈 MA - Momento Atual", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            odd_b = st.number_input("Odd vitória", min_value=1.01, value=4.00, step=0.01, key="odd_b")
        with c2:
            res_b = st.text_input("Últimos resultados (V/E/D)", "DDVVE", key="res_b").upper()
        pontos_b, v_b, d_b = calcular_pontos_e_resultados(list(res_b))
        ma_b = calcular_ma(pontos_b, v_b, d_b, odd_b)
        with c3:
            st.metric("MA", f"{ma_b:.1f}")
        st.progress(int(ma_b))
        st.caption(f"Vitórias: {v_b} | Empates: {len(res_b)-v_b-d_b} | Derrotas: {d_b}")

    with st.expander("💪 FG - Força Geral", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            gm_b = st.number_input("Gols/jogo", 0.0, 5.0, 1.2, 0.1, key="gm_b")
            fa_b = st.number_input("Finalizações/jogo", 0.0, 10.0, 3.2, 0.1, key="fa_b")
        with c2:
            gs_b = st.number_input("Gols sofridos/jogo", 0.0, 5.0, 1.5, 0.1, key="gs_b")
            xga_b = st.number_input("xG contra", 0.0, 5.0, 1.4, 0.1, key="xga_b")
        with c3:
            posse_b = st.slider("Posse (%)", 0, 100, 48, key="posse_b")
        dados_fg_b = {'GM': gm_b, 'FA': fa_b, 'GS': gs_b, 'xGA': xga_b, 'Posse': posse_b}
        dados_fg_b = {k: v for k, v in dados_fg_b.items() if v != 0.0}
        n_jogos_b = st.number_input("Jogos temporada", 1, 38, 10, key="n_b")
        fg_b = calcular_fg(dados_fg_b, medias_liga, n_jogos_b)
        st.metric("FG", f"{fg_b:.1f}")
        st.progress(int(fg_b))

    with st.expander("🏆 CPP", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            pts_cpp_b = st.number_input("Pontos", 0, 30, 4, key="pcpp_b")
        with c2:
            jogos_cpp_b = st.number_input("Jogos", 0, 10, 2, key="jcpp_b")
        cpp_b = calcular_cpp(pts_cpp_b, jogos_cpp_b, odd_b)
        st.metric("CPP", f"{cpp_b:.1f}")

    with st.expander("🎨 Estilo", expanded=False):
        st.markdown("**Indicadores (deixe 0 se não disponível)**")
        c1, c2 = st.columns(2)
        with c1:
            posse_est_b = st.slider("Posse (%)", 0, 100, 48, key="posse_est_b")
            ppda_b = st.number_input("PPDA", 0.0, 20.0, 0.0, key="ppda_b")
        with c2:
            trans_b = st.number_input("Chutes transição", 0.0, 10.0, 0.0, key="trans_b")
        dados_estilo_b = {}
        if posse_est_b > 0: dados_estilo_b['posse'] = posse_est_b
        if ppda_b > 0: dados_estilo_b['ppda'] = ppda_b
        if trans_b > 0: dados_estilo_b['chutes_trans'] = trans_b
        vetor_estilo_b = calcular_vetor_estilo(dados_estilo_b, medias_liga, n_jogos_b)
        st.write(vetor_estilo_b)

    with st.expander("🧠 Psicológico", expanded=False):
        cons_b = st.text_input("Últimos 10 resultados", "DDVVEDDVV", key="cons_b").upper()
        pts_cons_b, _, _ = calcular_pontos_e_resultados(list(cons_b))
        moral_b = st.slider("Moral (pts 3 jogos)", 0, 9, 3, key="moral_b")
        p_obj_b = st.slider("Pressão", 0, 100, 60, key="pobj_b")
        sens_b = st.slider("Sensibilidade", -1.0, 1.0, -0.3, 0.1, key="sens_b")
        psic_b = calcular_psicologico(consistencia_pontos=pts_cons_b, moral_pontos=moral_b,
                                      pressao_p_obj=p_obj_b, pressao_sensibilidade=sens_b)
        st.metric("Psicológico", f"{psic_b:.1f}")

    prateleira_b = st.selectbox("Prateleira", ["Elite", "Alta", "Média", "Baixa", "Crítico"], key="prat_b")
    prat_b_num = prat_map[prateleira_b]

# ==================== ESTILO CRUZADO ====================
estilo_a = calcular_estilo(dados_estilo_a, medias_liga, n_jogos_a, vetor_estilo_b) if vetor_estilo_b else 50.0
estilo_b = calcular_estilo(dados_estilo_b, medias_liga, n_jogos_b, vetor_estilo_a) if vetor_estilo_a else 50.0

# ==================== RESULTADOS ====================
st.header("📊 RESULTADOS DO CONFRONTO")

colunas = st.columns(5)
pilares = ['MA', 'FG', 'CPP', 'Estilo', 'Psicológico']
valores_a = [ma_a, fg_a, cpp_a, estilo_a, psic_a]
valores_b = [ma_b, fg_b, cpp_b, estilo_b, psic_b]

for i, pilar in enumerate(pilares):
    with colunas[i]:
        st.metric(pilar, f"{valores_a[i]:.1f}", delta=f"{valores_a[i]-valores_b[i]:.1f} vs {nome_b}")
        st.progress(int(valores_a[i]))

radar_df = pd.DataFrame({
    'Pilar': pilares * 2,
    'Valor': valores_a + valores_b,
    'Time': [nome_a]*5 + [nome_b]*5
})
radar_chart = alt.Chart(radar_df).mark_bar().encode(
    x=alt.X('Pilar:N', axis=alt.Axis(title=None)),
    y=alt.Y('Valor:Q', scale=alt.Scale(domain=[0, 100])),
    color=alt.Color('Time:N', scale=alt.Scale(range=['#FFD700', '#B8860B'])),
    column=alt.Column('Time:N', title=None)
).properties(width=150, height=300)
st.altair_chart(radar_chart, use_container_width=True)

st.header("⚡ ENGRAMS CORE")
ec = calcular_engramscore(
    ma_a=ma_a, fg_a=fg_a, cpp_a=cpp_a, estilo_a=estilo_a, psicologico_a=psic_a,
    ma_b=ma_b, fg_b=fg_b, cpp_b=cpp_b, estilo_b=estilo_b, psicologico_b=psic_b,
    time_mandante='A'
)

col_ec1, col_ec2 = st.columns(2)
col_ec1.markdown(f"<h2 style='text-align:center; color:#FFD700;'>{nome_a}</h2>", unsafe_allow_html=True)
col_ec1.markdown(f"<h1 style='text-align:center; color:#FFD700;'>{ec['EC_A']:.1f}</h1>", unsafe_allow_html=True)
col_ec1.progress(int(ec['EC_A']))
col_ec2.markdown(f"<h2 style='text-align:center; color:#FFD700;'>{nome_b}</h2>", unsafe_allow_html=True)
col_ec2.markdown(f"<h1 style='text-align:center; color:#FFD700;'>{ec['EC_B']:.1f}</h1>", unsafe_allow_html=True)
col_ec2.progress(int(ec['EC_B']))

st.subheader("Probabilidades 1X2")
p_df = pd.DataFrame({
    'Resultado': [f'Vitória {nome_a}', 'Empate', f'Vitória {nome_b}'],
    'Probabilidade': [ec['P_A'], ec['P_E'], ec['P_B']]
})
st.bar_chart(p_df.set_index('Resultado'))

st.header("⚽ MERCADO DE GOLS")
odd_over25 = st.number_input("Odd Over 2.5", 1.01, 10.0, 1.90, 0.01, key="odd_over")
n_jogos_mercado = st.number_input("Jogos temporada (peso dinâmico)", 1, 38, n_jogos_a, key="n_mercado")
fg_dict_a = {'ataque': fg_a, 'defesa': fg_a, 'meio': fg_a}
fg_dict_b = {'ataque': fg_b, 'defesa': fg_b, 'meio': fg_b}
psic_dict_a = {'moral': moral_a, 'pressao_obj': p_obj_a, 'sensibilidade': sens_a}
psic_dict_b = {'moral': moral_b, 'pressao_obj': p_obj_b, 'sensibilidade': sens_b}

gols = calcular_mercado_gols(
    gols_marcados_a=gm_a, gols_sofridos_a=gs_a,
    gols_marcados_b=gm_b, gols_sofridos_b=gs_b,
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
col_g4, col_g5, _ = st.columns([1,1,2])
col_g4.metric("BTTS Sim", f"{gols['btts_yes']:.2%}")
col_g5.metric("BTTS Não", f"{gols['btts_no']:.2%}")

st.caption(f"λ modelo: {gols['lambda_modelo']:.3f} | λ mercado: {gols['lambda_mercado']:.3f} | λ final: {gols['lambda_final']:.3f}")
