import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

# Interface
from src.interface.css import carregar_css, renderizar_header, renderizar_rodape
from src.interface.sidebar import renderizar_sidebar
from src.interface.entrada_fbref import renderizar_modo_fbref
from src.interface.entrada_manual import renderizar_modo_manual
from src.interface.odds import renderizar_odds
from src.interface.resultados import renderizar_resultados

# ------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ------------------------------------------------------------
st.set_page_config(page_title="EngramScore ⚽", page_icon="⚽", layout="wide")

# Carregar CSS
carregar_css()

# Header
renderizar_header()

# Sidebar
renderizar_sidebar()

# ------------------------------------------------------------
# ÁREA PRINCIPAL
# ------------------------------------------------------------

# Verificar se um jogo foi selecionado da barra lateral
if "jogo_selecionado" in st.session_state:
    jogo = st.session_state["jogo_selecionado"]
    st.markdown(f"""
    <div style="text-align:center; margin:20px 0;">
        <h2>{jogo['casa']} vs {jogo['fora']}</h2>
        <div style="font-size:18px; color:#F0C040;">{jogo.get('resultado_previsto', '')}</div>
        <div style="font-size:14px; color:#B0B8C0;">EC Casa: {jogo['EC_A']} | EC Fora: {jogo['EC_B']}</div>
    </div>
    """, unsafe_allow_html=True)
    st.info("📊 A análise completa com gráficos será carregada na próxima atualização do sistema.")
    
    # Botão para limpar seleção
    if st.button("🔄 Voltar para nova análise"):
        del st.session_state["jogo_selecionado"]
        st.rerun()

else:
    # Modo de entrada
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("""<div style="text-align:center; margin-bottom:20px;"><span style="font-size:13px; text-transform:uppercase; letter-spacing:3px; color:#B0B8C0;">Dados do Confronto</span></div>""", unsafe_allow_html=True)

    modo_entrada = st.radio("Modo de entrada:", ["📋 Colar do FBref", "✏️ Manual"], horizontal=True)

    # Renderizar modo selecionado
    if modo_entrada == "📋 Colar do FBref":
        dados = renderizar_modo_fbref()
    else:
        dados = renderizar_modo_manual()

    # Renderizar odds (comum aos dois modos)
    odds = renderizar_odds()

    # Botão de análise
    if dados is not None:
        st.markdown("<br>", unsafe_allow_html=True)
        col_btn = st.columns([1, 2, 1])
        with col_btn[1]:
            gerar = st.button("⚡ GERAR ENGRAMSCORE", type="primary", use_container_width=True)

        if gerar:
            renderizar_resultados(dados, odds)

# Rodapé
renderizar_rodape()
