"""
Estilo Perfil v4 (Classificação Tática — WhoScored)

Classifica o perfil tático de um time com base em indicadores normalizados (0-100).
Usa métricas do WhoScored para identificar:

PERFIS MANTIDOS:
- Dominante
- Pressão Alta
- Reativo / Contra-ataque
- Defensivo
- Equilibrado
- Posse Estéril
- Efetivo
- Transição Rápida
- Bloco Baixo
- Pelas Pontas

NOVOS PERFIS:
- Jogo Vertical (bolas enfiadas)
- Chutão / Jogo Direto (bolas longas + pouca posse)
"""

from typing import Dict
from src.utils import normalizar_indicador

# ----------------------------------------------------------
# Limiares
# ----------------------------------------------------------
ALTO = 60
BAIXO = 40

# Indicadores expandidos (códigos FBref + WhoScored)
INDICADORES_PERFIL = [
    'Poss',        # Posse de bola (%)
    'SoT',         # Chutes no alvo (FBref) / Shots (WhoScored)
    'CK',          # Escanteios (FBref)
    'Fls',         # Faltas cometidas
    'CrdY',        # Cartões amarelos (FBref)
    'Tkl',         # Desarmes
    'Press',       # Pressões tentadas (FBref)
    'Int',         # Interceptações (FBref)
    'PrgP',        # Passes progressivos (FBref)
    'Crs',         # Cruzamentos (FBref + WhoScored)
    'Off',         # Impedimentos (FBref)
    'ThrBall',     # Bolas enfiadas (WhoScored) 🆕
    'ShortPass',   # Passes curtos (WhoScored) 🆕
    'LongBall',    # Bolas longas (WhoScored) 🆕
    'AttThird',    # % Terço adversário (WhoScored) 🆕
    'GlsCA',       # Gols de contra-ataque (WhoScored) 🆕
    'GlsSP',       # Gols de bola parada (WhoScored) 🆕
]

# Indicadores que são "menor é melhor"
INDICADORES_INVERTIDOS = {'LongBall', 'Fls'}


def normalizar_indicadores(dados_time: Dict[str, float],
                           medias_liga: Dict[str, float],
                           indicadores: list,
                           invertidos: set = None) -> Dict[str, float]:
    """Normaliza uma lista de indicadores em relação à média da liga."""
    if invertidos is None:
        invertidos = INDICADORES_INVERTIDOS
    resultado = {}
    for cod in indicadores:
        if cod in dados_time and cod in medias_liga:
            menor = cod in invertidos
            resultado[cod] = normalizar_indicador(
                dados_time[cod], medias_liga[cod], menor_melhor=menor
            )
        else:
            resultado[cod] = 50.0
    return resultado


def classificar_perfil(indicadores_norm: Dict[str, float]) -> str:
    """
    Classifica o time com base nos indicadores normalizados (0-100).
    """
    posse = indicadores_norm.get('Poss', 50.0)
    fa = indicadores_norm.get('SoT', 50.0)
    eca = indicadores_norm.get('CK', 50.0)
    fc = indicadores_norm.get('Fls', 50.0)
    ca = indicadores_norm.get('CrdY', 50.0)
    des = indicadores_norm.get('Tkl', 50.0)
    press = indicadores_norm.get('Press', 50.0)
    inter = indicadores_norm.get('Int', 50.0)
    prgp = indicadores_norm.get('PrgP', 50.0)
    crs = indicadores_norm.get('Crs', 50.0)
    off = indicadores_norm.get('Off', 50.0)
    thrball = indicadores_norm.get('ThrBall', 50.0)
    shortpass = indicadores_norm.get('ShortPass', 50.0)
    longball = indicadores_norm.get('LongBall', 50.0)
    attthird = indicadores_norm.get('AttThird', 50.0)
    glsca = indicadores_norm.get('GlsCA', 50.0)
    glssp = indicadores_norm.get('GlsSP', 50.0)

    # Flags básicas
    alta_posse = posse > ALTO
    baixa_posse = posse < BAIXO
    alto_vol_ofensivo = (fa > ALTO) and (eca > ALTO)
    baixo_vol_ofensivo = (fa < BAIXO) and (eca < BAIXO)
    alta_agressividade = (fc > ALTO) and (ca > ALTO)
    alto_desarme = des > ALTO
    alta_pressao = press > ALTO
    alto_inter = inter > ALTO
    alto_prgp = prgp > ALTO
    alto_crs = crs > ALTO
    alto_off = off > ALTO
    alto_thrball = thrball > ALTO
    alto_shortpass = shortpass > ALTO
    baixo_longball = longball < BAIXO
    alto_attthird = attthird > ALTO
    alto_glsca = glsca > ALTO
    alto_glssp = glssp > ALTO

    # ============ DECISÃO HIERÁRQUICA ============

    # 1. Pressão Alta
    if alta_posse and alto_vol_ofensivo and alta_agressividade and alta_pressao:
        return "Pressão Alta"

    # 2. Dominante
    if alta_posse and alto_vol_ofensivo and alto_prgp and alto_attthird:
        return "Dominante"

    # 3. Jogo Vertical 🆕
    if alto_thrball and not alto_crs:
        return "Jogo Vertical"

    # 4. Pelas Pontas
    if alto_crs and not alto_thrball:
        return "Pelas Pontas"

    # 5. Posse Estéril
    if alta_posse and baixo_vol_ofensivo and alto_shortpass:
        return "Posse Estéril"

    # 6. Chutão / Jogo Direto 🆕
    if baixa_posse and baixo_longball:  # nota baixa em LongBall = muitas bolas longas
        return "Chutão / Jogo Direto"

    # 7. Bloco Baixo
    if baixa_posse and alto_inter and alto_desarme and not alto_attthird:
        return "Bloco Baixo"

    # 8. Reativo / Contra-ataque (melhorado com GlsCA)
    if baixa_posse and (alto_desarme or alto_glsca) and fa > ALTO:
        return "Reativo / Contra-ataque"

    # 9. Transição Rápida
    if baixa_posse and alto_prgp and fa > ALTO:
        return "Transição Rápida"

    # 10. Defensivo
    if baixa_posse and alta_agressividade and alto_desarme and alto_inter:
        return "Defensivo"

    # 11. Efetivo
    if baixa_posse and fa > ALTO and alto_off:
        return "Efetivo"

    # 12. Equilibrado
    if (BAIXO <= posse <= ALTO) and (BAIXO <= fa <= ALTO):
        return "Equilibrado"

    # Fallback
    if alta_agressividade and alto_desarme:
        return "Defensivo"
    if alto_vol_ofensivo:
        return "Dominante" if alta_posse else "Efetivo"
    if alto_crs:
        return "Pelas Pontas"
    if alto_thrball:
        return "Jogo Vertical"

    return "Equilibrado"


def obter_perfil_time(dados_time: Dict[str, float],
                      medias_liga: Dict[str, float]) -> str:
    """
    Recebe médias por jogo do time e da liga e retorna o perfil tático.
    """
    indicadores_norm = normalizar_indicadores(
        dados_time, medias_liga, INDICADORES_PERFIL
    )
    return classificar_perfil(indicadores_norm)
