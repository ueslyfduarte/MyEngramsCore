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
from src.metricas.estilo import calcular_vetor_estilo, calcular_estilo, INDICADORES_ESTILO
from src.metricas.psicologico import calcular_psicologico
from src.mercados.gols import calcular_mercado_gols

# ==================== ENGRAMS CORE (incorporado) ====================
PESOS_PADRAO = {
    'MA': 0.20,
    'FG': 0.25,
    'CPP': 0.20,
    'Estilo': 0.20,
    'Psicologico': 0.15,
}
THR_MANDANTE = 10
THR_VISITANTE = 8

def _redistribuir_pesos(pilares_disponiveis: Dict[str, Optional[float]],
                        pesos: Dict[str, float]) -> Dict[str, float]:
    ativos = {k: v for k, v in pilares_disponiveis.items() if v is not None}
    if not ativos:
        return {}
    peso_total = sum(pesos.get(k, 0.0) for k in ativos)
    if peso_total == 0:
        n = len(ativos)
        return {k: 1.0/n for k in ativos}
    return {k: pesos.get(k, 0.0)/peso_total for k in ativos}

def _aplicar_fator_casa(ma_casa: float, ma_fora: float,
                        thr_casa: float = THR_MANDANTE,
                        thr_fora: float = THR_VISITANTE) -> Tuple[float, float]:
    diff_casa = ma_casa - ma_fora
    diff_fora = ma_fora - ma_casa
    if diff_casa >= thr_casa:
        return 1.0, 0.0
    elif diff_fora >= thr_fora:
        return 0.0, 1.0
    else:
        return 0.0, 0.0

def calcular_engramscore(
    ma_a: Optional[float] = None, fg_a: Optional[float] = None,
    cpp_a: Optional[float] = None, estilo_a: Optional[float] = None,
    psicologico_a: Optional[float] = None,
    ma_b: Optional[float] = None, fg_b: Optional[float] = None,
    cpp_b: Optional[float] = None, estilo_b: Optional[float] = None,
    psicologico_b: Optional[float] = None,
    time_mandante: str = 'A',
    pesos: Dict[str, float] = None,
    thr_mandante: float = THR_MANDANTE,
    thr_visitante: float = THR_VISITANTE,
) -> Dict[str, float]:
    if pesos is None:
        pesos = PESOS_PADRAO.copy()

    pilares_a = {
        'MA': ma_a, 'FG': fg_a, 'CPP': cpp_a,
        'Estilo': estilo_a, 'Psicologico': psicologico_a,
    }
    pilares_b = {
        'MA': ma_b, 'FG': fg_b, 'CPP': cpp_b,
        'Estilo': estilo_b, 'Psicologico': psicologico_b,
    }

    ativos_ambos = {}
    for pilar in ['MA', 'FG', 'CPP', 'Estilo', 'Psicologico']:
        if pilares_a[pilar] is not None and pilares_b[pilar] is not None:
            ativos_ambos[pilar] = True

    if not ativos_ambos:
        return {
            'EC_A': 50.0, 'EC_B': 50.0,
            'P_A': 0.333, 'P_B': 0.333, 'P_E': 0.334,
            'P_A_ou_E': 0.667, 'P_B_ou_E': 0.667,
        }

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

    ec_a += bonus_a
    ec_b += bonus_b
    ec_a = max(0.0, min(100.0, ec_a))
    ec_b = max(0.0, min(100.0, ec_b))

    soma = ec_a + ec_b
    if soma == 0:
        p_a = p_b = 0.333
        p_e = 0.334
    else:
        p_a = ec_a / soma
        p_b = ec_b / soma
        p_e = 1.0 - p_a - p_b
        if p_e < 0:
            p_e = 0.0
            total = p_a + p_b
            if total > 0:
                p_a /= total
                p_b /= total

    return {
        'EC_A': round(ec_a, 2),
        'EC_B': round(ec_b, 2),
        'P_A': round(p_a, 4),
        'P_B': round(p_b, 4),
        'P_E': round(p_e, 4),
        'P_A_ou_E': round(p_a + p_e, 4),
        'P_B_ou_E': round(p_b + p_e, 4),
    }

# ==================== FUNÇÕES DE DESCRIÇÃO TEXTUAL ====================
def descrever_fg(valor, nome_time):
    if valor >= 70: return f"{nome_time} apresenta uma **Força Geral muito acima da média** ({valor:.0f})."
    elif valor >= 55: return f"{nome_time} tem uma **Força Geral acima da média** ({valor:.0f})."
    elif valor >= 45: return f"{nome_time} está com uma **Força Geral dentro da média** ({valor:.0f})."
    else: return f"{nome_time} mostra uma **Força Geral abaixo da média** ({valor:.0f})."

def descrever_estilo(vetor, nome):
    if not vetor: return ""
    dim_max = max(vetor, key=lambda k: vetor[k] if vetor[k] is not None else 0)
    valor_max = vetor[dim_max]
    nomes = {
        'posse': 'Posse/Paciência',
        'pressao_alta': 'Pressão Alta',
        'contra_ataque': 'Contra-ataque',
        'jogo_laterais': 'Jogo pelas Laterais',
        'jogo_meio': 'Jogo pelo Meio',
        'transicao_rapida': 'Transição Rápida',
        'defesa_bloco_baixo': 'Defesa em Bloco Baixo',
        'pressao_pos_perda': 'Pressão Pós-Perda'
    }
    nome_dim = nomes.get(dim_max, dim_max)
    return f"{nome} se destaca no estilo **{nome_dim}** ({valor_max:.0f}/100)."

# ==================== INTERFACE STREAMLIT ====================
st.set_page_config(page_title="EngramsCore ⚽", page_icon="⚽", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0a0a0a; color: #FFD700; }
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
    .card {
        background: #1a1a1a; border: 1px solid #FFD700; border-radius: 10px;
        padding: 15px; margin-bottom: 15px; box-shadow: 0px 0px 15px rgba(255,215,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

st.title("⚽ ENGRAMS CORE")
st.markdown("<p style='color:#FFD700; font-size:1.2em;'>Sistema de Análise Esportiva Diferencial</p>", unsafe_allow_html=True)

# ==================== ABA DE ENTRADA DE DADOS ====================
st.header("📝 Dados do Confronto")

col_a, col_liga, col_b = st.columns(3)

with col_a:
    st.subheader("🏠 Time A (Mandante)")
    nome_a = st.text_input("Nome", "Time A", key="nome_a")
    # MA
    with st.expander("📈 Momento Atual (MA)", expanded=False):
        odd_a = st.number_input("Odd Vitória", 1.01, 10.0, 1.80, 0.01, key="odd_a")
        res_a = st.text_input("Últ. resultados (V/E/D)", "VVEDV", key="res_a").upper()
    # FG
    with st.expander("💪 Força Geral (FG)", expanded=False):
        gm_a = st.number_input("Gols/jogo", 0.0, 5.0, 2.0, 0.1, key="gm_a")
        fa_a = st.number_input("Finalizações/jogo", 0.0, 10.0, 4.5, 0.1, key="fa_a")
        gs_a = st.number_input("Gols sofridos/jogo", 0.0, 5.0, 0.8, 0.1, key="gs_a")
        xga_a = st.number_input("xG contra", 0.0, 5.0, 0.9, 0.1, key="xga_a")
        posse_a = st.slider("Posse %", 0, 100, 55, key="posse_a")
    # CPP
    with st.expander("🏆 Confronto por Prateleira (CPP)", expanded=False):
        pts_cpp_a = st.number_input("Pontos", 0, 30, 6, key="pcpp_a")
        jogos_cpp_a = st.number_input("Jogos", 0, 10, 3, key="jcpp_a")
    # Estilo
    with st.expander("🎨 Estilo de Jogo", expanded=False):
        dados_estilo_a_input = {}
        for dim, indicadores in INDICADORES_ESTILO.items():
            st.markdown(f"**{dim.replace('_', ' ').title()}**")
            for nome_tecnico, chave in indicadores.items():
                val = st.number_input(f"{nome_tecnico}", value=0.0, step=0.1, key=f"a_{chave}")
                if val > 0:
                    dados_estilo_a_input[chave] = val
    # Psicológico
    with st.expander("🧠 Psicológico", expanded=False):
        cons_a = st.text_input("Últ. 10 resultados", "VVEDVVEDVV", key="cons_a").upper()
        moral_a = st.slider("Moral (pts 3j)", 0, 9, 6, key="moral_a")
        p_obj_a = st.slider("Pressão", 0, 100, 40, key="pobj_a")
        sens_a = st.slider("Sensibilidade", -1.0, 1.0, 0.0, 0.1, key="sens_a")
    prat_a = st.selectbox("Prateleira", ["Elite","Alta","Média","Baixa","Crítico"], key="prat_a")
    n_jogos_a = st.number_input("Jogos temporada", 1, 38, 10, key="nj_a")

with col_liga:
    st.subheader("📊 Liga (Referências)")
    medias_liga = {}
    # FG
    with st.expander("💪 Força Geral", expanded=False):
        medias_liga['GM'] = st.number_input("Média Gols/jogo", 0.1, 5.0, 1.4, 0.1, key="l_fg_gm")
        medias_liga['FA'] = st.number_input("Média Finalizações/j", 0.1, 10.0, 4.0, 0.1, key="l_fg_fa")
        medias_liga['GS'] = st.number_input("Média Gols sofridos/j", 0.1, 5.0, 1.4, 0.1, key="l_fg_gs")
        medias_liga['xGA'] = st.number_input("Média xG contra", 0.1, 5.0, 1.4, 0.1, key="l_fg_xga")
        medias_liga['Posse'] = st.number_input("Média Posse %", 0.0, 100.0, 50.0, 1.0, key="l_fg_posse")
    # Estilo
    with st.expander("🎨 Estilo", expanded=False):
        for dim, indicadores in INDICADORES_ESTILO.items():
            st.markdown(f"**{dim.replace('_', ' ').title()}**")
            for nome_tecnico, chave in indicadores.items():
                medias_liga[chave] = st.number_input(f"Média {nome_tecnico}", value=0.0, step=0.1, key=f"l_est_{chave}")
    # Estilo
    with st.expander("🎨 Estilo", expanded=False):
        for dim, indicadores in INDICADORES_ESTILO.items():
            st.markdown(f"**{dim.replace('_', ' ').title()}**")
            for nome_tecnico, chave in indicadores.items():
                medias_liga[chave] = st.number_input(f"Média {nome_tecnico}", value=0.0, step=0.1, key=f"l_{chave}")

with col_b:
    st.subheader("✈️ Time B (Visitante)")
    nome_b = st.text_input("Nome", "Time B", key="nome_b")
    # MA
    with st.expander("📈 Momento Atual (MA)", expanded=False):
        odd_b = st.number_input("Odd Vitória", 1.01, 10.0, 4.00, 0.01, key="odd_b")
        res_b = st.text_input("Últ. resultados (V/E/D)", "DDVVE", key="res_b").upper()
    # FG
    with st.expander("💪 Força Geral (FG)", expanded=False):
        gm_b = st.number_input("Gols/jogo", 0.0, 5.0, 1.2, 0.1, key="gm_b")
        fa_b = st.number_input("Finalizações/jogo", 0.0, 10.0, 3.2, 0.1, key="fa_b")
        gs_b = st.number_input("Gols sofridos/jogo", 0.0, 5.0, 1.5, 0.1, key="gs_b")
        xga_b = st.number_input("xG contra", 0.0, 5.0, 1.4, 0.1, key="xga_b")
        posse_b = st.slider("Posse %", 0, 100, 48, key="posse_b")
    # CPP
    with st.expander("🏆 Confronto por Prateleira (CPP)", expanded=False):
        pts_cpp_b = st.number_input("Pontos", 0, 30, 4, key="pcpp_b")
        jogos_cpp_b = st.number_input("Jogos", 0, 10, 2, key="jcpp_b")
    # Estilo
    with st.expander("🎨 Estilo de Jogo", expanded=False):
        dados_estilo_b_input = {}
        for dim, indicadores in INDICADORES_ESTILO.items():
            st.markdown(f"**{dim.replace('_', ' ').title()}**")
            for nome_tecnico, chave in indicadores.items():
                val = st.number_input(f"{nome_tecnico}", value=0.0, step=0.1, key=f"b_{chave}")
                if val > 0:
                    dados_estilo_b_input[chave] = val
    # Psicológico
    with st.expander("🧠 Psicológico", expanded=False):
        cons_b = st.text_input("Últ. 10 resultados", "DDVVEDDVV", key="cons_b").upper()
        moral_b = st.slider("Moral (pts 3j)", 0, 9, 3, key="moral_b")
        p_obj_b = st.slider("Pressão", 0, 100, 60, key="pobj_b")
        sens_b = st.slider("Sensibilidade", -1.0, 1.0, -0.3, 0.1, key="sens_b")
    prat_b = st.selectbox("Prateleira", ["Elite","Alta","Média","Baixa","Crítico"], key="prat_b")
    n_jogos_b = st.number_input("Jogos temporada", 1, 38, 10, key="nj_b")

# Botão
st.markdown("---")
gerar = st.button("⚡ Gerar Engrama", type="primary")

# ==================== RESULTADOS ====================
if gerar:
    # Processar MA
    _, v_a, d_a = calcular_pontos_e_resultados(list(res_a))
    ma_a = calcular_ma(sum(3 if c=='V' else 1 if c=='E' else 0 for c in res_a), v_a, d_a, odd_a)
    _, v_b, d_b = calcular_pontos_e_resultados(list(res_b))
    ma_b = calcular_ma(sum(3 if c=='V' else 1 if c=='E' else 0 for c in res_b), v_b, d_b, odd_b)

    # FG
    dados_fg_a = {'GM': gm_a, 'FA': fa_a, 'GS': gs_a, 'xGA': xga_a, 'Posse': posse_a}
    dados_fg_a = {k:v for k,v in dados_fg_a.items() if v != 0.0}
    dados_fg_b = {'GM': gm_b, 'FA': fa_b, 'GS': gs_b, 'xGA': xga_b, 'Posse': posse_b}
    dados_fg_b = {k:v for k,v in dados_fg_b.items() if v != 0.0}
    fg_a = calcular_fg(dados_fg_a, medias_liga, n_jogos_a)
    fg_b = calcular_fg(dados_fg_b, medias_liga, n_jogos_b)

    # CPP
    cpp_a = calcular_cpp(pts_cpp_a, jogos_cpp_a, odd_a)
    cpp_b = calcular_cpp(pts_cpp_b, jogos_cpp_b, odd_b)

    # Estilo
    vetor_a = calcular_vetor_estilo(dados_estilo_a_input, medias_liga, n_jogos_a)
    vetor_b = calcular_vetor_estilo(dados_estilo_b_input, medias_liga, n_jogos_b)
    estilo_a = calcular_estilo(dados_estilo_a_input, medias_liga, n_jogos_a, vetor_b) if vetor_b else 50.0
    estilo_b = calcular_estilo(dados_estilo_b_input, medias_liga, n_jogos_b, vetor_a) if vetor_a else 50.0

    # Psicológico
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

    # EngramsCore
    ec = calcular_engramscore(
        ma_a=ma_a, fg_a=fg_a, cpp_a=cpp_a, estilo_a=estilo_a, psicologico_a=psic_a,
        ma_b=ma_b, fg_b=fg_b, cpp_b=cpp_b, estilo_b=estilo_b, psicologico_b=psic_b,
        time_mandante='A'
    )

    # ============ EXIBIÇÃO DOS RESULTADOS ============
    st.header("📊 Resultados da Análise")

    # Cards dos pilares
    pilares = ['MA', 'FG', 'CPP', 'Estilo', 'Psicológico']
    vals_a = [ma_a, fg_a, cpp_a, estilo_a, psic_a]
    vals_b = [ma_b, fg_b, cpp_b, estilo_b, psic_b]

    colunas = st.columns(5)
    for i, p in enumerate(pilares):
        with colunas[i]:
            st.metric(p, f"{vals_a[i]:.0f}", delta=f"{vals_a[i]-vals_b[i]:.0f} vs {nome_b}")
            st.progress(int(vals_a[i]))

    # Gráfico radar
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(r=vals_a, theta=pilares, fill='toself', name=nome_a, marker=dict(color='#FFD700')))
    fig_radar.add_trace(go.Scatterpolar(r=vals_b, theta=pilares, fill='toself', name=nome_b, marker=dict(color='#B8860B')))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,100])), showlegend=True, template='plotly_dark')
    st.plotly_chart(fig_radar, use_container_width=True)

    # Estilos
    st.subheader("🎨 Estilos de Jogo")
    col_est1, col_est2 = st.columns(2)
    with col_est1:
        st.markdown(f"**{nome_a}**")
        if vetor_a:
            dims = list(vetor_a.keys())
            vals_dim_a = [vetor_a[d] if vetor_a[d] is not None else 0 for d in dims]
            max_dim_a = dims[vals_dim_a.index(max(vals_dim_a))]
            st.markdown(f"🔷 **Ênfase principal:** {max_dim_a.replace('_',' ').title()} ({max(vals_dim_a):.0f})")
            fig_bar_a = px.bar(x=vals_dim_a, y=dims, orientation='h',
                               color=[1 if d==max_dim_a else 0 for d in dims],
                               color_continuous_scale=['#B8860B','#FFD700'])
            fig_bar_a.update_layout(template='plotly_dark', showlegend=False, height=300)
            st.plotly_chart(fig_bar_a, use_container_width=True)
            st.markdown(descrever_estilo(vetor_a, nome_a))
        else:
            st.info("Nenhum dado de estilo fornecido.")

    with col_est2:
        st.markdown(f"**{nome_b}**")
        if vetor_b:
            dims = list(vetor_b.keys())
            vals_dim_b = [vetor_b[d] if vetor_b[d] is not None else 0 for d in dims]
            max_dim_b = dims[vals_dim_b.index(max(vals_dim_b))]
            st.markdown(f"🔷 **Ênfase principal:** {max_dim_b.replace('_',' ').title()} ({max(vals_dim_b):.0f})")
            fig_bar_b = px.bar(x=vals_dim_b, y=dims, orientation='h',
                               color=[1 if d==max_dim_b else 0 for d in dims],
                               color_continuous_scale=['#B8860B','#FFD700'])
            fig_bar_b.update_layout(template='plotly_dark', showlegend=False, height=300)
            st.plotly_chart(fig_bar_b, use_container_width=True)
            st.markdown(descrever_estilo(vetor_b, nome_b))
        else:
            st.info("Nenhum dado de estilo fornecido.")

    # EngramsCore
    st.header("⚡ EngramsCore")
    col_ec1, col_ec2 = st.columns(2)
    with col_ec1:
        st.markdown(f"<h2 style='text-align:center;color:#FFD700;'>{nome_a}</h2>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align:center;color:#FFD700;'>{ec['EC_A']:.1f}</h1>", unsafe_allow_html=True)
        st.progress(int(ec['EC_A']))
    with col_ec2:
        st.markdown(f"<h2 style='text-align:center;color:#FFD700;'>{nome_b}</h2>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align:center;color:#FFD700;'>{ec['EC_B']:.1f}</h1>", unsafe_allow_html=True)
        st.progress(int(ec['EC_B']))

    # Probabilidades
    st.subheader("Probabilidades 1X2")
    prob_df = pd.DataFrame({
        'Resultado': [f'Vitória {nome_a}', 'Empate', f'Vitória {nome_b}'],
        'Probabilidade': [ec['P_A'], ec['P_E'], ec['P_B']]
    })
    fig_prob = px.bar(prob_df, x='Resultado', y='Probabilidade',
                      color='Resultado', color_discrete_sequence=['#FFD700','#B8860B','#8B7500'])
    st.plotly_chart(fig_prob, use_container_width=True)
    st.write(f"Dupla {nome_a} ou Empate: {ec['P_A_ou_E']:.2%}  |  Dupla {nome_b} ou Empate: {ec['P_B_ou_E']:.2%}")

    # Descrições textuais
    st.subheader("📝 Análise Descritiva")
    desc_a = [descrever_fg(fg_a, nome_a)]
    if vetor_a: desc_a.append(descrever_estilo(vetor_a, nome_a))
    st.markdown(" ".join(desc_a))
    desc_b = [descrever_fg(fg_b, nome_b)]
    if vetor_b: desc_b.append(descrever_estilo(vetor_b, nome_b))
    st.markdown(" ".join(desc_b))

    # Mercado de Gols
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
