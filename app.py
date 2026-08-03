import sys
import importlib.util
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
INTERFACE_DIR = SRC_DIR / "interface"

sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(SRC_DIR))

import streamlit as st

def carregar_modulo(nome_arquivo, nome_modulo):
    caminho = INTERFACE_DIR / nome_arquivo
    try:
        spec = importlib.util.spec_from_file_location(nome_modulo, caminho)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo
    except Exception as e:
        st.error(f"Erro ao carregar {nome_arquivo}: {e}")
        return None

css = carregar_modulo("css.py", "css")
sidebar = carregar_modulo("sidebar.py", "sidebar")
entrada_fbref = carregar_modulo("entrada_fbref.py", "entrada_fbref")
entrada_manual = carregar_modulo("entrada_manual.py", "entrada_manual")
odds = carregar_modulo("odds.py", "odds")
resultados = carregar_modulo("resultados.py", "resultados")

if not all([css, sidebar, entrada_fbref, entrada_manual, odds, resultados]):
    st.stop()

st.set_page_config(page_title="EngramScore ⚽", page_icon="⚽", layout="wide")
css.carregar_css()
css.renderizar_header()
sidebar.renderizar_sidebar()

if "jogo_selecionado" in st.session_state:
    jogo = st.session_state["jogo_selecionado"]
    st.markdown(f"<h2>{jogo['casa']} vs {jogo['fora']}</h2>", unsafe_allow_html=True)
    if st.button("🔄 Nova análise"):
        del st.session_state["jogo_selecionado"]
        st.rerun()
else:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    modo = st.radio("Modo:", ["📋 Colar do FBref", "✏️ Manual"], horizontal=True)
    dados = entrada_fbref.renderizar_modo_fbref() if modo == "📋 Colar do FBref" else entrada_manual.renderizar_modo_manual()
    odds_data = odds.renderizar_odds()
    if dados:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚡ GERAR ENGRAMSCORE", type="primary", use_container_width=True):
            resultados.renderizar_resultados(dados, odds_data)

css.renderizar_rodape()
