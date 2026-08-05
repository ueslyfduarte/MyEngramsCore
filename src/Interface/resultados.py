"""
Resultados — EngramScore
Exibição dos resultados: EngramScore, abas, gráficos, heatmap, cenários, micro métricas, candlestick.
"""

import streamlit as st
import pandas as pd
import math
import plotly.graph_objects as go
import plotly.express as px

from src.metricas.ma import calcular_ma_simples
from src.metricas.fg import calcular_fg
from src.metricas.cpp import calcular_cpp
from src.metricas.estilo import calcular_estilo
from src.metricas.psicologico import (
    calcular_psicologico,
    calcular_pressao_tabela,
)
from src.metricas.estilo_perfil import obter_perfil_time


def normalizar_dados(dados):
    """Garante que todas as chaves esperadas existam, independente da fonte."""
    ml = dados.get("medias_liga", {})
    mapeamento = {
        'Poss': 'Posse', 'Tkl': 'Des', 'Fls': 'FC', 'CrdY': 'CA',
        'Shots': 'FA', 'SoT': 'FA',
    }
    for chave_alternativa, chave_padrao in mapeamento.items():
        if chave_alternativa in ml and chave_padrao not in ml:
            ml[chave_padrao] = ml[chave_alternativa]
    defaults = {
        'GM': 1.4, 'FA': 4.0, 'ECa': 5.0, 'Posse': 50.0,
        'GS': 1.4, 'FAS': 4.0, 'ECc': 5.0, 'Des': 15.0,
        'FC': 12.0, 'CA': 2.0,
    }
    for key, default in defaults.items():
        if key not in ml or ml[key] == 0:
            ml[key] = default
    dados["medias_liga"] = ml
    return dados


def desenhar_campo_duplo(fA, fB, nome_casa, nome_fora):
    """Campo de futebol realista com faixas de força."""
    fig = go.Figure()
    fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100,
                  fillcolor="#1B4D1B", line=dict(color="white", width=2))
    fig.add_shape(type="line", x0=50, y0=0, x1=50, y1=100, line=dict(color="white", width=2))
    fig.add_shape(type="circle", x0=35, y0=35, x1=65, y1=65, line=dict(color="white", width=2))
    fig.add_shape(type="rect", x0=0, y0=20, x1=20, y1=80, line=dict(color="white", width=1.5))
    fig.add_shape(type="rect", x0=80, y0=20, x1=100, y1=80, line=dict(color="white", width=1.5))
    fig.add_shape(type="rect", x0=0, y0=35, x1=10, y1=65, line=dict(color="white", width=1))
    fig.add_shape(type="rect", x0=90, y0=35, x1=100, y1=65, line=dict(color="white", width=1))
    zonas = ['Defesa', 'Meio', 'Ataque']
    for i, (zona, fa) in enumerate(zip(zonas, fA)):
        x0 = i * 33.33; x1 = (i+1) * 33.33
        fig.add_shape(type="rect", x0=x0, y0=50, x1=x1, y1=100,
                      fillcolor=f"rgba(240,192,64,{fa*0.5})", line_width=0)
        fig.add_annotation(x=(x0+x1)/2, y=75, text=f"{zona}<br>{fa*100:.0f}%",
                           showarrow=False, font=dict(color="white", size=11))
    fig.add_annotation(x=15, y=110, text=f"🏠 {nome_casa}", showarrow=False,
                       font=dict(color="#F0C040", size=14))
    zonas_B = ['Ataque', 'Meio', 'Defesa']
    for i, (zona, fb) in enumerate(zip(zonas_B, fB)):
        x0 = i * 33.33; x1 = (i+1) * 33.33
        fig.add_shape(type="rect", x0=x0, y0=0, x1=x1, y1=50,
                      fillcolor=f"rgba(74,144,217,{fb*0.5})", line_width=0)
        fig.add_annotation(x=(x0+x1)/2, y=25, text=f"{zona}<br>{fb*100:.0f}%",
                           showarrow=False, font=dict(color="white", size=11))
    fig.add_annotation(x=85, y=110, text=f"✈️ {nome_fora}", showarrow=False,
                       font=dict(color="#4a90d9", size=14))
    fig.update_xaxes(visible=False, range=[0,100])
    fig.update_yaxes(visible=False, range=[-10,120])
    fig.update_layout(template='plotly_dark', paper_bgcolor='#0A0E17',
                      height=500, margin=dict(l=20, r=20, t=40, b=20))
    return fig


def gerar_cenarios_justificados(results_adj, nome_casa, nome_fora, gm_casa, gm_fora,
                                 gs_casa, gs_fora, EC_A, EC_B, lambda_casa_adj, lambda_fora_adj):
    """Retorna os 5 cenários mais prováveis com justificativas."""
    empate_adj = sum(p for gA, gB, p in results_adj if gA == gB)
    vitoria_fora_adj = sum(p for gA, gB, p in results_adj if gA < gB)
    over15_adj = sum(p for gA, gB, p in results_adj if gA+gB > 1.5)
    over25_adj = sum(p for gA, gB, p in results_adj if gA+gB > 2.5)
    over35_adj = sum(p for gA, gB, p in results_adj if gA+gB > 3.5)
    btts_adj = sum(p for gA, gB, p in results_adj if gA > 0 and gB > 0)
    eventos = [
        ('Vitória do ' + nome_casa + ' por 2+ gols',
         sum(p for gA, gB, p in results_adj if gA >= gB+2),
         f"Ataque do {nome_casa} ({gm_casa:.1f} gols/j) contra defesa do {nome_fora} ({gs_fora:.1f} sofridos/j)."),
        ('Empate', empate_adj, f"Equilíbrio nos EngramScores ({EC_A:.1f} vs {EC_B:.1f})."),
        ('Vitória do ' + nome_fora, vitoria_fora_adj, f"{nome_fora} com {gm_fora:.1f} gols/j contra defesa de {gs_casa:.1f}."),
        ('Over 1.5 Gols', over15_adj, f"λ total ajustado: {lambda_casa_adj+lambda_fora_adj:.2f}."),
        ('Over 2.5 Gols', over25_adj, f"λ total ajustado: {lambda_casa_adj+lambda_fora_adj:.2f}."),
        ('Over 3.5 Gols', over35_adj, f"Possibilidade de placar elástico."),
        ('Ambos Marcam (BTTS)', btts_adj, f"{nome_casa} ({gm_casa:.1f}/{gs_casa:.1f}) x {nome_fora} ({gm_fora:.1f}/{gs_fora:.1f})."),
    ]
    eventos.sort(key=lambda x: x[1], reverse=True)
    return eventos[:5]


def selo(prob):
    if prob >= 0.75: return '<span class="selo-dourado">🏅 OURO</span>'
    elif prob >= 0.60: return '<span class="selo-verde">✅ CONFIÁVEL</span>'
    elif prob >= 0.50: return '<span class="selo-amarelo">⚠️ MODERADO</span>'
    else: return ''


def valor_com_destaque(valor, prob):
    if prob >= 0.75: return f'<span class="high-confidence" style="font-size:42px;">{valor:.1%}</span>'
    else: return f'<span style="font-size:42px; font-weight:900; color:#E0E0E0;">{valor:.1%}</span>'


def prob_team_over(lam, k):
    return 1 - sum(math.exp(-lam)*(lam**i)/math.factorial(i) for i in range(k+1))


def renderizar_resultados(dados, odds):
    """Processa os dados e renderiza todos os resultados."""
    dados = normalizar_dados(dados)
    # Extrair dados
    nome_casa = dados["nome_casa"]; nome_fora = dados["nome_fora"]
    n_casa = dados["n_casa"]; n_fora = dados["n_fora"]
    gm_casa = dados["gm_casa"]; gm_fora = dados["gm_fora"]
    fa_casa = dados["fa_casa"]; fa_fora = dados["fa_fora"]
    eca_casa = dados["eca_casa"]; eca_fora = dados["eca_fora"]
    posse_casa = dados["posse_casa"]; posse_fora = dados["posse_fora"]
    gs_casa = dados["gs_casa"]; gs_fora = dados["gs_fora"]
    fas_casa = dados["fas_casa"]; fas_fora = dados["fas_fora"]
    des_casa = dados["des_casa"]; des_fora = dados["des_fora"]
    fc_casa = dados["fc_casa"]; fc_fora = dados["fc_fora"]
    ca_casa = dados["ca_casa"]; ca_fora = dados["ca_fora"]
    res_casa = dados["res_casa"]; res_fora = dados["res_fora"]
    cons_casa = dados["cons_casa"]; cons_fora = dados["cons_fora"]
    moral_casa = dados["moral_casa"]; moral_fora = dados["moral_fora"]
    pos_casa = dados["pos_casa"]; pos_fora = dados["pos_fora"]
    pts_cpp_casa = dados["pts_cpp_casa"]; pts_cpp_fora = dados["pts_cpp_fora"]
    jogos_cpp_casa = dados["jogos_cpp_casa"]; jogos_cpp_fora = dados["jogos_cpp_fora"]
    dados_A = dados["dados_A"]; dados_B = dados["dados_B"]
    medias_liga = dados["medias_liga"]
    odd_casa = odds["odd_casa"]; odd_empate = odds["odd_empate"]; odd_fora = odds["odd_fora"]
    odd_over15 = odds["odd_over15"]; odd_over25 = odds["odd_over25"]; odd_over35 = odds["odd_over35"]
    odd_btts_sim = odds["odd_btts_sim"]; odd_btts_nao = odds["odd_btts_nao"]; odd_ht = odds["odd_ht"]

    aprov_casa_casa = dados.get("aprov_casa_casa", 50.0)
    aprov_fora_fora = dados.get("aprov_fora_fora", 50.0)

    def parse_seq(s): return [3 if c == 'V' else 1 if c == 'E' else 0 for c in s if c in 'VED']
    seq_casa = parse_seq(res_casa); seq_fora = parse_seq(res_fora)
    seq_cons_casa = parse_seq(cons_casa); seq_cons_fora = parse_seq(cons_fora)
    inv_sum = 1/odd_casa + 1/odd_empate + 1/odd_fora
    prob_v_casa = (1/odd_casa) / inv_sum; prob_emp = (1/odd_empate) / inv_sum; prob_v_fora = (1/odd_fora) / inv_sum

    def ma_recente(seq, pv, pe, n_total):
        if not seq: return 50.0
        recente = seq[-6:]
        return calcular_ma_simples(sum(recente), len(recente), n_total, pv, pe)
    ma_A = ma_recente(seq_casa, prob_v_casa, prob_emp, n_casa)
    ma_B = ma_recente(seq_fora, prob_v_fora, prob_emp, n_fora)
    fg_A = calcular_fg(dados_A, medias_liga, n_casa)
    fg_B = calcular_fg(dados_B, medias_liga, n_fora)
    cpp_A = calcular_cpp(pts_cpp_casa, jogos_cpp_casa, prob_v_casa, prob_emp)
    cpp_B = calcular_cpp(pts_cpp_fora, jogos_cpp_fora, prob_v_fora, prob_emp)
    estilo_A = calcular_estilo(dados_A, medias_liga, n_casa)
    estilo_B = calcular_estilo(dados_B, medias_liga, n_fora)
    perfil_A = obter_perfil_time(dados_A, medias_liga)
    perfil_B = obter_perfil_time(dados_B, medias_liga)
    dif_pts = (pos_casa - pos_fora) * 3
    p_obj_A = calcular_pressao_tabela(pos_casa, 24, pos_fora, dif_pts)
    p_obj_B = calcular_pressao_tabela(pos_fora, 24, pos_casa, -dif_pts)
    psic_A = calcular_psicologico(consistencia_pontos=seq_cons_casa if len(seq_cons_casa)>=5 else None, moral_pontos=moral_casa, pressao_p_obj=p_obj_A, pressao_sensibilidade=0.3)
    psic_B = calcular_psicologico(consistencia_pontos=seq_cons_fora if len(seq_cons_fora)>=5 else None, moral_pontos=moral_fora, pressao_p_obj=p_obj_B, pressao_sensibilidade=0.3)

    bonus_casa = max(0, (aprov_casa_casa - aprov_fora_fora) / 10)
    bonus_fora = max(0, (aprov_fora_fora - aprov_casa_casa) / 10)
    if aprov_fora_fora > 60:
        bonus_casa *= 0.5

    EC_A = (ma_A*0.25 + fg_A*0.25 + cpp_A*0.25 + psic_A*0.25) + bonus_casa
    EC_B = (ma_B*0.25 + fg_B*0.25 + cpp_B*0.25 + psic_B*0.25) + bonus_fora
    EC_A = max(0, min(100, EC_A)); EC_B = max(0, min(100, EC_B))
    diff_ec = abs(EC_A - EC_B)

    if diff_ec < 5.0:
        p_emp = 0.30 + (1 - diff_ec / 5.0) * 0.04
    elif diff_ec < 20:
        p_emp = 0.27 - (diff_ec - 5) / 15 * 0.07
    else:
        p_emp = max(0.14, 0.20 - (diff_ec - 20) / 80 * 0.06)

    total = EC_A + EC_B
    p_A = (1 - p_emp) * (EC_A / total) if total > 0 else 0.33
    p_B = 1 - p_A - p_emp
    lambda_casa_orig = (gm_casa + gs_fora) / 2
    lambda_fora_orig = (gm_fora + gs_casa) / 2
    fator_ajuste = (EC_A - EC_B) / 100.0
    lambda_casa_adj = max(0, lambda_casa_orig * (1 + fator_ajuste * 0.5))
    lambda_fora_adj = max(0, lambda_fora_orig * (1 - fator_ajuste * 0.5))
    results_adj = []
    for i in range(6):
        for j in range(6):
            prob = math.exp(-lambda_casa_adj)*(lambda_casa_adj**i)/math.factorial(i) * math.exp(-lambda_fora_adj)*(lambda_fora_adj**j)/math.factorial(j)
            results_adj.append((i, j, prob))
    vitoria_casa_adj = sum(p for gA,gB,p in results_adj if gA>gB)
    empate_adj = sum(p for gA,gB,p in results_adj if gA==gB)
    vitoria_fora_adj = sum(p for gA,gB,p in results_adj if gA<gB)
    over15_adj = sum(p for gA,gB,p in results_adj if gA+gB > 1.5)
    over25_adj = sum(p for gA,gB,p in results_adj if gA+gB > 2.5)
    over35_adj = sum(p for gA,gB,p in results_adj if gA+gB > 3.5)
    btts_adj = sum(p for gA,gB,p in results_adj if gA>0 and gB>0)
    under15_adj = 1 - over15_adj; under25_adj = 1 - over25_adj; under35_adj = 1 - over35_adj
    FATOR_HT = 0.44; ajuste_estilo = 0
    if perfil_A in ["Pressão Alta", "Dominante"]: ajuste_estilo += 0.05
    if perfil_B in ["Pressão Alta", "Dominante"]: ajuste_estilo -= 0.05
    lambda_ht_adj = (lambda_casa_adj + lambda_fora_adj) * (FATOR_HT + ajuste_estilo)
    prob_gol_ht_adj = 1 - math.exp(-lambda_ht_adj)
    casa_over05 = prob_team_over(lambda_casa_adj, 0); casa_over15 = prob_team_over(lambda_casa_adj, 1); casa_over25 = prob_team_over(lambda_casa_adj, 2)
    fora_over05 = prob_team_over(lambda_fora_adj, 0); fora_over15 = prob_team_over(lambda_fora_adj, 1); fora_over25 = prob_team_over(lambda_fora_adj, 2)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("""<div style="text-align:center; margin-bottom:30px;"><div style="font-size:13px; text-transform:uppercase; letter-spacing:4px; color:#B0B8C0;">Resultado da Análise</div><h2 style="font-weight:900; margin:8px 0; letter-spacing:-1px;"><span style="background:linear-gradient(180deg, #F0C040 0%, #D4A017 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">ENGRAMSCORE</span></h2></div>""", unsafe_allow_html=True)
    col_ec1, col_ec2 = st.columns(2)
    with col_ec1:
        st.markdown(f"""<div class="card-premium" style="text-align:center;"><div style="font-size:14px; text-transform:uppercase; letter-spacing:3px; color:#B0B8C0; margin-bottom:10px;">🏠 {nome_casa}</div><div class="metric-premium">{EC_A:.1f}</div><div class="metric-label-premium">EngramScore</div><div class="bar-premium"><div class="bar-fill-gold" style="width:{EC_A}%;"></div></div><div style="font-size:12px; color:#B0B8C0; margin-top:4px;">MA · FG · CPP · PSICOLÓGICO</div></div>""", unsafe_allow_html=True)
    with col_ec2:
        st.markdown(f"""<div class="card-premium" style="text-align:center;"><div style="font-size:14px; text-transform:uppercase; letter-spacing:3px; color:#B0B8C0; margin-bottom:10px;">✈️ {nome_fora}</div><div class="metric-premium-blue">{EC_B:.1f}</div><div class="metric-label-premium">EngramScore</div><div class="bar-premium"><div class="bar-fill-blue" style="width:{EC_B}%;"></div></div><div style="font-size:12px; color:#B0B8C0; margin-top:4px;">MA · FG · CPP · PSICOLÓGICO</div></div>""", unsafe_allow_html=True)
    if EC_A > EC_B: st.markdown(f"""<div style="text-align:center; margin:16px 0; font-size:16px; font-weight:700; color:#F0C040;">🔺 {nome_casa} leva vantagem de +{EC_A - EC_B:.1f} pontos</div>""", unsafe_allow_html=True)
    elif EC_B > EC_A: st.markdown(f"""<div style="text-align:center; margin:16px 0; font-size:16px; font-weight:700; color:#4A90D9;">🔻 {nome_fora} leva vantagem de +{EC_B - EC_A:.1f} pontos</div>""", unsafe_allow_html=True)
    else: st.markdown(f"""<div style="text-align:center; margin:16px 0; font-size:16px; font-weight:700; color:#F0C040;">⚖️ Equilíbrio absoluto</div>""", unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("""<div style="text-align:center; margin-bottom:20px;"><span style="font-size:13px; text-transform:uppercase; letter-spacing:3px; color:#B0B8C0;">Análises Detalhadas</span></div>""", unsafe_allow_html=True)
    tabs = st.tabs(["📊 PILARES","🎭 ESTILO","⚔️ CONFRONTO","🗺️ HEATMAP","🎲 CENÁRIOS","🔧 AJUSTE EC","📋 MERCADOS","🌟 DESTAQUES","📝 ANÁLISE","🧠 MICRO MÉTRICAS","🕯️ CANDLESTICK"])
    # ----- ABA 1: Pilares -----
    with tabs[0]:
        st.markdown('<div class="card-premium"><div class="card-header-premium">🔍 PILARES INDIVIDUAIS</div>', unsafe_allow_html=True)
        pilares_nomes = ['Momento Atual','Força Geral','Confronto','Psicológico']
        valores_A = [ma_A,fg_A,cpp_A,psic_A]
        valores_B = [ma_B,fg_B,cpp_B,psic_B]
        df = pd.DataFrame({'Pilar':pilares_nomes*2,'Time':[nome_casa]*4+[nome_fora]*4,'Força':valores_A+valores_B})
        fig = px.bar(df,x='Pilar',y='Força',color='Time',barmode='group',text_auto='.1f',
                     color_discrete_map={nome_casa:'#F0C040',nome_fora:'#4a90d9'},title="Comparativo de Pilares")
        fig.update_traces(textposition='outside',textfont=dict(size=14,color='white'))
        fig.update_layout(template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',transition_duration=800,hovermode='x unified')
        st.plotly_chart(fig,width='stretch')
        col_info1,col_info2=st.columns(2)
        with col_info1:
            st.markdown(f"""<div class="info-card"><strong>🏠 {nome_casa}</strong><br><strong>MA:</strong> {ma_A:.1f} (momentum recente)<br><strong>FG:</strong> {fg_A:.1f} (ataque/defesa/meio)<br><strong>CPP:</strong> {cpp_A:.1f} (confronto por prateleira)<br><strong>Psic:</strong> {psic_A:.1f} (consistência/moral/pressão)</div>""",unsafe_allow_html=True)
        with col_info2:
            st.markdown(f"""<div class="info-card"><strong>✈️ {nome_fora}</strong><br><strong>MA:</strong> {ma_B:.1f}<br><strong>FG:</strong> {fg_B:.1f}<br><strong>CPP:</strong> {cpp_B:.1f}<br><strong>Psic:</strong> {psic_B:.1f}</div>""",unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)

        st.markdown('<div class="card-premium"><div class="card-header-premium">🎯 FORÇA SETORIAL</div>',unsafe_allow_html=True)
        def norm_rad(val,media): return 50 if media==0 else max(0,min(100,50+(val-media)/media*50))
        atq_A=(norm_rad(gm_casa,medias_liga['GM'])+norm_rad(fa_casa,medias_liga['FA']))/2
        def_A=(100-norm_rad(gs_casa,medias_liga['GS'])+100-norm_rad(fas_casa,medias_liga['FAS']))/2
        mei_A=norm_rad(posse_casa,medias_liga['Posse'])
        atq_B=(norm_rad(gm_fora,medias_liga['GM'])+norm_rad(fa_fora,medias_liga['FA']))/2
        def_B=(100-norm_rad(gs_fora,medias_liga['GS'])+100-norm_rad(fas_fora,medias_liga['FAS']))/2
        mei_B=norm_rad(posse_fora,medias_liga['Posse'])
        fig_radar=go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=[atq_A,def_A,mei_A],theta=['Ataque','Defesa','Meio'],fill='toself',name=nome_casa,marker_color='#F0C040',hovertemplate='%{r:.1f}<br>%{theta}'))
        fig_radar.add_trace(go.Scatterpolar(r=[atq_B,def_B,mei_B],theta=['Ataque','Defesa','Meio'],fill='toself',name=nome_fora,marker_color='#4a90d9',hovertemplate='%{r:.1f}<br>%{theta}'))
        fig_radar.update_layout(polar=dict(radialaxis=dict(range=[0,100],tickfont=dict(color='white')),angularaxis=dict(tickfont=dict(color='white'))),template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',transition_duration=800,title=f"Comparação Setorial: {nome_casa} vs {nome_fora}")
        st.plotly_chart(fig_radar,width='stretch')
        st.markdown('</div>',unsafe_allow_html=True)

    # ----- ABA 2: Estilo -----
    with tabs[1]:
        st.markdown('<div class="card-premium"><div class="card-header-premium">🎭 PERFIS TÁTICOS</div>',unsafe_allow_html=True)
        col_perf1,col_perf2=st.columns(2)
        with col_perf1:
            cor_perfil='#F0C040' if 'Dominante' in perfil_A or 'Pressão' in perfil_A else '#4A90D9' if 'Reativo' in perfil_A else '#B0B8C0'
            st.markdown(f"""<div style="background:rgba(240,192,64,0.05);border:1px solid {cor_perfil};border-radius:12px;padding:20px;text-align:center;"><div style="font-size:18px;font-weight:700;color:#F0C040;margin-bottom:8px;">🏠 {nome_casa}</div><div style="font-size:28px;font-weight:900;color:{cor_perfil};">{perfil_A}</div><div style="font-size:13px;color:#B0B8C0;margin-top:8px;">Dominância: {estilo_A:.1f}/100</div></div>""",unsafe_allow_html=True)
        with col_perf2:
            cor_perfil='#F0C040' if 'Dominante' in perfil_B or 'Pressão' in perfil_B else '#4A90D9' if 'Reativo' in perfil_B else '#B0B8C0'
            st.markdown(f"""<div style="background:rgba(74,144,217,0.05);border:1px solid {cor_perfil};border-radius:12px;padding:20px;text-align:center;"><div style="font-size:18px;font-weight:700;color:#4A90D9;margin-bottom:8px;">✈️ {nome_fora}</div><div style="font-size:28px;font-weight:900;color:{cor_perfil};">{perfil_B}</div><div style="font-size:13px;color:#B0B8C0;margin-top:8px;">Dominância: {estilo_B:.1f}/100</div></div>""",unsafe_allow_html=True)
        st.markdown("**📊 Indicadores de Estilo de Jogo**")
        indicadores_estilo=['Posse','Chutes','Cruzamentos','Bolas Enfiadas','Passes Curtos','Presença Ofensiva']
        vals_estilo_A=[posse_casa,fa_casa,dados.get('crs_casa',eca_casa),dados.get('thrball_casa',0.5),dados.get('shortpass_casa',300),dados.get('attthird_casa',30)]
        vals_estilo_B=[posse_fora,fa_fora,dados.get('crs_fora',eca_fora),dados.get('thrball_fora',0.5),dados.get('shortpass_fora',300),dados.get('attthird_fora',30)]
        max_vals=[max(a,b) for a,b in zip(vals_estilo_A,vals_estilo_B)]
        vals_A_norm=[(a/m*50) if m>0 else 50 for a,m in zip(vals_estilo_A,max_vals)]
        vals_B_norm=[(b/m*50) if m>0 else 50 for b,m in zip(vals_estilo_B,max_vals)]
        df_estilo=pd.DataFrame({'Indicador':indicadores_estilo*2,'Time':[nome_casa]*6+[nome_fora]*6,'Valor':vals_A_norm+vals_B_norm})
        fig_estilo=px.bar(df_estilo,x='Indicador',y='Valor',color='Time',barmode='group',color_discrete_map={nome_casa:'#F0C040',nome_fora:'#4a90d9'},title="Comparativo de Estilo de Jogo")
        fig_estilo.update_traces(textposition='outside')
        fig_estilo.update_layout(template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',transition_duration=800)
        st.plotly_chart(fig_estilo,width='stretch')
        st.markdown("""<div class="info-card" style="margin-top:16px;"><strong>🏆 Dominante:</strong> Controla posse, finaliza muito, pressiona.<br><strong>🔥 Pressão Alta:</strong> Extremamente agressivo.<br><strong>⚡ Reativo/Contra‑ataque:</strong> Pouca posse, transições rápidas.<br><strong>🛡️ Defensivo:</strong> Prioriza não sofrer gols.<br><strong>⚖️ Equilibrado:</strong> Sem extremos.<br><strong>🅿️ Jogo Pelas Pontas:</strong> Muitos cruzamentos.<br><strong>⬆️ Jogo Vertical:</strong> Bolas enfiadas, profundidade.</div>""",unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)

    # ----- ABA 3: Confronto -----
    with tabs[2]:
        st.markdown('<div class="card-premium"><div class="card-header-premium">⚔️ CONFRONTO POR ESTATÍSTICA</div>',unsafe_allow_html=True)
        stats_completas=[('Gols Marcados',gm_casa,gm_fora,'maior','⚽'),('Finalizações Alvo',fa_casa,fa_fora,'maior','🎯'),('Posse (%)',posse_casa,posse_fora,'maior','🏐'),('Gols Sofridos',gs_casa,gs_fora,'menor','🥅'),('Finalizações Sofridas',fas_casa,fas_fora,'menor','🛡️'),('Faltas Cometidas',fc_casa,fc_fora,'menor','🟨'),('Cartões Amarelos',ca_casa,ca_fora,'menor','🟨'),('Desarmes',des_casa,des_fora,'maior','💪'),('Escanteios',eca_casa,eca_fora,'maior','🏳️')]
        for nome,vA,vB,tipo,icone in stats_completas:
            if tipo=='maior':
                vant=nome_casa if vA>vB else nome_fora if vB>vA else "Empate"
                cor_A='#00E676' if vA>vB else '#E0E0E0'; cor_B='#00E676' if vB>vA else '#E0E0E0'
            else:
                vant=nome_casa if vA<vB else nome_fora if vB<vA else "Empate"
                cor_A='#00E676' if vA<vB else '#E0E0E0'; cor_B='#00E676' if vB<vA else '#E0E0E0'
            st.markdown(f"""<div style="display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.03);font-size:14px;color:#E0E0E0;"><span>{icone} {nome}</span><span style="color:{cor_A};font-weight:600;">{nome_casa}: {vA:.1f}</span><span style="color:{cor_B};font-weight:600;">{nome_fora}: {vB:.1f}</span><span style="font-weight:700;color:#F0C040;">➡️ {vant}</span></div>""",unsafe_allow_html=True)
        vant_A=sum(1 for _,vA,vB,tipo,_ in stats_completas if (tipo=='maior' and vA>vB) or (tipo=='menor' and vA<vB))
        vant_B=sum(1 for _,vA,vB,tipo,_ in stats_completas if (tipo=='maior' and vB>vA) or (tipo=='menor' and vB<vA))
        st.markdown(f"""<div class="info-card" style="margin-top:16px;text-align:center;"><strong>{nome_casa}</strong> vence em <strong>{vant_A}/9</strong> estatísticas | <strong>{nome_fora}</strong> vence em <strong>{vant_B}/9</strong> estatísticas</div>""",unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)

    # ----- ABA 4: Heatmap -----
    with tabs[3]:
        st.markdown('<div class="card-premium"><div class="card-header-premium">🗺️ HEATMAP TÁTICO — FLUXO DE JOGO</div>',unsafe_allow_html=True)
        fA=[def_A/100,mei_A/100,atq_A/100]; fB=[atq_B/100,mei_B/100,def_B/100]
        fA=[max(0.05,min(0.95,f)) for f in fA]; fB=[max(0.05,min(0.95,f)) for f in fB]
        frames=[]
        for t in range(10):
            variacao=math.sin(t*0.5)*0.08
            fA_anim=[max(0.05,min(0.95,f+variacao)) for f in fA]
            fB_anim=[max(0.05,min(0.95,f-variacao)) for f in fB]
            shapes_list=[]
            zonas=['Defesa','Meio','Ataque']
            for i,(zona,fa,fb) in enumerate(zip(zonas,fA_anim,fB_anim)):
                shapes_list.append({'type':'rect','x0':i*33.33,'y0':50,'x1':(i+1)*33.33,'y1':100,'fillcolor':f"rgba(240,192,64,{fa})",'line':{'width':0}})
                shapes_list.append({'type':'rect','x0':i*33.33,'y0':0,'x1':(i+1)*33.33,'y1':50,'fillcolor':f"rgba(74,144,217,{fb})",'line':{'width':0}})
            frames.append(go.Frame(data=[],layout=go.Layout(shapes=shapes_list),name=f'f{t}'))
        fig_field=go.Figure()
        fig_field.add_shape(type="rect",x0=0,y0=0,x1=100,y1=100,fillcolor="#1B4D1B",line=dict(color="white",width=2))
        fig_field.add_shape(type="line",x0=50,y0=0,x1=50,y1=100,line=dict(color="white",width=2))
        fig_field.add_shape(type="circle",x0=35,y0=35,x1=65,y1=65,line=dict(color="white",width=2))
        fig_field.add_shape(type="rect",x0=0,y0=20,x1=20,y1=80,line=dict(color="white",width=1.5))
        fig_field.add_shape(type="rect",x0=80,y0=20,x1=100,y1=80,line=dict(color="white",width=1.5))
        fig_field.add_shape(type="rect",x0=0,y0=35,x1=10,y1=65,line=dict(color="white",width=1))
        fig_field.add_shape(type="rect",x0=90,y0=35,x1=100,y1=65,line=dict(color="white",width=1))
        zonas=['Defesa','Meio','Ataque']
        for i,(zona,fa) in enumerate(zip(zonas,fA)):
            x0=i*33.33; x1=(i+1)*33.33
            fig_field.add_shape(type="rect",x0=x0,y0=50,x1=x1,y1=100,fillcolor=f"rgba(240,192,64,{fa})",line_width=0)
        zonas_B=['Ataque','Meio','Defesa']
        for i,(zona,fb) in enumerate(zip(zonas_B,fB)):
            x0=i*33.33; x1=(i+1)*33.33
            fig_field.add_shape(type="rect",x0=x0,y0=0,x1=x1,y1=50,fillcolor=f"rgba(74,144,217,{fb})",line_width=0)
        for i,(zona,fa,fb) in enumerate(zip(['Defesa','Meio','Ataque'],fA,fB)):
            fig_field.add_annotation(x=i*33.33+16,y=75,text=f"{zona}<br>{fa*100:.0f}%",showarrow=False,font=dict(color="white",size=11))
            fig_field.add_annotation(x=i*33.33+16,y=25,text=f"{zona}<br>{fb*100:.0f}%",showarrow=False,font=dict(color="white",size=11))
        fig_field.add_annotation(x=15,y=110,text=f"🏠 {nome_casa}",showarrow=False,font=dict(color="#F0C040",size=14))
        fig_field.add_annotation(x=85,y=110,text=f"✈️ {nome_fora}",showarrow=False,font=dict(color="#4a90d9",size=14))
        fig_field.frames=frames
        fig_field.update_layout(template='plotly_dark',paper_bgcolor='#0A0E17',height=500,margin=dict(l=20,r=20,t=40,b=20),updatemenus=[dict(type='buttons',showactive=False,x=0.5,y=1.05,xanchor='center',buttons=[dict(label='▶️ Iniciar',method='animate',args=[None,dict(frame=dict(duration=500,redraw=True),fromcurrent=True,mode='immediate')]),dict(label='⏸️ Pausar',method='animate',args=[[None],dict(frame=dict(duration=0,redraw=False),mode='immediate')])])])
        fig_field.update_xaxes(visible=False,range=[0,100]); fig_field.update_yaxes(visible=False,range=[-10,120])
        st.plotly_chart(fig_field,width='stretch')
        st.markdown("""<div style="font-size:13px;color:#B0B8C0;text-align:center;">🔸 Dourado = Casa | 🔵 Azul = Visitante<br>Clique em ▶️ para ver o fluxo de jogo animado</div>""",unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
        # ----- ABA 5: Cenários -----
    with tabs[4]:
        st.markdown('<div class="card-premium"><div class="card-header-premium">🎲 CINCO CENÁRIOS MAIS PROVÁVEIS</div>',unsafe_allow_html=True)
        cenarios=gerar_cenarios_justificados(results_adj,nome_casa,nome_fora,gm_casa,gm_fora,gs_casa,gs_fora,EC_A,EC_B,lambda_casa_adj,lambda_fora_adj)
        for i,(tit,prob,just) in enumerate(cenarios):
            cor_barra='#F0C040' if prob>0.50 else '#4A90D9' if prob>0.30 else '#B0B8C0'
            st.markdown(f"""<div style="background:rgba(255,255,255,0.02);border-radius:10px;padding:14px 16px;margin:8px 0;border-left:4px solid {cor_barra};transition:all 0.3s ease;"><div style="display:flex;justify-content:space-between;align-items:center;"><span style="font-weight:700;color:#E0E0E0;font-size:15px;">{i+1}. {tit}</span><span style="font-size:22px;font-weight:900;color:{cor_barra};">{prob:.1%}</span></div><div style="font-size:12px;color:#B0B8C0;margin-top:6px;">{just}</div><div style="background:rgba(255,255,255,0.03);border-radius:4px;height:4px;margin-top:8px;"><div style="width:{prob*100}%;height:4px;background:{cor_barra};border-radius:4px;transition:width 1s ease;"></div></div></div>""",unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("**📊 Resumo de Probabilidades**")
        col_res1,col_res2,col_res3=st.columns(3)
        col_res1.metric(f"Vitória {nome_casa}",f"{p_A:.1%}",delta=f"EC: {EC_A:.1f}")
        col_res2.metric("Empate",f"{p_emp:.1%}")
        col_res3.metric(f"Vitória {nome_fora}",f"{p_B:.1%}",delta=f"EC: {EC_B:.1f}")
        st.markdown('</div>',unsafe_allow_html=True)

    # ----- ABA 6: Ajuste EC -----
    with tabs[5]:
        st.markdown('<div class="card-premium"><div class="card-header-premium">🔧 AJUSTE ENGRAMSCORE NOS GOLS ESPERADOS</div>',unsafe_allow_html=True)
        st.markdown(f"""<div style="text-align:center;margin:16px 0;"><span style="font-size:14px;color:#B0B8C0;">Fator de Ajuste (diferença dos ECs):</span><span style="font-size:28px;font-weight:900;color:#F0C040;margin-left:8px;">{fator_ajuste:+.2f}</span></div>""",unsafe_allow_html=True)
        col_orig,col_adj=st.columns(2)
        with col_orig:
            st.markdown(f"""<div style="background:rgba(255,255,255,0.02);border-radius:10px;padding:18px;text-align:center;"><div style="font-size:13px;color:#B0B8C0;text-transform:uppercase;">📊 Lambdas Originais</div><div style="font-size:32px;font-weight:900;color:#B0B8C0;">🏠 {lambda_casa_orig:.2f}</div><div style="font-size:32px;font-weight:900;color:#B0B8C0;">✈️ {lambda_fora_orig:.2f}</div><div style="font-size:11px;color:#5A6070;margin-top:4px;">Média simples: (GM + GS adv) / 2</div></div>""",unsafe_allow_html=True)
        with col_adj:
            st.markdown(f"""<div style="background:rgba(240,192,64,0.03);border:1px solid rgba(240,192,64,0.2);border-radius:10px;padding:18px;text-align:center;"><div style="font-size:13px;color:#F0C040;text-transform:uppercase;">✨ Lambdas Ajustados</div><div style="font-size:32px;font-weight:900;color:#F0C040;">🏠 {lambda_casa_adj:.2f}</div><div style="font-size:32px;font-weight:900;color:#F0C040;">✈️ {lambda_fora_adj:.2f}</div><div style="font-size:11px;color:#5A6070;margin-top:4px;">Ajustado pelo EngramScore (fator ×0.5)</div></div>""",unsafe_allow_html=True)
        impacto_casa=((lambda_casa_adj/lambda_casa_orig-1)*100) if lambda_casa_orig>0 else 0
        impacto_fora=((lambda_fora_adj/lambda_fora_orig-1)*100) if lambda_fora_orig>0 else 0
        st.markdown(f"""<div class="info-card" style="margin-top:16px;"><strong>📈 Impacto do Ajuste:</strong><br>🏠 {nome_casa}: expectativa de gols <strong>{'aumentou' if impacto_casa>0 else 'diminuiu'} {abs(impacto_casa):.1f}%</strong><br>✈️ {nome_fora}: expectativa de gols <strong>{'aumentou' if impacto_fora>0 else 'diminuiu'} {abs(impacto_fora):.1f}%</strong><br><br><small>Time com EC maior tem seu ataque favorecido e defesa reforçada.</small></div>""",unsafe_allow_html=True)
        df_lambdas=pd.DataFrame({'Métrica':['λ Casa Original','λ Casa Ajustado','λ Fora Original','λ Fora Ajustado'],'Valor':[lambda_casa_orig,lambda_casa_adj,lambda_fora_orig,lambda_fora_adj],'Tipo':['Original','Ajustado','Original','Ajustado'],'Time':[nome_casa,nome_casa,nome_fora,nome_fora]})
        fig_lambdas=px.bar(df_lambdas,x='Métrica',y='Valor',color='Tipo',barmode='group',color_discrete_map={'Original':'#B0B8C0','Ajustado':'#F0C040'},title="Comparação dos Lambdas")
        fig_lambdas.update_layout(template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_lambdas,width='stretch')
        st.markdown('</div>',unsafe_allow_html=True)

    # ----- ABA 7: Mercados -----
    with tabs[6]:
        st.markdown('<div class="card-premium"><div class="card-header-premium">📊 PROBABILIDADES 1X2</div>',unsafe_allow_html=True)
        col_p1,col_p2,col_p3=st.columns(3)
        with col_p1:
            borda='#00E676' if p_A>=p_emp and p_A>=p_B else '#252B38'
            st.markdown(f"""<div class="prob-box" style="border:2px solid {borda};"><div style="color:#00E676;font-size:14px;text-transform:uppercase;letter-spacing:1px;">Vitória {nome_casa}</div>{valor_com_destaque(p_A,p_A)}<div style="margin-top:8px;">{selo(p_A)}</div><div style="font-size:11px;color:#B0B8C0;margin-top:4px;">EC: {EC_A:.1f}</div></div>""",unsafe_allow_html=True)
        with col_p2:
            borda='#F0C040' if p_emp>=p_A and p_emp>=p_B else '#252B38'
            st.markdown(f"""<div class="prob-box" style="border:2px solid {borda};"><div style="color:#F0C040;font-size:14px;text-transform:uppercase;letter-spacing:1px;">Empate</div>{valor_com_destaque(p_emp,p_emp)}<div style="margin-top:8px;">{selo(p_emp)}</div><div style="font-size:11px;color:#B0B8C0;margin-top:4px;">Dif. EC: {diff_ec:.1f}</div></div>""",unsafe_allow_html=True)
        with col_p3:
            borda='#4A90D9' if p_B>=p_A and p_B>=p_emp else '#252B38'
            st.markdown(f"""<div class="prob-box" style="border:2px solid {borda};"><div style="color:#4A90D9;font-size:14px;text-transform:uppercase;letter-spacing:1px;">Vitória {nome_fora}</div>{valor_com_destaque(p_B,p_B)}<div style="margin-top:8px;">{selo(p_B)}</div><div style="font-size:11px;color:#B0B8C0;margin-top:4px;">EC: {EC_B:.1f}</div></div>""",unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)

        st.markdown('<div class="card-premium"><div class="card-header-premium">⚽ PROBABILIDADES DE GOLS (TOTAIS)</div>',unsafe_allow_html=True)
        df_gols=pd.DataFrame({'Mercado':['Over 0.5','Over 1.5','Over 2.5','Over 3.5','BTTS Sim','Gol 1ºT'],'Probabilidade':[1.0,over15_adj,over25_adj,over35_adj,btts_adj,prob_gol_ht_adj]})
        fig_gols=px.bar(df_gols,x='Mercado',y='Probabilidade',text_auto='.1%',color='Probabilidade',color_continuous_scale=['#4A90D9','#F0C040'],title="Probabilidades de Gols")
        fig_gols.update_traces(textposition='outside',textfont=dict(color='white',size=13))
        fig_gols.update_layout(template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',coloraxis_showscale=False,showlegend=False)
        st.plotly_chart(fig_gols,width='stretch')
        col_g1,col_g2,col_g3=st.columns(3)
        col_g1.metric("Over 1.5",f"{over15_adj:.1%}"); col_g2.metric("Over 2.5",f"{over25_adj:.1%}"); col_g3.metric("Over 3.5",f"{over35_adj:.1%}")
        col_g4,col_g5,col_g6=st.columns(3)
        col_g4.metric("Under 1.5",f"{under15_adj:.1%}"); col_g5.metric("Under 2.5",f"{under25_adj:.1%}"); col_g6.metric("Under 3.5",f"{under35_adj:.1%}")
        col_b1,col_b2,col_b3=st.columns(3)
        col_b1.metric("BTTS Sim",f"{btts_adj:.1%}"); col_b2.metric("BTTS Não",f"{1-btts_adj:.1%}"); col_b3.metric("Gol 1º Tempo",f"{prob_gol_ht_adj:.1%}")
        st.markdown(f"""<div class="info-card"><strong>λ ajustado:</strong> Casa {lambda_casa_adj:.2f}, Fora {lambda_fora_adj:.2f} | Total: {lambda_casa_adj+lambda_fora_adj:.2f}</div>""",unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)

        st.markdown('<div class="card-premium"><div class="card-header-premium">🎯 PROBABILIDADES INDIVIDUAIS DE GOLS</div>',unsafe_allow_html=True)
        col_i1,col_i2=st.columns(2)
        with col_i1:
            st.markdown(f"**🏠 {nome_casa}**")
            st.metric("Over 0.5",f"{casa_over05:.1%}"); st.metric("Over 1.5",f"{casa_over15:.1%}"); st.metric("Over 2.5",f"{casa_over25:.1%}")
            st.markdown(f"<small>λ: {lambda_casa_adj:.2f}</small>",unsafe_allow_html=True)
        with col_i2:
            st.markdown(f"**✈️ {nome_fora}**")
            st.metric("Over 0.5",f"{fora_over05:.1%}"); st.metric("Over 1.5",f"{fora_over15:.1%}"); st.metric("Over 2.5",f"{fora_over25:.1%}")
            st.markdown(f"<small>λ: {lambda_fora_adj:.2f}</small>",unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)

        st.markdown('<div class="card-premium"><div class="card-header-premium">📈 COMPARAÇÃO MODELO vs MERCADO (EDGE)</div>',unsafe_allow_html=True)
        probs_modelo={f"Vitória {nome_casa}":p_A,"Empate":p_emp,f"Vitória {nome_fora}":p_B,"Over 1.5":over15_adj,"Over 2.5":over25_adj,"Over 3.5":over35_adj,"BTTS Sim":btts_adj,"BTTS Não":1-btts_adj,"Gol 1º Tempo":prob_gol_ht_adj}
        odds_reais={f"Vitória {nome_casa}":odd_casa,"Empate":odd_empate,f"Vitória {nome_fora}":odd_fora,"Over 1.5":odd_over15,"Over 2.5":odd_over25,"Over 3.5":odd_over35,"BTTS Sim":odd_btts_sim,"BTTS Não":odd_btts_nao,"Gol 1º Tempo":odd_ht}
        linhas=[]
        for mercado,prob in probs_modelo.items():
            odd_mod=1/prob if prob>0 else 999; odd_real=odds_reais.get(mercado)
            if odd_real and odd_real>1.0:
                ev=(prob*odd_real-1)*100; indicacao="💚 VALOR" if ev>5 else "🟢 Bom" if ev>0 else "🔴 Sem"
                linhas.append((mercado,f"{prob:.1%}",f"{odd_mod:.2f}",f"{odd_real:.2f}",f"{ev:+.1f}%",indicacao))
            else: linhas.append((mercado,f"{prob:.1%}",f"{odd_mod:.2f}","-","-","⚪"))
        df_edge=pd.DataFrame(linhas,columns=["Mercado","Prob. Modelo","Odd Justa","Odd Real","EV%","Edge"])
        st.dataframe(df_edge,width='stretch',height=400)
        st.markdown("""<small>💚 VALOR = EV% > 5% | 🟢 Bom = EV% positivo | 🔴 Sem = sem valor identificado</small>""",unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
        # ----- ABA 8: Destaques -----
    with tabs[7]:
        st.markdown('<div class="card-premium"><div class="card-header-premium">🌟 DESTAQUES E DIFERENCIAIS</div>',unsafe_allow_html=True)
        st.markdown("**📊 Probabilidades Acima de 65%**")
        destaques=[]
        if p_A>0.65: destaques.append((f"Vitória {nome_casa}",p_A,"1X2"))
        if p_emp>0.65: destaques.append(("Empate",p_emp,"1X2"))
        if p_B>0.65: destaques.append((f"Vitória {nome_fora}",p_B,"1X2"))
        for nome,prob in [("Over 1.5",over15_adj),("Over 2.5",over25_adj),("Over 3.5",over35_adj),("BTTS Sim",btts_adj),("Gol 1º Tempo",prob_gol_ht_adj)]:
            if prob>0.65: destaques.append((nome,prob,"Gols"))
        if destaques:
            for nome,prob,cat in destaques:
                icone="🏆" if cat=="1X2" else "⚽"
                st.markdown(f"""<div style="background:rgba(240,192,64,0.08);border:1px solid rgba(240,192,64,0.3);border-radius:10px;padding:14px;margin:6px 0;display:flex;justify-content:space-between;align-items:center;"><span style="color:#F0C040;font-weight:700;">{icone} {nome}</span><span style="font-size:24px;font-weight:900;background:linear-gradient(180deg,#F0C040 0%,#D4A017 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{prob:.1%}</span></div>""",unsafe_allow_html=True)
        else: st.markdown('<div style="color:#B0B8C0;text-align:center;">Nenhuma probabilidade acima de 65%.</div>',unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("**🎯 Diferenciais Táticos**")
        dif_posse=posse_casa-posse_fora; dif_chutes=fa_casa-fa_fora; dif_desarme=des_casa-des_fora
        if abs(dif_posse)>5:
            time_dom=nome_casa if dif_posse>0 else nome_fora
            st.markdown(f"🟡 **Posse de bola**: {time_dom} deve dominar a posse ({abs(dif_posse):.1f}% a mais)")
        if abs(dif_chutes)>2:
            time_chutes=nome_casa if dif_chutes>0 else nome_fora
            st.markdown(f"🎯 **Finalizações**: {time_chutes} finaliza mais ({abs(dif_chutes):.1f} por jogo)")
        if abs(dif_desarme)>3:
            time_des=nome_casa if dif_desarme>0 else nome_fora
            st.markdown(f"💪 **Desarmes**: {time_des} desarma mais ({abs(dif_desarme):.1f} por jogo)")
        if dados.get('rating_casa',0)>0:
            dif_rating=dados.get('rating_casa',6.5)-dados.get('rating_fora',6.5)
            if abs(dif_rating)>0.2:
                time_rating=nome_casa if dif_rating>0 else nome_fora
                st.markdown(f"⭐ **Rating WhoScored**: {time_rating} melhor avaliado (dif: {abs(dif_rating):.2f})")
        if dados.get('glsca_casa',0)>0 or dados.get('glsca_fora',0)>0:
            st.markdown(f"⚡ **Contra-ataque**: {nome_casa} {dados.get('glsca_casa',0):.0f} gols | {nome_fora} {dados.get('glsca_fora',0):.0f} gols")
        st.markdown('</div>',unsafe_allow_html=True)

    # ----- ABA 9: Análise Descritiva -----
    with tabs[8]:
        st.markdown('<div class="card-premium"><div class="card-header-premium">📝 ANÁLISE DESCRITIVA COMPLETA</div>',unsafe_allow_html=True)
        st.markdown("### 🔍 Pilares Individuais")
        st.markdown(f"""<div class="info-card"><strong>Momento Atual:</strong> {nome_casa} {ma_A:.1f} × {nome_fora} {ma_B:.1f}. {'Casa em melhor fase.' if ma_A>ma_B else 'Visitante em melhor momento.' if ma_B>ma_A else 'Momentos semelhantes.'}<br><strong>Força Geral:</strong> {nome_casa} {fg_A:.1f} × {nome_fora} {fg_B:.1f}. {'Casa mais forte.' if fg_A>fg_B else 'Visitante mais forte.' if fg_B>fg_A else 'Força equilibrada.'}<br><strong>Confronto:</strong> {nome_casa} {cpp_A:.1f} × {nome_fora} {cpp_B:.1f}.<br><strong>Psicológico:</strong> {nome_casa} {psic_A:.1f} × {nome_fora} {psic_B:.1f}.</div>""",unsafe_allow_html=True)
        st.markdown("### ⚔️ Diferenciais por Pilar")
        dif_ma=ma_A-ma_B; dif_fg=fg_A-fg_B; dif_cpp=cpp_A-cpp_B; dif_psic=psic_A-psic_B
        vantagens_A=[]; vantagens_B=[]
        if dif_ma>0: vantagens_A.append("Momento Atual")
        elif dif_ma<0: vantagens_B.append("Momento Atual")
        if dif_fg>0: vantagens_A.append("Força Geral")
        elif dif_fg<0: vantagens_B.append("Força Geral")
        if dif_cpp>0: vantagens_A.append("Confronto")
        elif dif_cpp<0: vantagens_B.append("Confronto")
        if dif_psic>0: vantagens_A.append("Psicológico")
        elif dif_psic<0: vantagens_B.append("Psicológico")
        if vantagens_A: st.markdown(f"<div class='info-card'><strong>{nome_casa}</strong> leva vantagem em: {', '.join(vantagens_A)}.</div>",unsafe_allow_html=True)
        if vantagens_B: st.markdown(f"<div class='info-card'><strong>{nome_fora}</strong> leva vantagem em: {', '.join(vantagens_B)}.</div>",unsafe_allow_html=True)
        if not vantagens_A and not vantagens_B: st.markdown("<div class='info-card'>Equilíbrio total nos pilares.</div>",unsafe_allow_html=True)
        st.markdown("### ⚡ EngramScore")
        st.markdown(f"""<div class="info-card">{nome_casa} <strong>{EC_A:.1f}</strong> vs {nome_fora} <strong>{EC_B:.1f}</strong>. {'Vantagem clara para o mandante.' if EC_A>EC_B+5 else 'Visitante é o favorito.' if EC_B>EC_A+5 else 'Confronto extremamente equilibrado.'}</div>""",unsafe_allow_html=True)
        st.markdown("### 🎯 Desempenho Setorial")
        st.markdown(f"""<div class="info-card"><strong>Ataque:</strong> {nome_casa} {atq_A:.1f} × {nome_fora} {atq_B:.1f}.<br><strong>Defesa:</strong> {nome_casa} {def_A:.1f} × {nome_fora} {def_B:.1f}.<br><strong>Meio:</strong> {nome_casa} {mei_A:.1f} × {nome_fora} {mei_B:.1f}.</div>""",unsafe_allow_html=True)
        st.markdown(f"""<div class="info-card">{nome_casa} é <strong>{perfil_A}</strong>, {nome_fora} é <strong>{perfil_B}</strong>.</div>""",unsafe_allow_html=True)
        if dados.get('rating_casa',0)>0:
            st.markdown("### ⭐ Rating WhoScored")
            st.markdown(f"""<div class="info-card">{nome_casa}: <strong>{dados.get('rating_casa',6.5):.2f}</strong> | {nome_fora}: <strong>{dados.get('rating_fora',6.5):.2f}</strong></div>""",unsafe_allow_html=True)
        st.markdown("### 📊 Expectativa de Gols")
        st.markdown(f"""<div class="info-card">Total esperado: <strong>{lambda_casa_adj+lambda_fora_adj:.2f}</strong> gols.<br>Over 1.5: <strong>{over15_adj:.1%}</strong> | Over 2.5: <strong>{over25_adj:.1%}</strong> | Over 3.5: <strong>{over35_adj:.1%}</strong><br>BTTS: <strong>{btts_adj:.1%}</strong> | Gol 1ºT: <strong>{prob_gol_ht_adj:.1%}</strong></div>""",unsafe_allow_html=True)
        cen=gerar_cenarios_justificados(results_adj,nome_casa,nome_fora,gm_casa,gm_fora,gs_casa,gs_fora,EC_A,EC_B,lambda_casa_adj,lambda_fora_adj)
        st.markdown(f"""<div class="info-card"><strong>Cenário mais provável:</strong> {cen[0][0]} ({cen[0][1]:.1%})</div>""",unsafe_allow_html=True)
        st.markdown("### 📌 Recomendação Final")
        resultados_list=[(f"Vitória do {nome_casa}",p_A,vantagens_A,"mandante"),("Empate",p_emp,[],"empate"),(f"Vitória do {nome_fora}",p_B,vantagens_B,"visitante")]
        resultado_final=max(resultados_list,key=lambda x:x[1])
        nome_res,prob_res,vantagens_res,tipo_res=resultado_final
        if tipo_res=="empate":
            justificativa="O equilíbrio nos pilares indica uma partida disputada."
            if diff_ec<5: justificativa+=" A diferença de EngramScore é mínima."
            cor_borda="#F0C040"
        else:
            if vantagens_res: justificativa=f"Vantagens nos pilares {', '.join(vantagens_res)} dão a superioridade."
            elif tipo_res=="mandante": justificativa="Fator casa e ligeira superioridade no EngramScore inclinam a balança."
            else: justificativa="Visitante apresenta EngramScore superior, justificando o favoritismo."
            cor_borda="#00E676" if tipo_res=="mandante" else "#4A90D9"
        st.markdown(f"""<div class="info-card" style="border-color:{cor_borda};"><strong>{nome_res}</strong> é o resultado mais provável, com <strong>{prob_res:.1%}</strong> de chance.<br>{justificativa}</div>""",unsafe_allow_html=True)
        if tipo_res!="empate" and p_emp>0.25: st.markdown(f"""<div class="info-card" style="border-color:#F0C040;margin-top:8px;">⚠️ O empate também merece atenção, com <strong>{p_emp:.1%}</strong> de probabilidade.</div>""",unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)

    # ----- ABA 10: Micro Métricas -----
    with tabs[9]:
        st.markdown('<div class="card-premium"><div class="card-header-premium">🧠 MICRO MÉTRICAS — DETALHAMENTO DOS PILARES</div>', unsafe_allow_html=True)
        col_m1, col_m2 = st.columns(2)

        with col_m1:
            st.markdown(f"**🏠 {nome_casa}**")
            st.markdown(f"**Momento Atual (MA):** {ma_A:.1f}")
            st.markdown(f"**Força Geral (FG):** {fg_A:.1f}")
            st.markdown(f"  - Ataque: GM={dados_A.get('GM',0):.2f}, xG={dados_A.get('xG',0):.2f}, SoT={dados_A.get('SoT',0):.2f}")
            st.markdown(f"  - Defesa: GS={dados_A.get('GS',0):.2f}, xGA={dados_A.get('xGA',0):.2f}, Tkl={dados_A.get('Tkl',0):.2f}")
            st.markdown(f"  - Meio: Poss={dados_A.get('Poss',0):.1f}%, PrgP={dados_A.get('PrgP',0):.1f}")
            st.markdown(f"  - Intensidade: Press={dados_A.get('Press',0):.1f}, Tkl+Int={dados_A.get('Tkl',0)+dados_A.get('Int',0):.1f}")
            st.markdown(f"**Confronto por Prateleira (CPP):** {cpp_A:.1f}")
            st.markdown(f"  - Prateleira adversário: {dados.get('prat_casa','N/A')}")
            st.markdown(f"  - Pontos: {dados.get('pts_cpp_casa',0)} pts em {dados.get('jogos_cpp_casa',0)} jogos")
            st.markdown(f"**Psicológico:** {psic_A:.1f}")
            st.markdown(f"  - Consistência: {psic_A:.1f}")
            st.markdown(f"  - Moral: {moral_casa} pts (últ. 3)")
            st.markdown(f"  - Pressão: {p_obj_A:.1f}")

        with col_m2:
            st.markdown(f"**✈️ {nome_fora}**")
            st.markdown(f"**Momento Atual (MA):** {ma_B:.1f}")
            st.markdown(f"**Força Geral (FG):** {fg_B:.1f}")
            st.markdown(f"  - Ataque: GM={dados_B.get('GM',0):.2f}, xG={dados_B.get('xG',0):.2f}, SoT={dados_B.get('SoT',0):.2f}")
            st.markdown(f"  - Defesa: GS={dados_B.get('GS',0):.2f}, xGA={dados_B.get('xGA',0):.2f}, Tkl={dados_B.get('Tkl',0):.2f}")
            st.markdown(f"  - Meio: Poss={dados_B.get('Poss',0):.1f}%, PrgP={dados_B.get('PrgP',0):.1f}")
            st.markdown(f"  - Intensidade: Press={dados_B.get('Press',0):.1f}, Tkl+Int={dados_B.get('Tkl',0)+dados_B.get('Int',0):.1f}")
            st.markdown(f"**Confronto por Prateleira (CPP):** {cpp_B:.1f}")
            st.markdown(f"  - Prateleira adversário: {dados.get('prat_fora','N/A')}")
            st.markdown(f"  - Pontos: {dados.get('pts_cpp_fora',0)} pts em {dados.get('jogos_cpp_fora',0)} jogos")
            st.markdown(f"**Psicológico:** {psic_B:.1f}")
            st.markdown(f"  - Consistência: {psic_B:.1f}")
            st.markdown(f"  - Moral: {moral_fora} pts (últ. 3)")
            st.markdown(f"  - Pressão: {p_obj_B:.1f}")

        st.markdown("---")
        st.markdown("**🏟️ Fator Local**")
        st.markdown(f"""
        - Aproveitamento {nome_casa} em casa: {aprov_casa_casa:.1f}%
        - Aproveitamento {nome_fora} fora: {aprov_fora_fora:.1f}%
        - Bônus casa aplicado: {bonus_casa:.1f}
        - Bônus visitante aplicado: {bonus_fora:.1f}
        """)
        st.markdown('</div>',unsafe_allow_html=True)
        # ----- ABA 11: Candlestick -----
    with tabs[10]:
        st.markdown('<div class="card-premium"><div class="card-header-premium">🕯️ ANÁLISE POR PERÍODO (CANDLESTICK)</div>', unsafe_allow_html=True)
        st.markdown("*Cole a URL de uma partida no FBref para visualizar estatísticas por intervalo de tempo.*")
        match_url = st.text_input("URL da partida no FBref", key="candle_url")
        
        if match_url:
            if st.button("🔍 Extrair dados do jogo"):
                with st.spinner("Extraindo dados do FBref..."):
                    try:
                        from src.data_loader import get_match_period_stats_fbref
                        df_period = get_match_period_stats_fbref(match_url)
                        
                        if df_period is None or df_period.empty:
                            st.error("Não foi possível encontrar estatísticas por período. Verifique a URL e se o jogo já possui dados disponíveis.")
                        else:
                            metricas = df_period.iloc[:, 0].tolist()
                            metrica = st.selectbox("Selecione a métrica", metricas)
                            
                            row = df_period[df_period.iloc[:, 0] == metrica].iloc[0]
                            intervalos = [col for col in df_period.columns if '-' in col or '+' in col]
                            valores = []
                            for interv in intervalos:
                                try:
                                    val = float(row[interv])
                                except:
                                    val = 0.0
                                valores.append(val)
                            
                            fig = go.Figure()
                            for i, interv in enumerate(intervalos):
                                if i == 0:
                                    open_val = 0
                                else:
                                    open_val = valores[i-1]
                                close_val = valores[i]
                                high_val = max(open_val, close_val)
                                low_val = min(open_val, close_val)
                                fig.add_trace(go.Candlestick(
                                    x=[interv],
                                    open=[open_val],
                                    high=[high_val],
                                    low=[low_val],
                                    close=[close_val],
                                    name=interv
                                ))
                            fig.update_layout(
                                title=f"{metrica} por intervalo de tempo",
                                xaxis_title="Intervalo",
                                yaxis_title=metrica,
                                template='plotly_dark',
                                showlegend=False
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Erro ao processar dados: {e}")
        else:
            st.info("Exemplo de URL: `https://fbref.com/en/matches/abc123/2023-2024/TeamA-TeamB`")
        st.markdown('</div>',unsafe_allow_html=True)
