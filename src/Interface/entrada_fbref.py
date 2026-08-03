"""
Entrada FBref — EngramScore
Modo de colagem da tabela do FBref para extrair estatísticas automaticamente.
"""

import streamlit as st


def renderizar_modo_fbref():
    """
    Renderiza o modo de entrada via colagem do FBref.
    Retorna um dicionário com os dados extraídos ou None.
    """
    st.markdown("### 📋 Cole a tabela do FBref")
    st.markdown("*Acesse [fbref.com](https://fbref.com), escolha a liga, selecione a tabela inteira (Ctrl+A) e cole abaixo.*")

    texto_colado = st.text_area(
        "Cole aqui a tabela do FBref",
        height=200,
        placeholder="Squad\tMP\tGls\tAst\t...\nPalmeiras\t10\t21\t15\t...\nVasco\t10\t12\t8\t...",
        help="Selecione a tabela 'Standard Stats' inteira no FBref e cole aqui."
    )

    if not texto_colado:
        return None

    try:
        linhas = texto_colado.strip().split('\n')
        cabecalho = linhas[0].split('\t')
        dados_times = {}

        for linha in linhas[1:]:
            partes = linha.split('\t')
            if len(partes) >= 3:
                nome_time = partes[0].strip()
                if nome_time and nome_time not in ['Squad', '']:
                    dados_times[nome_time] = partes

        if not dados_times:
            st.error("❌ Nenhum time encontrado. Verifique o formato.")
            return None

        st.success(f"✅ {len(dados_times)} times encontrados!")

        # Selecionar times
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            nome_casa = st.selectbox("🏠 Time da Casa", list(dados_times.keys()), key="fb_casa")
        with col_t2:
            nome_fora = st.selectbox("✈️ Time Visitante", list(dados_times.keys()), key="fb_fora")

        # Função para extrair valores
        def extrair_valor(partes, cabecalho, padroes):
            for padrao in padroes:
                for i, col in enumerate(cabecalho):
                    if padrao.lower() in col.lower() and i < len(partes):
                        try:
                            return float(partes[i])
                        except:
                            continue
            return 0.0

        # Função para calcular média da liga
        def media_liga(padroes, cabecalho, dados):
            valores = []
            for nome, partes in dados.items():
                val = extrair_valor(partes, cabecalho, padroes)
                if val > 0:
                    valores.append(val)
            return sum(valores) / len(valores) if valores else 0.0

        # Extrair dados dos times selecionados
        partes_casa = dados_times[nome_casa]
        partes_fora = dados_times[nome_fora]

        gm_casa = extrair_valor(partes_casa, cabecalho, ['Gls', 'Goals'])
        fa_casa = extrair_valor(partes_casa, cabecalho, ['SoT'])
        eca_casa = extrair_valor(partes_casa, cabecalho, ['CK'])
        posse_casa = extrair_valor(partes_casa, cabecalho, ['Poss'])
        gs_casa = extrair_valor(partes_casa, cabecalho, ['GA', 'Goals Against'])
        fas_casa = extrair_valor(partes_casa, cabecalho, ['SoTA'])
        des_casa = extrair_valor(partes_casa, cabecalho, ['Tkl'])
        fc_casa = extrair_valor(partes_casa, cabecalho, ['Fls'])
        ca_casa = extrair_valor(partes_casa, cabecalho, ['CrdY'])

        gm_fora = extrair_valor(partes_fora, cabecalho, ['Gls', 'Goals'])
        fa_fora = extrair_valor(partes_fora, cabecalho, ['SoT'])
        eca_fora = extrair_valor(partes_fora, cabecalho, ['CK'])
        posse_fora = extrair_valor(partes_fora, cabecalho, ['Poss'])
        gs_fora = extrair_valor(partes_fora, cabecalho, ['GA', 'Goals Against'])
        fas_fora = extrair_valor(partes_fora, cabecalho, ['SoTA'])
        des_fora = extrair_valor(partes_fora, cabecalho, ['Tkl'])
        fc_fora = extrair_valor(partes_fora, cabecalho, ['Fls'])
        ca_fora = extrair_valor(partes_fora, cabecalho, ['CrdY'])

        # Calcular médias da liga
        medias_liga = {
            'GM': media_liga(['Gls', 'Goals'], cabecalho, dados_times),
            'FA': media_liga(['SoT'], cabecalho, dados_times),
            'ECa': media_liga(['CK'], cabecalho, dados_times),
            'Posse': media_liga(['Poss'], cabecalho, dados_times),
            'GS': media_liga(['GA', 'Goals Against'], cabecalho, dados_times),
            'FAS': media_liga(['SoTA'], cabecalho, dados_times),
            'ECc': media_liga(['CK'], cabecalho, dados_times),
            'Des': media_liga(['Tkl'], cabecalho, dados_times),
            'FC': media_liga(['Fls'], cabecalho, dados_times),
            'CA': media_liga(['CrdY'], cabecalho, dados_times),
        }

        # Exibir médias da liga
        st.markdown("### 📊 Médias da Liga (auto-calculadas)")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Gols/jogo", f"{medias_liga['GM']:.2f}")
            st.metric("Posse", f"{medias_liga['Posse']:.1f}%")
        with col_m2:
            st.metric("Finalizações alvo/j", f"{medias_liga['FA']:.2f}")
            st.metric("Desarmes/j", f"{medias_liga['Des']:.1f}")
        with col_m3:
            st.metric("Escanteios/j", f"{medias_liga['ECa']:.2f}")
            st.metric("Faltas/j", f"{medias_liga['FC']:.1f}")

        # Campos complementares
        st.markdown("### 📝 Dados Complementares")
        st.markdown("*Preencha os resultados recentes e dados de confronto.*")

        col_extra1, col_extra2 = st.columns(2)
        with col_extra1:
            res_casa = st.text_input("Últ. 5 resultados Casa (V/E/D)", "VVEDV", key="fb_res_casa").upper()
            cons_casa = st.text_input("Últ. 10 resultados Casa (V/E/D)", "VVEDVVEDVV", key="fb_cons_casa").upper()
            moral_casa = st.slider("Moral Casa (pts 3j)", 0, 9, 6, key="fb_moral_casa")
            pos_casa = st.number_input("Posição Casa", 1, 24, 2, key="fb_pos_casa")
            prat_casa = st.selectbox("Prateleira Adv. Casa", ["Elite","Alta","Média","Baixa","Crítica"], key="fb_prat_casa")
            pts_cpp_casa = st.number_input("Pontos CPP Casa", 0, 30, 6, key="fb_cpp_casa")
            jogos_cpp_casa = st.number_input("Jogos CPP Casa", 0, 10, 3, key="fb_jcpp_casa")
        with col_extra2:
            res_fora = st.text_input("Últ. 5 resultados Fora (V/E/D)", "DDVVE", key="fb_res_fora").upper()
            cons_fora = st.text_input("Últ. 10 resultados Fora (V/E/D)", "DDVVEDDVV", key="fb_cons_fora").upper()
            moral_fora = st.slider("Moral Fora (pts 3j)", 0, 9, 3, key="fb_moral_fora")
            pos_fora = st.number_input("Posição Fora", 1, 24, 16, key="fb_pos_fora")
            prat_fora = st.selectbox("Prateleira Adv. Fora", ["Elite","Alta","Média","Baixa","Crítica"], key="fb_prat_fora")
            pts_cpp_fora = st.number_input("Pontos CPP Fora", 0, 30, 4, key="fb_cpp_fora")
            jogos_cpp_fora = st.number_input("Jogos CPP Fora", 0, 10, 2, key="fb_jcpp_fora")

        # Montar dicionário de retorno
        return {
            "nome_casa": nome_casa,
            "nome_fora": nome_fora,
            "n_casa": 10,
            "n_fora": 10,
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
                'GS': gs_casa, 'FAS': fas_casa, 'ECc': 0, 'Des': des_casa,
                'FC': fc_casa, 'CA': ca_casa
            },
            "dados_B": {
                'GM': gm_fora, 'FA': fa_fora, 'ECa': eca_fora, 'Posse': posse_fora,
                'GS': gs_fora, 'FAS': fas_fora, 'ECc': 0, 'Des': des_fora,
                'FC': fc_fora, 'CA': ca_fora
            },
        }

    except Exception as e:
        st.error(f"❌ Erro ao processar tabela: {e}")
        return None
