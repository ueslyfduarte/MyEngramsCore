"""
Entrada Manual — EngramScore
Formulário tradicional com cards para digitação dos dados.
"""

import streamlit as st


def renderizar_modo_manual():
    """
    Renderiza o modo de entrada manual com cards por setor.
    Retorna um dicionário com os dados preenchidos.
    """
    colA, colB = st.columns(2)

    # ============= TIME A =============
    with colA:
        with st.container():
            st.markdown('<div class="card-premium">', unsafe_allow_html=True)
            st.markdown('<div class="card-header-premium">🏠 TIME DA CASA</div>', unsafe_allow_html=True)
            nome_casa = st.text_input("Nome", "Time A", key="casa", label_visibility="collapsed")
            n_casa = st.number_input("Jogos", 1, 38, 10, key="nj_casa")
            gm_casa = st.number_input("Gols/jogo", 0.0, 5.0, 2.0, 0.1, key="gm_casa")
            fa_casa = st.number_input("Finalizações alvo/j", 0.0, 10.0, 4.5, 0.1, key="fa_casa")
            eca_casa = st.number_input("Escanteios a favor/j", 0.0, 20.0, 5.5, 0.1, key="eca_casa")
            posse_casa = st.slider("Posse (%)", 0, 100, 55, key="posse_casa")
            gs_casa = st.number_input("Gols sofridos/j", 0.0, 5.0, 0.8, 0.1, key="gs_casa")
            fas_casa = st.number_input("Finalizações alvo sofridas/j", 0.0, 10.0, 3.0, 0.1, key="fas_casa")
            des_casa = st.number_input("Desarmes/j", 0.0, 50.0, 16.0, 0.1, key="des_casa")
            fc_casa = st.number_input("Faltas/j", 0.0, 30.0, 13.0, 0.1, key="fc_casa")
            ca_casa = st.number_input("Cartões amarelos/j", 0.0, 10.0, 2.2, 0.1, key="ca_casa")
            res_casa = st.text_input("Últ. 5 resultados (V/E/D)", "VVEDV", key="res_casa").upper()
            cons_casa = st.text_input("Últ. 10 resultados (V/E/D)", "VVEDVVEDVV", key="cons_casa").upper()
            moral_casa = st.slider("Moral (pts 3j)", 0, 9, 6, key="moral_casa")
            pts_cpp_casa = st.number_input("Pontos contra prateleira", 0, 30, 6, key="pcpp_casa")
            jogos_cpp_casa = st.number_input("Jogos contra prateleira", 0, 10, 3, key="jcpp_casa")
            prat_casa = st.selectbox("Prateleira do Adversário", ["Elite","Alta","Média","Baixa","Crítica"], key="prat_casa")
            pos_casa = st.number_input("Posição na tabela", 1, 24, 2, key="pos_casa")
            st.markdown('</div>', unsafe_allow_html=True)

    # ============= TIME B =============
    with colB:
        with st.container():
            st.markdown('<div class="card-premium">', unsafe_allow_html=True)
            st.markdown('<div class="card-header-premium">✈️ TIME VISITANTE</div>', unsafe_allow_html=True)
            nome_fora = st.text_input("Nome", "Time B", key="fora", label_visibility="collapsed")
            n_fora = st.number_input("Jogos", 1, 38, 10, key="nj_fora")
            gm_fora = st.number_input("Gols/jogo", 0.0, 5.0, 1.2, 0.1, key="gm_fora")
            fa_fora = st.number_input("Finalizações alvo/j", 0.0, 10.0, 3.2, 0.1, key="fa_fora")
            eca_fora = st.number_input("Escanteios a favor/j", 0.0, 20.0, 4.5, 0.1, key="eca_fora")
            posse_fora = st.slider("Posse (%)", 0, 100, 48, key="posse_fora")
            gs_fora = st.number_input("Gols sofridos/j", 0.0, 5.0, 1.5, 0.1, key="gs_fora")
            fas_fora = st.number_input("Finalizações alvo sofridas/j", 0.0, 10.0, 3.8, 0.1, key="fas_fora")
            des_fora = st.number_input("Desarmes/j", 0.0, 50.0, 14.0, 0.1, key="des_fora")
            fc_fora = st.number_input("Faltas/j", 0.0, 30.0, 11.0, 0.1, key="fc_fora")
            ca_fora = st.number_input("Cartões amarelos/j", 0.0, 10.0, 1.8, 0.1, key="ca_fora")
            res_fora = st.text_input("Últ. 5 resultados (V/E/D)", "DDVVE", key="res_fora").upper()
            cons_fora = st.text_input("Últ. 10 resultados (V/E/D)", "DDVVEDDVV", key="cons_fora").upper()
            moral_fora = st.slider("Moral (pts 3j)", 0, 9, 3, key="moral_fora")
            pts_cpp_fora = st.number_input("Pontos contra prateleira", 0, 30, 4, key="pcpp_fora")
            jogos_cpp_fora = st.number_input("Jogos contra prateleira", 0, 10, 2, key="jcpp_fora")
            prat_fora = st.selectbox("Prateleira do Adversário", ["Elite","Alta","Média","Baixa","Crítica"], key="prat_fora")
            pos_fora = st.number_input("Posição na tabela", 1, 24, 16, key="pos_fora")
            st.markdown('</div>', unsafe_allow_html=True)

    # ============= MÉDIAS DA LIGA =============
    with st.expander("⚙️ Médias da Liga (Manual)", expanded=False):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            media_gm = st.number_input("Gols/jogo", 0.1, 5.0, 1.4, 0.1, key="media_gm")
            media_fa = st.number_input("Finalizações alvo/j", 0.0, 10.0, 4.0, 0.1, key="media_fa")
            media_eca = st.number_input("Escanteios a favor/j", 0.0, 20.0, 5.0, 0.1, key="media_eca")
            media_posse = st.number_input("Posse (%)", 0.0, 100.0, 50.0, 1.0, key="media_posse")
            media_gs = st.number_input("Gols sofridos/j", 0.1, 5.0, 1.4, 0.1, key="media_gs")
        with col_s2:
            media_fas = st.number_input("Finalizações alvo sofridas/j", 0.0, 10.0, 4.0, 0.1, key="media_fas")
            media_ecc = st.number_input("Escanteios contra/j", 0.0, 20.0, 5.0, 0.1, key="media_ecc")
            media_des = st.number_input("Desarmes/j", 0.0, 50.0, 15.0, 0.1, key="media_des")
            media_fc = st.number_input("Faltas/j", 0.0, 30.0, 12.0, 0.1, key="media_fc")
            media_ca = st.number_input("Cartões amarelos/j", 0.0, 10.0, 2.0, 0.1, key="media_ca")

        medias_liga = {
            'GM': media_gm, 'FA': media_fa, 'ECa': media_eca,
            'GS': media_gs, 'FAS': media_fas, 'ECc': media_ecc,
            'FC': media_fc, 'CA': media_ca, 'Des': media_des, 'Posse': media_posse,
        }

    # Montar dicionário de retorno
    return {
        "nome_casa": nome_casa,
        "nome_fora": nome_fora,
        "n_casa": n_casa,
        "n_fora": n_fora,
        "gm_casa": gm_casa, "fa_casa": fa_casa, "eca_casa": eca_casa,
        "posse_casa": posse_casa, "gs_casa": gs_casa, "fas_casa": fas_casa,
        "des_casa": des_casa, "fc_casa": fc_casa, "ca_casa": ca_casa,
        "gm_fora": gm_fora, "fa_fora": fa_fora, "eca_fora": eca_fora,
        "posse_fora": posse_fora, "gs_fora": gs_fora, "fas_fora": fas_fora,
        "des_fora": des_fora, "fc_fora": fc_fora, "ca_fora": ca_fora,
        "res_casa": res_casa, "cons_casa": cons_casa, "moral_casa": moral_casa,
        "pos_casa": pos_casa, "prat_casa": prat_casa,
        "pts_cpp_casa": pts_cpp_casa, "jogos_cpp_casa": jogos_cpp_casa,
        "res_fora": res_fora, "cons_fora": cons_fora, "moral_fora": moral_fora,
        "pos_fora": pos_fora, "prat_fora": prat_fora,
        "pts_cpp_fora": pts_cpp_fora, "jogos_cpp_fora": jogos_cpp_fora,
        "medias_liga": medias_liga,
        "dados_A": {
            'GM': gm_casa, 'FA': fa_casa, 'ECa': eca_casa, 'Posse': posse_casa,
            'GS': gs_casa, 'FAS': fas_casa, 'ECc': media_ecc, 'Des': des_casa,
            'FC': fc_casa, 'CA': ca_casa
        },
        "dados_B": {
            'GM': gm_fora, 'FA': fa_fora, 'ECa': eca_fora, 'Posse': posse_fora,
            'GS': gs_fora, 'FAS': fas_fora, 'ECc': media_ecc, 'Des': des_fora,
            'FC': fc_fora, 'CA': ca_fora
        },
    }
