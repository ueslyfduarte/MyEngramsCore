import streamlit as st
import pandas as pd
from src.metricas.ma import calcular_ma, calcular_pontos_e_resultados
from src.metricas.fg import calcular_fg
from src.metricas.cpp import calcular_cpp
from src.metricas.estilo import calcular_vetor_estilo, calcular_estilo
from src.metricas.psicologico import calcular_psicologico
from src.engramscore import calcular_engramscore
from src.mercados.gols import calcular_mercado_gols

# Configuração da página
st.set_page_config(page_title="EngramsCore", page_icon="⚽", layout="wide")

st.title("⚽ EngramsCore - Análise Esportiva")
st.markdown("Método próprio de avaliação de equipes para um confronto.")

# --- Barra lateral: Médias da Liga (comum a todos os cálculos) ---
st.sidebar.header("📊 Médias da Liga (referência)")
with st.sidebar.expander("Ajustar médias", expanded=False):
    media_gm = st.number_input("Média de gols marcados/jogo", value=1.4, step=0.1)
    media_gs = st.number_input("Média de gols sofridos/jogo", value=1.4, step=0.1)
    media_posse = st.number_input("Média de posse (%)", value=50.0, step=1.0)
    # Outras médias podem ser adicionadas conforme necessário
    medias_liga = {
        'GM': media_gm,
        'GS': media_gs,
        'Posse': media_posse,
        # Preencher mais campos quando disponíveis
    }

# --- Entrada de dados dos times ---
col1, col2 = st.columns(2)

with col1:
    st.header("Time A (Mandante)")
    nome_a = st.text_input("Nome do Time A", "Time A")
    
    with st.expander("📈 MA - Momento Atual", expanded=True):
        resultados_a = st.text_input("Últimos resultados (V/E/D)", "VVDVE", key="res_a").upper()
        odd_a = st.number_input("Odd vitória (1X2)", min_value=1.01, value=1.80, step=0.01, key="odd_a")
        pontos_a, v_a, d_a = calcular_pontos_e_resultados(list(resultados_a))
        ma_a = calcular_ma(pontos_a, v_a, d_a, odd_a)
        st.metric("MA calculado", f"{ma_a:.2f}")
    
    with st.expander("💪 FG - Força Geral", expanded=False):
        st.markdown("**Ataque**")
        gm_a = st.number_input("Gols marcados/jogo", min_value=0.0, value=2.0, step=0.1, key="gm_a")
        fa_a = st.number_input("Finalizações alvo/jogo", value=0.0, step=0.1, key="fa_a")
        xg_a = st.number_input("xG/jogo", value=0.0, step=0.1, key="xg_a")
        st.markdown("**Defesa**")
        gs_a = st.number_input("Gols sofridos/jogo", min_value=0.0, value=0.8, step=0.1, key="gs_a")
        xga_a = st.number_input("xG contra/jogo", value=0.0, step=0.1, key="xga_a")
        st.markdown("**Meio**")
        posse_a = st.number_input("Posse de bola (%)", value=55.0, step=1.0, key="posse_a")
        # Montar dicionário para FG
        dados_fg_a = {'GM': gm_a, 'FA': fa_a, 'xG': xg_a, 'GS': gs_a, 'xGA': xga_a, 'Posse': posse_a}
        # Remover zeros (indicadores não informados)
        dados_fg_a = {k: v for k, v in dados_fg_a.items() if v != 0.0}
        n_jogos_a = st.number_input("Jogos na temporada", min_value=1, value=10, step=1, key="n_a")
        fg_a = calcular_fg(dados_fg_a, medias_liga, n_jogos_a)
        st.metric("FG calculado", f"{fg_a:.2f}")
    
    with st.expander("🏆 CPP - Confronto por Prateleira", expanded=False):
        pontos_cpp_a = st.number_input("Pontos contra prateleira do adversário", min_value=0, value=6, step=1, key="pcpp_a")
        jogos_cpp_a = st.number_input("Jogos contra essa prateleira", min_value=0, value=3, step=1, key="jcpp_a")
        cpp_a = calcular_cpp(pontos_cpp_a, jogos_cpp_a, odd_a)
        st.metric("CPP calculado", f"{cpp_a:.2f}")
    
    with st.expander("🎨 Estilo de Jogo", expanded=False):
        st.markdown("**Indicadores (deixe 0 se não disponível)**")
        posse_est_a = st.number_input("Posse (%)", value=55.0, key="posse_est_a")
        ppda_a = st.number_input("PPDA", value=0.0, key="ppda_a")  # quanto menor, mais pressão
        trans_a = st.number_input("Chutes em transição/jogo", value=0.0, key="trans_a")
        # Simplificando: coletar alguns indicadores chave
        dados_estilo_a = {}
        if posse_est_a > 0: dados_estilo_a['posse'] = posse_est_a
        if ppda_a > 0: dados_estilo_a['ppda'] = ppda_a
        if trans_a > 0: dados_estilo_a['chutes_trans'] = trans_a
        vetor_estilo_a = calcular_vetor_estilo(dados_estilo_a, medias_liga, n_jogos_a)
        st.write("Vetor calculado:", vetor_estilo_a)
    
    with st.expander("🧠 Psicológico", expanded=False):
        st.markdown("**Consistência (últimos 10 resultados V/E/D)**")
        cons_a = st.text_input("Resultados", "VVEDVVEDVV", key="cons_a").upper()
        pontos_cons_a, _, _ = calcular_pontos_e_resultados(list(cons_a))
        moral_a = st.slider("Moral (pontos últimos 3 jogos)", 0, 9, 6, key="moral_a")
        p_obj_a = st.slider("Pressão objetiva (0-100)", 0, 100, 40, key="pobj_a")
        sens_a = st.slider("Sensibilidade (-1 a +1)", -1.0, 1.0, 0.0, 0.1, key="sens_a")
        psic_a = calcular_psicologico(
            consistencia_pontos=pontos_cons_a,
            moral_pontos=moral_a,
            pressao_p_obj=p_obj_a,
            pressao_sensibilidade=sens_a
        )
        st.metric("Psicológico calculado", f"{psic_a:.2f}")
    
    prateleira_a = st.selectbox("Prateleira", ["Elite", "Alta", "Média", "Baixa", "Crítico"], index=2, key="prat_a")
    prat_map = {"Elite": 0, "Alta": 1, "Média": 2, "Baixa": 3, "Crítico": 4}
    prat_a_num = prat_map[prateleira_a]

# Time B (Visitante) - análogo
with col2:
    st.header("Time B (Visitante)")
    nome_b = st.text_input("Nome do Time B", "Time B")
    
    with st.expander("📈 MA - Momento Atual", expanded=True):
        resultados_b = st.text_input("Últimos resultados (V/E/D)", "DDVVE", key="res_b").upper()
        odd_b = st.number_input("Odd vitória (1X2)", min_value=1.01, value=4.00, step=0.01, key="odd_b")
        pontos_b, v_b, d_b = calcular_pontos_e_resultados(list(resultados_b))
        ma_b = calcular_ma(pontos_b, v_b, d_b, odd_b)
        st.metric("MA calculado", f"{ma_b:.2f}")
    
    with st.expander("💪 FG - Força Geral", expanded=False):
        st.markdown("**Ataque**")
        gm_b = st.number_input("Gols marcados/jogo", min_value=0.0, value=1.2, step=0.1, key="gm_b")
        fa_b = st.number_input("Finalizações alvo/jogo", value=0.0, step=0.1, key="fa_b")
        xg_b = st.number_input("xG/jogo", value=0.0, step=0.1, key="xg_b")
        st.markdown("**Defesa**")
        gs_b = st.number_input("Gols sofridos/jogo", min_value=0.0, value=1.5, step=0.1, key="gs_b")
        xga_b = st.number_input("xG contra/jogo", value=0.0, step=0.1, key="xga_b")
        st.markdown("**Meio**")
        posse_b = st.number_input("Posse de bola (%)", value=48.0, step=1.0, key="posse_b")
        dados_fg_b = {'GM': gm_b, 'FA': fa_b, 'xG': xg_b, 'GS': gs_b, 'xGA': xga_b, 'Posse': posse_b}
        dados_fg_b = {k: v for k, v in dados_fg_b.items() if v != 0.0}
        n_jogos_b = st.number_input("Jogos na temporada", min_value=1, value=10, step=1, key="n_b")
        fg_b = calcular_fg(dados_fg_b, medias_liga, n_jogos_b)
        st.metric("FG calculado", f"{fg_b:.2f}")
    
    with st.expander("🏆 CPP - Confronto por Prateleira", expanded=False):
        pontos_cpp_b = st.number_input("Pontos contra prateleira do adversário", min_value=0, value=4, step=1, key="pcpp_b")
        jogos_cpp_b = st.number_input("Jogos contra essa prateleira", min_value=0, value=2, step=1, key="jcpp_b")
        cpp_b = calcular_cpp(pontos_cpp_b, jogos_cpp_b, odd_b)
        st.metric("CPP calculado", f"{cpp_b:.2f}")
    
    with st.expander("🎨 Estilo de Jogo", expanded=False):
        posse_est_b = st.number_input("Posse (%)", value=48.0, key="posse_est_b")
        ppda_b = st.number_input("PPDA", value=0.0, key="ppda_b")
        trans_b = st.number_input("Chutes em transição/jogo", value=0.0, key="trans_b")
        dados_estilo_b = {}
        if posse_est_b > 0: dados_estilo_b['posse'] = posse_est_b
        if ppda_b > 0: dados_estilo_b['ppda'] = ppda_b
        if trans_b > 0: dados_estilo_b['chutes_trans'] = trans_b
        vetor_estilo_b = calcular_vetor_estilo(dados_estilo_b, medias_liga, n_jogos_b)
        st.write("Vetor calculado:", vetor_estilo_b)
    
    with st.expander("🧠 Psicológico", expanded=False):
        cons_b = st.text_input("Resultados", "DDVVEDDVV", key="cons_b").upper()
        pontos_cons_b, _, _ = calcular_pontos_e_resultados(list(cons_b))
        moral_b = st.slider("Moral (pontos últimos 3 jogos)", 0, 9, 3, key="moral_b")
        p_obj_b = st.slider("Pressão objetiva (0-100)", 0, 100, 60, key="pobj_b")
        sens_b = st.slider("Sensibilidade (-1 a +1)", -1.0, 1.0, -0.3, 0.1, key="sens_b")
        psic_b = calcular_psicologico(
            consistencia_pontos=pontos_cons_b,
            moral_pontos=moral_b,
            pressao_p_obj=p_obj_b,
            pressao_sensibilidade=sens_b
        )
        st.metric("Psicológico calculado", f"{psic_b:.2f}")
    
    prateleira_b = st.selectbox("Prateleira", ["Elite", "Alta", "Média", "Baixa", "Crítico"], index=3, key="prat_b")
    prat_b_num = prat_map[prateleira_b]

# --- Cálculo do estilo final (cruzado) ---
# Precisamos calcular estilo usando o vetor do oponente (já temos vetores parciais)
# Vamos usar a função calcular_estilo que cruza os vetores
# Nota: os dicionários de dados_estilo podem estar incompletos, mas a função aceita.
estilo_a = calcular_estilo(dados_estilo_a, medias_liga, n_jogos_a, vetor_estilo_b) if vetor_estilo_b else 50.0
estilo_b = calcular_estilo(dados_estilo_b, medias_liga, n_jogos_b, vetor_estilo_a) if vetor_estilo_a else 50.0

# --- Resultados ---
st.header("📊 Resultados do Confronto")

# Tabela dos pilares
pilares_df = pd.DataFrame({
    'Pilar': ['MA', 'FG', 'CPP', 'Estilo', 'Psicológico'],
    nome_a: [ma_a, fg_a, cpp_a, estilo_a, psic_a],
    nome_b: [ma_b, fg_b, cpp_b, estilo_b, psic_b]
})
st.dataframe(pilares_df.style.format({nome_a: "{:.2f}", nome_b: "{:.2f}"}), use_container_width=True)

# EngramsCore
ec = calcular_engramscore(
    ma_a=ma_a, fg_a=fg_a, cpp_a=cpp_a, estilo_a=estilo_a, psicologico_a=psic_a,
    ma_b=ma_b, fg_b=fg_b, cpp_b=cpp_b, estilo_b=estilo_b, psicologico_b=psic_b,
    time_mandante='A'
)

st.subheader("EngramsCore")
col_ec1, col_ec2 = st.columns(2)
col_ec1.metric(f"{nome_a} (Mandante)", f"{ec['EC_A']:.2f}")
col_ec2.metric(f"{nome_b} (Visitante)", f"{ec['EC_B']:.2f}")

st.subheader("Probabilidades 1X2")
p_a, p_e, p_b = ec['P_A'], ec['P_E'], ec['P_B']
st.write(f"Vitória {nome_a}: {p_a:.2%}")
st.write(f"Empate: {p_e:.2%}")
st.write(f"Vitória {nome_b}: {p_b:.2%}")
st.write(f"Dupla chance {nome_a} ou Empate: {ec['P_A_ou_E']:.2%}")
st.write(f"Dupla chance {nome_b} ou Empate: {ec['P_B_ou_E']:.2%}")

# Mercado de gols
st.header("⚽ Mercado de Gols")
odd_over25 = st.number_input("Odd Over 2.5 (mercado)", min_value=1.01, value=1.90, step=0.01)
n_jogos_mercado = st.number_input("Jogos na temporada (para peso dinâmico)", min_value=1, value=n_jogos_a, step=1)

# Preparar dicionários para FG (simplificado: usar os mesmos valores de FG calculados)
fg_dict_a = {'ataque': fg_a, 'defesa': fg_a, 'meio': fg_a}  # idealmente separados, mas FG já é agregado
fg_dict_b = {'ataque': fg_b, 'defesa': fg_b, 'meio': fg_b}
psic_dict_a = {'moral': moral_a, 'pressao_obj': p_obj_a, 'sensibilidade': sens_a}
psic_dict_b = {'moral': moral_b, 'pressao_obj': p_obj_b, 'sensibilidade': sens_b}

gols = calcular_mercado_gols(
    gols_marcados_a=gm_a, gols_sofridos_a=gs_a,
    gols_marcados_b=gm_b, gols_sofridos_b=gs_b,
    n_jogos=n_jogos_mercado,
    ma_a=ma_a, ma_b=ma_b,
    fg_a=fg_dict_a, fg_b=fg_dict_b,
    cpp_a=cpp_a, cpp_b=cpp_b,
    estilo_a=vetor_estilo_a, estilo_b=vetor_estilo_b,
    psic_a=psic_dict_a, psic_b=psic_dict_b,
    ec_a=ec['EC_A'], ec_b=ec['EC_B'],
    prateleira_a=prat_a_num, prateleira_b=prat_b_num,
    odd_over25=odd_over25
)

st.write(f"λ modelo: {gols['lambda_modelo']:.3f} | λ mercado: {gols['lambda_mercado']:.3f} | λ final: {gols['lambda_final']:.3f}")
col_g1, col_g2, col_g3, col_g4 = st.columns(4)
col_g1.metric("Over 1.5", f"{gols['over_1.5']:.2%}")
col_g2.metric("Over 2.5", f"{gols['over_2.5']:.2%}")
col_g3.metric("Over 3.5", f"{gols['over_3.5']:.2%}")
col_g4.metric("BTTS Yes", f"{gols['btts_yes']:.2%}")

st.success("Análise concluída!")
