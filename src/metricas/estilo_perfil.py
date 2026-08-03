"""
Estilo Perfil v3 (Classificação Tática Expandida)

Classifica o perfil tático de um time com base em indicadores normalizados
(0-100). Usa métricas do FBref para maior precisão.

Perfis disponíveis:
- Dominante
- Pressão Alta
- Reativo / Contra-ataque
- Defensivo
- Equilibrado
- Posse Estéril
- Efetivo
- Transição Rápida (novo)
- Bloco Baixo (novo)
"""

from typing import Dict, Optional
from src.utils import normalizar_indicador

# ----------------------------------------------------------
# Limiares (configuráveis)
# ----------------------------------------------------------
ALTO = 60
BAIXO = 40

# Indicadores expandidos (códigos FBref)
INDICADORES_PERFIL = [
    'Poss',      # Posse de bola (%)
    'SoT',       # Chutes no alvo por 90min
    'CK',        # Escanteios a favor
    'Fls',       # Faltas cometidas
    'CrdY',      # Cartões amarelos
    'Tkl',       # Desarmes
    'Press',     # Pressões tentadas (🆕)
    'Int',       # Interceptações (🆕)
    'PrgP',      # Passes progressivos (🆕)
    'Crs',       # Cruzamentos (🆕)
    'Off',       # Impedimentos (🆕)
]


def normalizar_indicadores(dados_time: Dict[str, float],
                           medias_liga: Dict[str, float],
                           indicadores: list,
                           invertidos: set = None) -> Dict[str, float]:
    """Normaliza uma lista de indicadores em relação à média da liga."""
    if invertidos is None:
        invertidos = set()
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

    Parâmetros:
        indicadores_norm: dicionário com:
            'Poss', 'SoT', 'CK', 'Fls', 'CrdY', 'Tkl', 'Press', 'Int', 'PrgP', 'Crs', 'Off'

    Retorna:
        string com o nome do perfil.
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

    # Decisão hierárquica refinada

    # 1. Pressão Alta: posse alta + volume ofensivo + agressividade + pressão
    if alta_posse and alto_vol_ofensivo and alta_agressividade and alta_pressao:
        return "Pressão Alta"

    # 2. Dominante: posse alta + volume ofensivo + passes progressivos
    if alta_posse and alto_vol_ofensivo and alto_prgp:
        return "Dominante"

    # 3. Posse Estéril: posse alta + pouco volume ofensivo
    if alta_posse and baixo_vol_ofensivo:
        return "Posse Estéril"

    # 4. Transição Rápida: posse baixa + passes progressivos altos + finalizações altas
    if baixa_posse and alto_prgp and fa > ALTO:
        return "Transição Rápida"

    # 5. Efetivo: posse baixa + finaliza altas + impedimentos (joga no limite)
    if baixa_posse and fa > ALTO and alto_off:
        return "Efetivo"

    # 6. Bloco Baixo: posse baixa + interceptações altas + desarmes altos + pouca pressão
    if baixa_posse and alto_inter and alto_desarme and press < BAIXO:
        return "Bloco Baixo"

    # 7. Defensivo: posse baixa + agressividade + desarmes + interceptações
    if baixa_posse and alta_agressividade and alto_desarme and alto_inter:
        return "Defensivo"

    # 8. Reativo / Contra-ataque: posse baixa + desarmes altos
    if baixa_posse and alto_desarme:
        return "Reativo / Contra-ataque"

    # 9. Pelas pontas (novo): cruzamentos altos
    if alto_crs and not alto_prgp:
        return "Pelas Pontas"

    # 10. Equilibrado
    if (BAIXO <= posse <= ALTO) and (BAIXO <= fa <= ALTO):
        return "Equilibrado"

    # Fallback
    if alta_agressividade and alto_desarme:
        return "Defensivo"
    if alto_vol_ofensivo:
        return "Dominante" if alta_posse else "Efetivo"

    return "Equilibrado"


def obter_perfil_time(dados_time: Dict[str, float],
                      medias_liga: Dict[str, float]) -> str:
    """
    Recebe médias por jogo do time e da liga e retorna o perfil tático.

    Exemplo:
        dados_time = {'Poss': 55.0, 'SoT': 5.2, 'CK': 6.1, 'Fls': 14.0, 
                      'CrdY': 2.5, 'Tkl': 18.0, 'Press': 45.0, 'Int': 12.0,
                      'PrgP': 38.0, 'Crs': 15.0, 'Off': 2.5}
        medias_liga = {'Poss': 50.0, 'SoT': 4.1, 'CK': 5.0, 'Fls': 12.0, 
                       'CrdY': 2.0, 'Tkl': 15.0, 'Press': 40.0, 'Int': 10.0,
                       'PrgP': 35.0, 'Crs': 18.0, 'Off': 2.0}
        perfil = obter_perfil_time(dados_time, medias_liga)
    """
    indicadores_norm = normalizar_indicadores(
        dados_time, medias_liga, INDICADORES_PERFIL
    )
    return classificar_perfil(indicadores_norm)
