import sys
import importlib.util
from pathlib import Path
import streamlit as st

# ✅ PRIMEIRA CHAMADA STREAMLIT
st.set_page_config(page_title="EngramScore ⚽", page_icon="⚽", layout="wide")

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


# Carregar módulos
css = carregar_modulo("css.py", "css")
sidebar = carregar_modulo("sidebar.py", "sidebar")
entrada_hibrida = carregar_modulo("entrada_hibrida.py", "entrada_hibrida")
odds = carregar_modulo("odds.py", "odds")
resultados = carregar_modulo("resultados.py", "resultados")

# Renderizar interface
css.carregar_css()
css.renderizar_header()
sidebar.renderizar_sidebar()

# Área principal
if "jogo_selecionado" in st.session_state:
    jogo = st.session_state["jogo_selecionado"]
    st.markdown(f"<h2>{jogo['casa']} vs {jogo['fora']}</h2>", unsafe_allow_html=True)
    st.info("📊 Análise do dia carregada.")
    if st.button("🔄 Nova análise"):
        del st.session_state["jogo_selecionado"]
        st.rerun()
else:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("""<div style="text-align:center; margin-bottom:20px;"><span style="font-size:13px; text-transform:uppercase; letter-spacing:3px; color:#B0B8C0;">Dados do Confronto</span></div>""", unsafe_allow_html=True)

    dados = entrada_hibrida.renderizar_modo_hibrido()
    odds_data = odds.renderizar_odds()

    if dados is not None:
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

css.renderizar_rodape()
