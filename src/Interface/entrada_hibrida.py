"""
Entrada Híbrida — EngramScore
Reconhece automaticamente tabelas do FBref ou WhoScored.
Permite colar múltiplas tabelas para extrair o máximo de indicadores.
"""

import streamlit as st
import re


def detectar_formato(texto):
    """
    Detecta se o texto colado é do FBref ou do WhoScored.
    Retorna 'fbref', 'whoscored' ou None.
    """
    if not texto or len(texto) < 50:
        return None
    
    if any(padrao in texto for padrao in ['Gls', 'Ast', 'SoT', 'Poss', 'Tkl', 'CrdY']):
        return 'fbref'
    
    if any(padrao in texto for padrao in ['Rating', 'Chutes pj', 'Disciplina', 'Posse%']):
        return 'whoscored'
    
    return None


def extrair_valor(partes, cabecalho, padroes):
    """Extrai valor numérico de uma linha baseado em padrões de coluna."""
    for padrao in padroes:
        for i, col in enumerate(cabecalho):
            if padrao.lower() in col.lower() and i < len(partes):
                try:
                    return float(partes[i])
                except (ValueError, IndexError):
                    continue
    return 0.0


def media_liga(padroes, cabecalho, dados):
    """Calcula a média da liga para um conjunto de padrões."""
    valores = []
    for nome, stats in dados.items():
        val = stats.get(padroes[0], 0)
        if val > 0:
            valores.append(val)
    return sum(valores) / len(valores) if valores else 0.0


def extrair_fbref(texto):
    """Extrai dados de uma tabela do FBref."""
    linhas = texto.strip().split('\n')
    cabecalho = linhas[0].split('\t')
    dados_times = {}
    
    for linha in linhas[1:]:
        partes = linha.split('\t')
        if len(partes) >= 3:
            nome_time = partes[0].strip()
            if nome_time and nome_time not in ['Squad', '']:
                dados_times[nome_time] = {
                    'GM': extrair_valor(partes, cabecalho, ['Gls', 'Goals']),
                    'FA': extrair_valor(partes, cabecalho, ['SoT']),
                    'ECa': extrair_valor(partes, cabecalho, ['CK']),
                    'CK': extrair_valor(partes, cabecalho, ['CK']),
                    'Poss': extrair_valor(partes, cabecalho, ['Poss']),
                    'GS': extrair_valor(partes, cabecalho, ['GA', 'Goals Against']),
                    'FAS': extrair_valor(partes, cabecalho, ['SoTA']),
                    'Tkl': extrair_valor(partes, cabecalho, ['Tkl']),
                    'Fls': extrair_valor(partes, cabecalho, ['Fls']),
                    'CrdY': extrair_valor(partes, cabecalho, ['CrdY']),
                    'Int': extrair_valor(partes, cabecalho, ['Int']),
                    'Sh': extrair_valor(partes, cabecalho, ['Sh']),
                }
    
    if not dados_times:
        return None, None
    
    medias_liga = {
        'GM': media_liga(['GM'], cabecalho, dados_times),
        'FA': media_liga(['FA'], cabecalho, dados_times),
        'ECa': media_liga(['ECa'], cabecalho, dados_times),
        'Poss': media_liga(['Poss'], cabecalho, dados_times),
        'GS': media_liga(['GS'], cabecalho, dados_times),
        'FAS': media_liga(['FAS'], cabecalho, dados_times),
        'ECc': media_liga(['ECa'], cabecalho, dados_times),
        'Des': media_liga(['Tkl'], cabecalho, dados_times),
        'FC': media_liga(['Fls'], cabecalho, dados_times),
        'CA': media_liga(['CrdY'], cabecalho, dados_times),
        'Int': media_liga(['Int'], cabecalho, dados_times),
        'TC': media_liga(['Sh'], cabecalho, dados_times),
    }
    
    return dados_times, medias_liga


def extrair_whoscored(texto):
    """Extrai dados de uma tabela do WhoScored (detecta o tipo automaticamente)."""
    if 'Rating' in texto and 'Chutes pj' in texto:
        return extrair_whoscored_geral(texto)
    elif 'Cruzamentos pj' in texto or 'Bolas Enfiadas pj' in texto:
        return extrair_whoscored_posicional(texto)
    elif 'Contra-ataque' in texto or 'Bola Parada' in texto:
        return extrair_whoscored_situacional(texto)
    elif 'Terço' in texto:
        return extrair_whoscored_territorial(texto)
    return None, None


def extrair_whoscored_geral(texto):
    """Extrai dados da tabela geral do WhoScored."""
    linhas = texto.strip().split('\n')
    dados_times = {}
    medias = {'GM': 0, 'Shots': 0, 'Poss': 0, 'Cmp%': 0, 'FC': 0, 'Rating': 0}
    count = 0
    
    for linha in linhas[1:]:
        partes = linha.split('\t')
        if len(partes) < 5:
            continue
        
        nome_time = re.sub(r'^\d+\.\s*', '', partes[0].strip())
        if not nome_time:
            continue
        
        try:
            gols = float(partes[1]) if len(partes) > 1 else 0
            chutes = float(partes[2]) if len(partes) > 2 else 0
            disciplina = float(partes[3]) if len(partes) > 3 else 0
            posse = float(partes[4]) if len(partes) > 4 else 0
            acerto_passe = float(partes[5]) if len(partes) > 5 else 0
            rating = float(partes[-1]) if len(partes) > 6 else 0
            
            dados_times[nome_time] = {
                'GM': gols, 'Shots': chutes, 'Poss': posse,
                'Cmp%': acerto_passe, 'FC': disciplina, 'Rating': rating,
            }
            
            medias['GM'] += gols
            medias['Shots'] += chutes
            medias['Poss'] += posse
            medias['Cmp%'] += acerto_passe
            medias['FC'] += disciplina
            medias['Rating'] += rating
            count += 1
        except (ValueError, IndexError):
            continue
    
    if count > 0:
        for key in medias:
            medias[key] /= count
    
    return dados_times, medias


def extrair_whoscored_posicional(texto):
    """Extrai dados posicionais do WhoScored."""
    linhas = texto.strip().split('\n')
    dados_times = {}
    
    for linha in linhas[1:]:
        partes = linha.split('\t')
        if len(partes) < 5:
            continue
        
        nome_time = re.sub(r'^\d+\.\s*', '', partes[0].strip())
        if not nome_time:
            continue
        
        try:
            if nome_time not in dados_times:
                dados_times[nome_time] = {}
            dados_times[nome_time]['Crs'] = float(partes[1]) if len(partes) > 1 else 0
            dados_times[nome_time]['ThrBall'] = float(partes[2]) if len(partes) > 2 else 0
            dados_times[nome_time]['LongBall'] = float(partes[3]) if len(partes) > 3 else 0
            dados_times[nome_time]['ShortPass'] = float(partes[4]) if len(partes) > 4 else 0
        except (ValueError, IndexError):
            continue
    
    return dados_times, None


def extrair_whoscored_situacional(texto):
    """Extrai dados situacionais do WhoScored."""
    linhas = texto.strip().split('\n')
    dados_times = {}
    
    for linha in linhas[1:]:
        partes = linha.split('\t')
        if len(partes) < 5:
            continue
        
        nome_time = re.sub(r'^\d+\.\s*', '', partes[0].strip())
        if not nome_time:
            continue
        
        try:
            if nome_time not in dados_times:
                dados_times[nome_time] = {}
            dados_times[nome_time]['GlsBR'] = float(partes[1]) if len(partes) > 1 else 0
            dados_times[nome_time]['GlsCA'] = float(partes[2]) if len(partes) > 2 else 0
            dados_times[nome_time]['GlsSP'] = float(partes[3]) if len(partes) > 3 else 0
            dados_times[nome_time]['GlsPK'] = float(partes[4]) if len(partes) > 4 else 0
        except (ValueError, IndexError):
            continue
    
    return dados_times, None


def extrair_whoscored_territorial(texto):
    """Extrai dados territoriais do WhoScored."""
    linhas = texto.strip().split('\n')
    dados_times = {}
    
    for linha in linhas[1:]:
        partes = linha.split('\t')
        if len(partes) < 4:
            continue
        
        nome_time = re.sub(r'^\d+\.\s*', '', partes[0].strip())
        if not nome_time:
            continue
        
        try:
            if nome_time not in dados_times:
                dados_times[nome_time] = {}
            dados_times[nome_time]['OwnThird'] = float(partes[1].replace('%', '')) if len(partes) > 1 else 0
            dados_times[nome_time]['MidThird'] = float(partes[2].replace('%', '')) if len(partes) > 2 else 0
            dados_times[nome_time]['AttThird'] = float(partes[3].replace('%', '')) if len(partes) > 3 else 0
        except (ValueError, IndexError):
            continue
    
    return dados_times, None


def mesclar_dados(dados_existentes, novos_dados):
    """Mescla novos dados aos já existentes, sem sobrescrever."""
    if not novos_dados:
        return dados_existentes
    
    for time, stats in novos_dados.items():
        if time not in dados_existentes:
            dados_existentes[time] = {}
        for key, value in stats.items():
            if key not in dados_existentes[time] or dados_existentes[time][key] == 0:
                dados_existentes[time][key] = value
    
    return dados_existentes


def renderizar_modo_hibrido():
    """Renderiza o modo de entrada híbrido (FBref + WhoScored)."""
    st.markdown("### 📋 Cole as tabelas (FBref ou WhoScored)")
    st.markdown("*Cole uma ou mais tabelas. O sistema detecta automaticamente a fonte.*")

    texto_colado = st.text_area(
        "Cole aqui (pode colar várias vezes)",
        height=200,
        placeholder="Cole a tabela do FBref ou WhoScored...\n\nPode colar outra tabela depois para complementar.",
        help="Cole a tabela inteira (Ctrl+A no site, Ctrl+V aqui)."
    )

    if "dados_acumulados" not in st.session_state:
        st.session_state.dados_acumulados = {}
    if "medias_liga" not in st.session_state:
        st.session_state.medias_liga = {}
    if "times_disponiveis" not in st.session_state:
        st.session_state.times_disponiveis = []

    if texto_colado:
        formato = detectar_formato(texto_colado)
        
        if formato == 'fbref':
            st.success("✅ Detectado: FBref")
            dados_times, medias_liga = extrair_fbref(texto_colado)
            if dados_times:
                st.session_state.medias_liga.update(medias_liga or {})
                st.session_state.dados_acumulados = mesclar_dados(
                    st.session_state.dados_acumulados, dados_times
                )
                st.session_state.times_disponiveis = list(st.session_state.dados_acumulados.keys())
                st.success(f"✅ {len(dados_times)} times extraídos do FBref")
        
        elif formato == 'whoscored':
            st.success("✅ Detectado: WhoScored")
            dados_times, medias_liga = extrair_whoscored(texto_colado)
            if dados_times:
                if medias_liga:
                    st.session_state.medias_liga.update(medias_liga)
                st.session_state.dados_acumulados = mesclar_dados(
                    st.session_state.dados_acumulados, dados_times
                )
                st.session_state.times_disponiveis = list(st.session_state.dados_acumulados.keys())
                st.success(f"✅ {len(dados_times)} times extraídos do WhoScored")
        else:
            st.warning("⚠️ Formato não reconhecido. Tente colar a tabela inteira do site.")

    if st.button("🗑️ Limpar dados acumulados"):
        st.session_state.dados_acumulados = {}
        st.session_state.medias_liga = {}
        st.session_state.times_disponiveis = []
        st.rerun()

    if st.session_state.times_disponiveis:
        st.markdown("---")
        st.markdown(f"### 📊 {len(st.session_state.times_disponiveis)} times disponíveis")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            nome_casa = st.selectbox("🏠 Time da Casa", st.session_state.times_disponiveis, key="hib_casa")
        with col_t2:
            nome_fora = st.selectbox("✈️ Time Visitante", st.session_state.times_disponiveis, key="hib_fora")

        if st.session_state.medias_liga:
            st.markdown("### 📊 Médias da Liga (calculadas)")
            col_m1, col_m2, col_m3 = st.columns(3)
            ml = st.session_state.medias_liga
            with col_m1:
                if ml.get('GM'): st.metric("Gols/jogo", f"{ml['GM']:.2f}")
                if ml.get('Poss'): st.metric("Posse", f"{ml['Poss']:.1f}%")
            with col_m2:
                if ml.get('FA'): st.metric("Finalizações alvo/j", f"{ml['FA']:.2f}")
                if ml.get('Rating'): st.metric("Rating médio", f"{ml['Rating']:.2f}")
            with col_m3:
                if ml.get('FC'): st.metric("Faltas/j", f"{ml['FC']:.1f}")
                if ml.get('CA'): st.metric("Cartões/j", f"{ml['CA']:.1f}")

        st.markdown("### 📝 Dados Complementares")
        col_extra1, col_extra2 = st.columns(2)
        with col_extra1:
            res_casa = st.text_input("Últ. 5 resultados Casa (V/E/D)", "VVEDV", key="hib_res_casa").upper()
            cons_casa = st.text_input("Últ. 10 resultados Casa (V/E/D)", "VVEDVVEDVV", key="hib_cons_casa").upper()
            moral_casa = st.slider("Moral Casa (pts 3j)", 0, 9, 6, key="hib_moral_casa")
            pos_casa = st.number_input("Posição Casa", 1, 24, 2, key="hib_pos_casa")
            pts_cpp_casa = st.number_input("Pontos CPP Casa", 0, 30, 6, key="hib_cpp_casa")
            jogos_cpp_casa = st.number_input("Jogos CPP Casa", 0, 10, 3, key="hib_jcpp_casa")
        with col_extra2:
            res_fora = st.text_input("Últ. 5 resultados Fora (V/E/D)", "DDVVE", key="hib_res_fora").upper()
            cons_fora = st.text_input("Últ. 10 resultados Fora (V/E/D)", "DDVVEDDVV", key="hib_cons_fora").upper()
            moral_fora = st.slider("Moral Fora (pts 3j)", 0, 9, 3, key="hib_moral_fora")
            pos_fora = st.number_input("Posição Fora", 1, 24, 16, key="hib_pos_fora")
            pts_cpp_fora = st.number_input("Pontos CPP Fora", 0, 30, 4, key="hib_cpp_fora")
            jogos_cpp_fora = st.number_input("Jogos CPP Fora", 0, 10, 2, key="hib_jcpp_fora")

        dados_casa = st.session_state.dados_acumulados.get(nome_casa, {})
        dados_fora = st.session_state.dados_acumulados.get(nome_fora, {})
        ml = st.session_state.medias_liga

        return {
            "nome_casa": nome_casa,
            "nome_fora": nome_fora,
            "n_casa": 10, "n_fora": 10,
            "gm_casa": dados_casa.get('GM', 0),
            "fa_casa": dados_casa.get('FA', dados_casa.get('Shots', 0)),
            "eca_casa": dados_casa.get('ECa', dados_casa.get('CK', 0)),
            "posse_casa": dados_casa.get('Poss', 50),
            "gs_casa": dados_casa.get('GS', 0),
            "fas_casa": dados_casa.get('FAS', 0),
            "des_casa": dados_casa.get('Tkl', 0),
            "fc_casa": dados_casa.get('FC', dados_casa.get('Fls', 0)),
            "ca_casa": dados_casa.get('CrdY', 0),
            "gm_fora": dados_fora.get('GM', 0),
            "fa_fora": dados_fora.get('FA', dados_fora.get('Shots', 0)),
            "eca_fora": dados_fora.get('ECa', dados_fora.get('CK', 0)),
            "posse_fora": dados_fora.get('Poss', 50),
            "gs_fora": dados_fora.get('GS', 0),
            "fas_fora": dados_fora.get('FAS', 0),
            "des_fora": dados_fora.get('Tkl', 0),
            "fc_fora": dados_fora.get('FC', dados_fora.get('Fls', 0)),
            "ca_fora": dados_fora.get('CrdY', 0),
            "res_casa": res_casa, "cons_casa": cons_casa, "moral_casa": moral_casa,
            "pos_casa": pos_casa, "pts_cpp_casa": pts_cpp_casa, "jogos_cpp_casa": jogos_cpp_casa,
            "res_fora": res_fora, "cons_fora": cons_fora, "moral_fora": moral_fora,
            "pos_fora": pos_fora, "pts_cpp_fora": pts_cpp_fora, "jogos_cpp_fora": jogos_cpp_fora,
            "prat_casa": "Média", "prat_fora": "Média",
            "medias_liga": ml,
            "dados_A": dados_casa,
            "dados_B": dados_fora,
            "crs_casa": dados_casa.get('Crs', 0),
            "thrball_casa": dados_casa.get('ThrBall', 0),
            "shortpass_casa": dados_casa.get('ShortPass', 0),
            "longball_casa": dados_casa.get('LongBall', 0),
            "attthird_casa": dados_casa.get('AttThird', 50),
            "glsca_casa": dados_casa.get('GlsCA', 0),
            "glssp_casa": dados_casa.get('GlsSP', 0),
            "rating_casa": dados_casa.get('Rating', 6.5),
            "crs_fora": dados_fora.get('Crs', 0),
            "thrball_fora": dados_fora.get('ThrBall', 0),
            "shortpass_fora": dados_fora.get('ShortPass', 0),
            "longball_fora": dados_fora.get('LongBall', 0),
            "attthird_fora": dados_fora.get('AttThird', 50),
            "glsca_fora": dados_fora.get('GlsCA', 0),
            "glssp_fora": dados_fora.get('GlsSP', 0),
            "rating_fora": dados_fora.get('Rating', 6.5),
        }

    return None
