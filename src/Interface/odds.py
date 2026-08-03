"""
Odds — EngramScore
Entrada de odds de mercado (1X2, Over/Under, BTTS, Gol 1º Tempo).
"""

import streamlit as st


def renderizar_odds():
    """
    Renderiza os campos de entrada de odds de mercado.
    Retorna um dicionário com todas as odds preenchidas.
    """
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("### 💰 Odds de Mercado")

    # 1X2
    st.markdown("**1X2**")
    col_odd1, col_odd2, col_odd3 = st.columns(3)
    with col_odd1:
        odd_casa = st.number_input("🏠 Vitória Casa", 1.01, 10.0, 1.80, 0.01, key="odd_casa")
    with col_odd2:
        odd_empate = st.number_input("🤝 Empate", 1.01, 10.0, 3.50, 0.01, key="odd_empate")
    with col_odd3:
        odd_fora = st.number_input("✈️ Vitória Fora", 1.01, 10.0, 4.00, 0.01, key="odd_fora")

    # Gols Totais
    st.markdown("**Gols Totais**")
    col_g1, col_g2, col_g3 = st.columns(3)
    with col_g1:
        odd_over15 = st.number_input("Over 1.5", 1.01, 20.0, value=None, step=0.01, format="%.2f", key="odd_over15")
    with col_g2:
        odd_over25 = st.number_input("Over 2.5", 1.01, 20.0, value=None, step=0.01, format="%.2f", key="odd_over25")
    with col_g3:
        odd_over35 = st.number_input("Over 3.5", 1.01, 20.0, value=None, step=0.01, format="%.2f", key="odd_over35")

    # Ambos Marcam (BTTS)
    st.markdown("**Ambos Marcam (BTTS)**")
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        odd_btts_sim = st.number_input("BTTS Sim", 1.01, 20.0, value=None, step=0.01, format="%.2f", key="odd_btts_sim")
    with col_b2:
        odd_btts_nao = st.number_input("BTTS Não", 1.01, 20.0, value=None, step=0.01, format="%.2f", key="odd_btts_nao")

    # Gol 1º Tempo
    st.markdown("**Gol 1º Tempo**")
    odd_ht = st.number_input("Gol 1º Tempo (Sim)", 1.01, 20.0, value=None, step=0.01, format="%.2f", key="odd_ht")

    return {
        "odd_casa": odd_casa,
        "odd_empate": odd_empate,
        "odd_fora": odd_fora,
        "odd_over15": odd_over15,
        "odd_over25": odd_over25,
        "odd_over35": odd_over35,
        "odd_btts_sim": odd_btts_sim,
        "odd_btts_nao": odd_btts_nao,
        "odd_ht": odd_ht,
    }
