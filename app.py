import sys
import importlib.util
from pathlib import Path

# Caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
INTERFACE_DIR = SRC_DIR / "interface"

# Adicionar ao sys.path para importações internas dos módulos
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(SRC_DIR))

import streamlit as st

# Função para carregar um módulo diretamente do caminho
def carregar_modulo(nome_arquivo, nome_modulo):
    caminho = INTERFACE_DIR / nome_arquivo
    spec = importlib.util.spec_from_file_location(nome_modulo, caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo

# Carregar todos os módulos da interface
css = carregar_modulo("css.py", "css")
sidebar = carregar_modulo("sidebar.py", "sidebar")
entrada_fbref = carregar_modulo("entrada_fbref.py", "entrada_fbref")
entrada_manual = carregar_modulo("entrada_manual.py", "entrada_manual")
odds = carregar_modulo("odds.py", "odds")
resultados = carregar_modulo("resultados.py", "resultados")

# ------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ------------------------------------------------------------
st.set_page_config(page_title="EngramScore ⚽", page_icon="⚽", layout="wide")

# Carregar CSS
css.carregar_css()

# Header
css.renderizar_header()

# Sidebar
sidebar.renderizar_sidebar()

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
    st.info("📊 A análise completa com gráficos será carregada na próxima atualização do sistema.")
    if st.button("🔄 Voltar para nova análise"):
        del st.session_state["jogo_selecionado"]
        st.rerun()
else:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("""<div style="text-align:center; margin-bottom:20px;"><span style="font-size:13px; text-transform:uppercase; letter-spacing:3px; color:#B0B8C0;">Dados do Confronto</span></div>""", unsafe_allow_html=True)

    modo_entrada = st.radio("Modo de entrada:", ["📋 Colar do FBref", "✏️ Manual"], horizontal=True)

    if modo_entrada == "📋 Colar do FBref":
        dados = entrada_fbref.renderizar_modo_fbref()
    else:
        dados = entrada_manual.renderizar_modo_manual()

    odds_data = odds.renderizar_odds()

    if dados is not None:
        st.markdown("<br>", unsafe_allow_html=True)
        col_btn = st.columns([1, 2, 1])
        with col_btn[1]:
            gerar = st.button("⚡ GERAR ENGRAMSCORE", type="primary", use_container_width=True)
        if gerar:
            resultados.renderizar_resultados(dados, odds_data)

# Rodapé
css.renderizar_rodape()
