"""
Estilo Perfil (v1)

Classifica o perfil tático de um time com base em indicadores normalizados
(0-100). Os indicadores são os mesmos usados na FG, permitindo
aproveitar os dados já coletados.

Perfis disponíveis:
- Dominante
- Pressão Alta
- Reativo / Contra-ataque
- Defensivo
- Equilibrado
- Posse Estéril
- Efetivo
"""

from typing import Dict, Optional

# ----------------------------------------------------------
# Limiares (configuráveis)
# ----------------------------------------------------------
ALTO = 60
BAIXO = 40

# Mapeamento dos indicadores usados na classificação
INDICADORES_PERFIL = ['Posse', 'FA', 'ECa', 'FC', 'CA', 'Des']

# ----------------------------------------------------------
# Funções de normalização (mesmas da FG)
# ----------------------------------------------------------
def normalizar_indicador(valor_time: float, media_liga: float,
                         menor_melhor: bool = False) -> float:
    """Normaliza um indicador em relação à média da liga (0-100)."""
    if media_liga == 0:
        return 50.0
    pct = (valor_time - media_liga) / media_liga
    if menor_melhor:
        pct = -pct
    pct = max(-1.0, min(1.0, pct))
    return max(0.0, min(100.0, 50.0 + pct * 50.0))


def normalizar_indicadores(dados_time: Dict[str, float],
                           medias_liga: Dict[str, float],
                           indicadores: list,
                           invertidos: set = None) -> Dict[str, float]:
    """
    Normaliza uma lista de indicadores.
    Retorna dicionário {código: nota 0-100}.
    """
    if invertidos is None:
        invertidos = set()
    resultado = {}
    for cod in indicadores:
        if cod in dados_time and cod in medias_liga:
            menor = cod in invertidos
            resultado[cod] = normalizar_indicador(dados_time[cod], medias_liga[cod], menor)
        else:
            resultado[cod] = 50.0  # fallback neutro
    return resultado


# ----------------------------------------------------------
# Função de classificação
# ----------------------------------------------------------
def classificar_perfil(indicadores_norm: Dict[str, float]) -> str:
    """
    Classifica o time com base nos indicadores normalizados (0-100).

    Parâmetros:
        indicadores_norm: dicionário com pelo menos:
            'Posse', 'FA', 'ECa', 'FC', 'CA', 'Des'
            (valores entre 0 e 100; se ausente, assume 50)

    Retorna:
        string com o nome do perfil.
    """
    posse = indicadores_norm.get('Posse', 50.0)
    fa = indicadores_norm.get('FA', 50.0)
    eca = indicadores_norm.get('ECa', 50.0)
    fc = indicadores_norm.get('FC', 50.0)
    ca = indicadores_norm.get('CA', 50.0)
    des = indicadores_norm.get('Des', 50.0)

    alta_posse = posse > ALTO
    baixa_posse = posse < BAIXO
    alto_vol_ofensivo = (fa > ALTO) and (eca > ALTO)
    baixo_vol_ofensivo = (fa < BAIXO) and (eca < BAIXO)
    alta_agressividade = (fc > ALTO) and (ca > ALTO)
    alto_desarme = des > ALTO

    # Decisão hierárquica
    if alta_posse and alto_vol_ofensivo:
        if alta_agressividade:
            return "Pressão Alta"
        return "Dominante"

    if alta_posse and baixo_vol_ofensivo:
        return "Posse Estéril"

    if baixa_posse:
        if fa > ALTO:  # pouco volume mas finaliza bem no alvo
            return "Efetivo"
        if alto_desarme:
            if alta_agressividade:
                return "Defensivo"
            return "Reativo / Contra-ataque"

    # Médio
    if (BAIXO <= posse <= ALTO) and (BAIXO <= fa <= ALTO):
        return "Equilibrado"

    # Fallback: análise dos destaques
    if alta_agressividade and alto_desarme:
        return "Defensivo"
    if alto_vol_ofensivo:
        return "Dominante" if alta_posse else "Efetivo"

    return "Equilibrado"


# ----------------------------------------------------------
# Função de conveniência (dados brutos → perfil)
# ----------------------------------------------------------
def obter_perfil_time(dados_time: Dict[str, float],
                      medias_liga: Dict[str, float]) -> str:
    """
    Recebe médias por jogo do time e da liga e retorna o perfil tático.

    Exemplo:
        dados_time = {'Posse': 55.0, 'FA': 5.2, 'ECa': 6.1, 'FC': 14.0, 'CA': 2.5, 'Des': 18.0}
        medias_liga = {'Posse': 50.0, 'FA': 4.1, 'ECa': 5.0, 'FC': 12.0, 'CA': 2.0, 'Des': 15.0}
        perfil = obter_perfil_time(dados_time, medias_liga)
    """
    # Nenhum desses indicadores é invertido (todos "maior melhor" para o perfil)
    indicadores_norm = normalizar_indicadores(dados_time, medias_liga, INDICADORES_PERFIL)
    return classificar_perfil(indicadores_norm)
