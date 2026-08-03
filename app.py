import streamlit as st
from src.ui.css import carregar_css
from src.ui.sidebar import renderizar_sidebar
from src.ui.entrada_fbref import renderizar_modo_fbref
from src.ui.entrada_manual import renderizar_modo_manual
from src.ui.odds import renderizar_odds
from src.ui.resultados import renderizar_resultados

# Configuração
st.set_page_config(page_title="EngramScore ⚽", page_icon="⚽", layout="wide")
carregar_css()

# Header
st.markdown("<h1>ENGRAMSCORE</h1>", unsafe_allow_html=True)

# Sidebar
renderizar_sidebar()

# Modo de entrada
modo = st.radio("Modo:", ["📋 Colar do FBref", "✏️ Manual"], horizontal=True)

if modo == "📋 Colar do FBref":
    dados = renderizar_modo_fbref()
else:
    dados = renderizar_modo_manual()

# Odds
odds = renderizar_odds()

# Botão e resultados
if st.button("⚡ GERAR ENGRAMSCORE"):
    renderizar_resultados(dados, odds)
