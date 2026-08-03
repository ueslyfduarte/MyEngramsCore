"""
Sidebar — EngramScore
Barra lateral com jogos pendentes e análises do dia.
"""

import streamlit as st
import pandas as pd
import os

ARQUIVO_PENDENTES = "dados/jogos_pendentes.csv"
ARQUIVO_ANALISES = "dados/analises_prontas.csv"

LIGAS_DISPONIVEIS = [
    "brasileirao_serie_a", "brasileirao_serie_b", "premier_league",
    "la_liga", "bundesliga", "serie_a", "ligue_1", "mls", "liga_mx",
    "primera_division_argentina", "championship", "eredivisie",
    "liga_portugal", "super_lig_turquia", "jupiler_pro_league",
    "superliga_grecia", "russian_premier_league", "austrian_bundesliga",
    "super_liga_suica", "superliga_dinamarca", "allsvenskan",
    "eliteserien", "czech_first_league", "ekstraklasa",
    "liga_1_romenia", "ukrainian_premier_league", "scottish_premiership",
    "croatian_hnl", "primera_division_uruguai", "primera_division_chile",
    "primera_a_equador", "primera_division_paraguai", "primera_division_peru",
    "categoria_primera_a", "primera_division_venezuela", "j1_league",
    "k_league_1", "saudi_pro_league", "a_league", "egyptian_premier_league",
    "superettan", "liga_1_indonesia", "indian_super_league",
    "liga_nacional_honduras", "liga_fpf"
]


def carregar_pendentes():
    """Carrega a lista de jogos pendentes do CSV."""
    if os.path.exists(ARQUIVO_PENDENTES):
        return pd.read_csv(ARQUIVO_PENDENTES)
    return pd.DataFrame(columns=["casa", "fora", "liga"])


def salvar_pendentes(df):
    """Salva a lista de jogos pendentes no CSV."""
    df.to_csv(ARQUIVO_PENDENTES, index=False)


def carregar_analises():
    """Carrega as análises prontas do CSV."""
    if os.path.exists(ARQUIVO_ANALISES):
        return pd.read_csv(ARQUIVO_ANALISES)
    return None


def renderizar_sidebar():
    """Renderiza toda a barra lateral."""
    st.markdown("## 📋 Jogos Pendentes")
    st.markdown("*Adicione jogos para análise futura.*")

    df_pendentes = carregar_pendentes()

    # Adicionar novo jogo
    col_add1, col_add2 = st.columns(2)
    with col_add1:
        novo_casa = st.text_input("Casa", key="pend_casa", placeholder="Palmeiras")
    with col_add2:
        novo_fora = st.text_input("Fora", key="pend_fora", placeholder="Vasco")

    nova_liga = st.selectbox("Liga", LIGAS_DISPONIVEIS, key="pend_liga")

    if st.button("➕ Adicionar"):
        if novo_casa and novo_fora:
            novo = pd.DataFrame({
                "casa": [novo_casa],
                "fora": [novo_fora],
                "liga": [nova_liga]
            })
            df_pendentes = pd.concat([df_pendentes, novo], ignore_index=True)
            salvar_pendentes(df_pendentes)
            st.success(f"{novo_casa} x {novo_fora} adicionado!")
            st.rerun()

    # Listar jogos pendentes
    if not df_pendentes.empty:
        st.markdown("---")
        for idx, row in df_pendentes.iterrows():
            col_j, col_r = st.columns([4, 1])
            with col_j:
                st.markdown(f"• {row['casa']} x {row['fora']}")
            with col_r:
                if st.button("🗑️", key=f"rem_{idx}"):
                    df_pendentes = df_pendentes.drop(idx).reset_index(drop=True)
                    salvar_pendentes(df_pendentes)
                    st.rerun()

    # Análises do dia
    st.markdown("---")
    st.markdown("## 📊 Análises do Dia")

    df_analises = carregar_analises()

    if df_analises is not None and not df_analises.empty:
        st.success(f"✅ {len(df_analises)} análises disponíveis")
        for idx, row in df_analises.iterrows():
            if st.button(f"📊 {row['casa']} x {row['fora']}", key=f"ana_{idx}"):
                st.session_state["jogo_selecionado"] = {
                    "casa": row["casa"],
                    "fora": row["fora"],
                    "EC_A": row["EC_A"],
                    "EC_B": row["EC_B"],
                    "p_A": row["p_A"],
                    "p_emp": row["p_emp"],
                    "p_B": row["p_B"],
                    "resultado_previsto": row.get("resultado_previsto", ""),
                }
                st.rerun()
    else:
        st.info("Nenhuma análise pronta ainda.")
