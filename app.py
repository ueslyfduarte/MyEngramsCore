"""
app.py — EngramScore
Sistema de análise esportiva com três modos de entrada:
- Manual (digitação)
- Híbrido (colagem de tabelas FBref/WhoScored)
- Automático (API‑Football + FBref + Understat)
"""

import sys
import importlib.util
from pathlib import Path
from datetime import datetime

import streamlit as st

# ✅ PRIMEIRA CHAMADA STREAMLIT
st.set_page_config(page_title="EngramScore ⚽", page_icon="⚽", layout="wide")

# Configuração de caminhos
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
INTERFACE_DIR = SRC_DIR / "Interface"

sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(SRC_DIR))


def carregar_modulo(nome_arquivo, nome_modulo):
    """Carrega um módulo Python a partir do caminho absoluto."""
    caminho = INTERFACE_DIR / nome_arquivo
    if not caminho.exists():
        st.error(f"❌ Arquivo não encontrado: {caminho}")
        st.stop()
    try:
        spec = importlib.util.spec_from_file_location(nome_modulo, caminho)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo
    except Exception as e:
        st.error(f"❌ Erro ao carregar {nome_arquivo}: {e}")
        st.stop()


# Carregar módulos da interface
css = carregar_modulo("css.py", "css")
sidebar = carregar_modulo("sidebar.py", "sidebar")
entrada_hibrida = carregar_modulo("entrada_hibrida.py", "entrada_hibrida")
entrada_manual = carregar_modulo("entrada_manual.py", "entrada_manual")
odds = carregar_modulo("odds.py", "odds")
resultados = carregar_modulo("resultados.py", "resultados")

# Carregar o novo data_loader (automático)
try:
    from src.data_loader import carregar_dados_automaticos, LIGAS_MAP
    AUTO_DISPONIVEL = True
except ImportError:
    AUTO_DISPONIVEL = False
    LIGAS_MAP = {}

# Renderizar interface fixa
css.carregar_css()
css.renderizar_header()
sidebar.renderizar_sidebar()

# ============================================================
# Seleção do modo de entrada
# ============================================================
modo = st.sidebar.radio(
    "Modo de entrada",
    ["Manual", "Híbrido (colar tabelas)", "Automático (dados reais)"]
)

dados = None
odds_data = None

# --- MODO AUTOMÁTICO ---
if modo == "Automático (dados reais)":
    if not AUTO_DISPONIVEL:
        st.error("❌ Módulo data_loader não encontrado. Verifique se src/data_loader.py existe.")
    else:
        st.markdown("### 🤖 Análise Automática")
        st.markdown("*Os dados serão obtidos de API‑Football, FBref e Understat.*")

        # Inicializar estado da sessão
        if "times_carregados" not in st.session_state:
            st.session_state.times_carregados = False
            st.session_state.lista_times = []
            st.session_state.liga_selecionada = ""

        # Seleção da liga (sem ação automática)
        lista_ligas = list(LIGAS_MAP.keys()) if LIGAS_MAP else ["Premier League"]
        col_liga, col_btn = st.columns([3, 1])
        with col_liga:
            liga = st.selectbox("Liga", lista_ligas, key="auto_liga")
        with col_btn:
            st.write("")  # espaço
            carregar_times_btn = st.button("📋 Carregar Times", use_container_width=True)

        # Se o botão foi pressionado OU se a liga mudou em relação à armazenada
        if carregar_times_btn or (liga != st.session_state.liga_selecionada and st.session_state.times_carregados == False):
            api_key = st.secrets.get("API_FOOTBALL_KEY", None)
            if not api_key:
                st.error("Configure a chave API_FOOTBALL_KEY nos secrets do Streamlit.")
            else:
                with st.spinner("Buscando times da liga..."):
                    try:
                        from src.data_loader import get_all_teams_from_league
                        info = LIGAS_MAP[liga]
                        season = datetime.now().year
                        times_dict = get_all_teams_from_league(info["api_id"], season, api_key)
                        st.session_state.lista_times = sorted(list(times_dict.keys()))
                        st.session_state.times_carregados = True
                        st.session_state.liga_selecionada = liga
                    except Exception as e:
                        st.error(f"❌ Erro ao carregar times: {e}")
                        st.session_state.times_carregados = False

        # Exibir as selectboxes somente se a lista estiver pronta
        if st.session_state.times_carregados:
            col1, col2 = st.columns(2)
            with col1:
                time_casa = st.selectbox("🏠 Time da casa", st.session_state.lista_times, key="auto_casa")
            with col2:
                time_fora = st.selectbox("✈️ Time visitante", st.session_state.lista_times, key="auto_fora")

            api_key = st.secrets.get("API_FOOTBALL_KEY", None)
            if st.button("🔍 Buscar dados", type="primary"):
                if not api_key:
                    st.error("Configure a chave API_FOOTBALL_KEY nos secrets do Streamlit.")
                elif time_casa == time_fora:
                    st.error("Escolha times diferentes para a análise.")
                else:
                    with st.spinner("Coletando dados das fontes oficiais..."):
                        try:
                            dados = carregar_dados_automaticos(
                                time_casa=time_casa,
                                time_fora=time_fora,
                                liga=liga,
                                api_key=api_key
                            )
                            st.success("✅ Dados coletados com sucesso!")
                            odds_data = {
                                "odd_casa": dados.get("odd_casa"),
                                "odd_empate": dados.get("odd_empate"),
                                "odd_fora": dados.get("odd_fora"),
                                "odd_over15": dados.get("odd_over15"),
                                "odd_over25": dados.get("odd_over25"),
                                "odd_over35": dados.get("odd_over35"),
                                "odd_btts_sim": dados.get("odd_btts_sim"),
                                "odd_btts_nao": dados.get("odd_btts_nao"),
                                "odd_ht": dados.get("odd_ht"),
                            }
                        except Exception as e:
                            st.error(f"❌ Falha na coleta: {e}")
        else:
            st.info("👆 Clique em **Carregar Times** para obter a lista de clubes da liga selecionada.")

# --- MODO HÍBRIDO (original) ---
elif modo == "Híbrido (colar tabelas)":
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(
        """<div style="text-align:center; margin-bottom:20px;">
        <span style="font-size:13px; text-transform:uppercase; letter-spacing:3px; color:#B0B8C0;">
        Dados do Confronto (Híbrido)
        </span></div>""",
        unsafe_allow_html=True
    )
    dados = entrada_hibrida.renderizar_modo_hibrido()
    odds_data = odds.renderizar_odds()

# --- MODO MANUAL ---
else:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(
        """<div style="text-align:center; margin-bottom:20px;">
        <span style="font-size:13px; text-transform:uppercase; letter-spacing:3px; color:#B0B8C0;">
        Dados do Confronto (Manual)
        </span></div>""",
        unsafe_allow_html=True
    )
    dados = entrada_manual.renderizar_modo_manual()
    odds_data = odds.renderizar_odds()

# ============================================================
# Botão de gerar análise (modos Manual e Híbrido)
# ============================================================
if dados is not None:
    # Se for modo automático, as odds já estão em odds_data
    if odds_data is None:
        # fallback: se por algum motivo não temos odds, pega valores padrão
        odds_data = {
            "odd_casa": 1.8, "odd_empate": 3.5, "odd_fora": 4.0,
            "odd_over15": 1.2, "odd_over25": 1.8, "odd_over35": 2.5,
            "odd_btts_sim": 1.8, "odd_btts_nao": 1.9, "odd_ht": 1.5
        }

    st.markdown("<br>", unsafe_allow_html=True)
    col_btn = st.columns([1, 2, 1])
    with col_btn[1]:
        gerar = st.button("⚡ GERAR ENGRAMSCORE", type="primary", use_container_width=True)

    if gerar:
        try:
            resultados.renderizar_resultados(dados, odds_data)
        except Exception as e:
            st.error(f"❌ Erro ao gerar resultados: {e}")
            st.error("Verifique se todos os dados foram preenchidos corretamente.")

# ============================================================
# Se houver jogo selecionado na sidebar (análises prontas)
# ============================================================
if "jogo_selecionado" in st.session_state:
    jogo = st.session_state["jogo_selecionado"]
    st.markdown(f"<h2>{jogo['casa']} vs {jogo['fora']}</h2>", unsafe_allow_html=True)
    st.info("📊 Análise do dia carregada.")
    if st.button("🔄 Nova análise"):
        del st.session_state["jogo_selecionado"]
        st.rerun()

css.renderizar_rodape()
